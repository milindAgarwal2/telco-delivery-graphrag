"""Document ingestion for the Phase-1 RAG baseline.

Ported from the parent ChatBOT project's ``embeddingEngine.py`` and trimmed to
what the baseline needs: the FastEmbed + Chroma vector store, character-based
chunking, and the content-hash UPSERT that prevents duplicate chunks on
re-ingest. The PDF/PPTX/Spire/PyMuPDF machinery is intentionally NOT ported —
the synthetic CNPD corpus is markdown/text/JSON, so this module adds a
lightweight text/markdown/JSON ingester instead.

Vector-store settings (collection, persist dir, embedding model) come from
config.json via ``get_vectorstore_config()`` so ingestion and retrieval always
agree on where/how documents are embedded.

Key behaviours preserved from ChatBOT:
  - content-addressed doc IDs (SHA-256 of file bytes) -> re-ingest is an UPSERT
  - identical bytes = no-op (skipped); changed content REPLACES old chunks
  - cosine HNSW space; CharacterTextSplitter(chunk_size=500, overlap=200)
"""

import gc
import glob
import hashlib
import logging
import os

from langchain_text_splitters import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document

try:
    from .config import get_vectorstore_config
    from .logging_config import setup_logging
except ImportError:  # pragma: no cover - loose-script fallback
    from config import get_vectorstore_config
    from logging_config import setup_logging

setup_logging()
logger = logging.getLogger("ingest")

# Supported extensions for the baseline text ingester.
TEXT_EXTS = (".md", ".markdown", ".txt", ".json")


# ---------------------------------------------------------------------------
# Vector store
# ---------------------------------------------------------------------------
def get_vectorstore():
    """Return the shared Chroma vector store, configured from config.json.

    Collection name, persist directory, and embedding model are read fresh so a
    single config edit changes both ingestion and retrieval consistently.
    """
    vs_cfg = get_vectorstore_config()
    embedding_function = FastEmbedEmbeddings(model_name=vs_cfg["embedding_model"])
    return Chroma(
        collection_name=vs_cfg["collection"],
        embedding_function=embedding_function,
        persist_directory=vs_cfg["persist_dir"],
        collection_metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def get_text_chunks(text):
    """Split text into overlapping chunks (same params as ChatBOT)."""
    text_splitter = CharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=200,
        length_function=len,
        separator="\n",
    )
    return text_splitter.split_text(text)


# ---------------------------------------------------------------------------
# Content-hash upsert (preserved from ChatBOT)
# ---------------------------------------------------------------------------
def compute_doc_hash(filepath):
    """Return a content-addressed ID for a document: SHA-256 of its raw bytes.

    Streamed in 1 MB blocks so large files don't load fully into memory.
    """
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def delete_chunks_for_file(vectorstore, filepath):
    """Delete ONLY the embedded chunks whose file_name == filepath. Returns the
    number of chunks removed (best-effort)."""
    try:
        before = vectorstore._collection.count()
        vectorstore._collection.delete(where={"file_name": filepath})
        after = vectorstore._collection.count()
        return max(0, before - after)
    except Exception:
        return 0


def _existing_doc_hash(vectorstore, filepath):
    """Return the doc_hash already stored for this file_name, or None."""
    try:
        data = vectorstore._collection.get(
            where={"file_name": filepath}, include=["metadatas"], limit=1
        )
    except Exception:
        return None
    metas = (data or {}).get("metadatas") or []
    if metas and metas[0]:
        return metas[0].get("doc_hash")
    return None


def _prepare_upsert(vectorstore, filepath):
    """Shared upsert pre-step.

    - Same hash already present -> return (doc_hash, True) meaning "skip".
    - Otherwise delete any existing chunks for this file_name and return
      (doc_hash, False) to proceed. Makes re-ingest an UPSERT, not an append.
    """
    doc_hash = compute_doc_hash(filepath)
    existing = _existing_doc_hash(vectorstore, filepath)
    if existing is not None and existing == doc_hash:
        return doc_hash, True
    delete_chunks_for_file(vectorstore, filepath)
    return doc_hash, False


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------
def store_text_embedding(text_chunks, vectorstore, file, section, doc_hash=None):
    """Embed a list of text chunks for a file, tagging source metadata.

    Metadata mirrors ChatBOT's shape where it makes sense (file_name, doc_hash)
    but uses a ``section`` label (markdown heading path or "body") in place of a
    PDF page number, since the CNPD corpus is text/markdown.
    """
    docs = []
    for text in text_chunks:
        if not text or not text.strip():
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "file_name": file,
                    "section": section,
                    "contentType": "text",
                    "doc_hash": doc_hash or "",
                },
            )
        )
    if docs:
        vectorstore.add_documents(documents=docs)
    return len(docs)


# ---------------------------------------------------------------------------
# Markdown / text / JSON ingestion (NEW — replaces PDF/PPTX for the baseline)
# ---------------------------------------------------------------------------
def _split_markdown_sections(text):
    """Split markdown into (section_label, section_text) pairs by ATX headings.

    Keeps each heading with the body beneath it and builds a breadcrumb-style
    label (e.g. "Release Notes › 2 Known Issues") so retrieved chunks carry
    their location. Non-markdown text yields a single ("body", text) pair.
    """
    lines = text.splitlines()
    sections = []
    # Track the current heading stack by level for a breadcrumb label.
    stack = []  # list of (level, title)
    buf = []
    cur_label = "body"

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections.append((cur_label, body))

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            # Count leading '#'s = heading level.
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            if 1 <= level <= 6 and title:
                flush()
                buf = []
                # Pop deeper-or-equal levels, then push this one.
                stack = [(lv, t) for (lv, t) in stack if lv < level]
                stack.append((level, title))
                cur_label = " › ".join(t for _lv, t in stack)
                continue
        buf.append(line)
    flush()
    if not sections:
        sections = [("body", text.strip())]
    return sections


def ingest_text_file(filepath, vectorstore):
    """Embed a single markdown/text/JSON file into the vector store.

    Markdown is split by heading into sections (each section chunked); plain
    text/JSON is treated as one "body" section. Re-ingest is an UPSERT keyed by
    content hash: identical bytes are a no-op; changed content replaces chunks.

    Returns a summary dict: {sections, chunks, skipped}.
    """
    gc.collect()
    summary = {"sections": 0, "chunks": 0, "skipped": False}

    doc_hash, skip = _prepare_upsert(vectorstore, filepath)
    if skip:
        summary["skipped"] = True
        return summary

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    ext = os.path.splitext(filepath)[1].lower()
    if ext in (".md", ".markdown"):
        sections = _split_markdown_sections(raw)
    else:
        # .txt / .json: embed whole content as a single section.
        sections = [("body", raw.strip())]

    for label, body in sections:
        if not body.strip():
            continue
        summary["sections"] += 1
        chunks = get_text_chunks(body)
        summary["chunks"] += store_text_embedding(
            chunks, vectorstore, filepath, label, doc_hash=doc_hash
        )
    return summary


def ingest_file(filepath, vectorstore):
    """Dispatch to the right ingester by extension. Baseline supports text
    formats only (PDF/PPTX deferred). Raises ValueError for unsupported types."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in TEXT_EXTS:
        return ingest_text_file(filepath, vectorstore)
    raise ValueError(f"Unsupported file type for baseline ingestion: {ext}")


# ---------------------------------------------------------------------------
# Introspection / maintenance
# ---------------------------------------------------------------------------
def list_embedded_documents(vectorstore):
    """Return a sorted list of distinct file_name values already embedded."""
    try:
        data = vectorstore.get(include=["metadatas"])
    except Exception:
        return []
    names = set()
    for md in data.get("metadatas", []) or []:
        if md and md.get("file_name"):
            names.add(md["file_name"])
    return sorted(names)


def delete_document(filepath, vectorstore):
    """Remove a document's embedded chunks and (optionally) its source file.

    Returns a summary dict. The source file is left in place for the synthetic
    corpus (it's tracked in git); only the chunks are removed.
    """
    summary = {"chunks_deleted": 0}
    try:
        before = vectorstore._collection.count()
        vectorstore._collection.delete(where={"file_name": filepath})
        after = vectorstore._collection.count()
        summary["chunks_deleted"] = max(0, before - after)
    except Exception as ex:
        summary["error"] = f"chunk delete failed: {ex}"
    return summary


# ---------------------------------------------------------------------------
# Batch entrypoint
# ---------------------------------------------------------------------------
def ingest_directory(directory, vectorstore=None, reset=False):
    """Ingest every supported file under ``directory`` (recursively).

    If ``reset`` is True the collection is wiped first (clean full rebuild).
    Returns a dict mapping filepath -> per-file summary.
    """
    if vectorstore is None:
        vectorstore = get_vectorstore()
    if reset:
        try:
            vectorstore.reset_collection()
        except Exception as ex:
            logger.warning("reset_collection failed: %s", ex)

    results = {}
    paths = []
    for ext in TEXT_EXTS:
        paths += glob.glob(os.path.join(directory, "**", f"*{ext}"), recursive=True)
    for filepath in sorted(set(paths)):
        try:
            summary = ingest_file(filepath, vectorstore)
            results[filepath] = summary
            logger.info(
                "ingested %s | sections=%s chunks=%s skipped=%s",
                filepath, summary.get("sections"), summary.get("chunks"),
                summary.get("skipped"),
            )
        except ValueError as ex:
            logger.warning("skipped %s: %s", filepath, ex)
            results[filepath] = {"error": str(ex)}
    return results


def main():
    """CLI: ingest data/synthetic/ into the configured vector store."""
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "synthetic",
    )
    vs = get_vectorstore()
    results = ingest_directory(data_dir, vs, reset=True)
    total_chunks = sum(r.get("chunks", 0) for r in results.values())
    logger.info("ingest complete | files=%d total_chunks=%d", len(results), total_chunks)


if __name__ == "__main__":
    main()
