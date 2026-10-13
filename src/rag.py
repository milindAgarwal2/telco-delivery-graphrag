"""Phase-1 RAG answerer — UI-free.

Ties retrieval + the provider abstraction into a single ``answer_question()``
that any front-end (CLI, API, notebook, or a later Streamlit shell) can call.
This is the equivalent of ChatBOT's ``answer_question`` but with the Streamlit
streaming/rendering removed.

Flow:
  1. retrieve relevant chunks (MMR)
  2. run a lightweight confidence probe (best relevance score)
  3. resolve the configured provider (auto-fallback to extractive)
  4. generate the answer (grounded + cited, or extractive passages)
  5. return a structured result dict
"""

import logging

try:
    from .config import get_llm_provider, get_low_confidence_threshold
    from .logging_config import setup_logging
    from .retrieval import retrieve_docs, confidence_probe, build_context
    from .providers import resolve_provider, generate_answer
except ImportError:  # pragma: no cover
    from config import get_llm_provider, get_low_confidence_threshold
    from logging_config import setup_logging
    from retrieval import retrieve_docs, confidence_probe, build_context
    from providers import resolve_provider, generate_answer

setup_logging()
logger = logging.getLogger("rag")


def answer_question(user_question, provider=None):
    """Answer a question against the ingested DMC corpus.

    Parameters
    ----------
    user_question : str
    provider : str, optional
        Override the configured provider ("claude" | "qwen" | "none"). If None,
        the provider from config.json is used. Either way it is resolved with
        auto-fallback so answering never hard-fails.

    Returns
    -------
    dict with keys:
        answer           : str
        provider         : str   (the EFFECTIVE provider after fallback)
        sources          : list of (file_name, section) tuples offered as context
        confidence       : float | None  (best retrieval relevance score in [0,1])
        low_confidence   : bool  (confidence below the configured threshold)
        num_docs         : int   (chunks retrieved)
    """
    requested = provider if provider is not None else get_llm_provider()
    effective = resolve_provider(requested)

    docs = retrieve_docs(user_question)
    score = confidence_probe(user_question)
    threshold = get_low_confidence_threshold()
    low_conf = score is not None and score < threshold

    answer = generate_answer(effective, user_question, docs)
    _context, sources = build_context(docs)

    logger.info(
        "answered | provider=%s(req=%s) docs=%d confidence=%s low=%s",
        effective, requested, len(docs), score, low_conf,
    )
    return {
        "answer": answer,
        "provider": effective,
        "sources": sources,
        "confidence": score,
        "low_confidence": low_conf,
        "num_docs": len(docs),
    }


def _format_result(result):
    """Pretty-print a result dict for CLI use."""
    lines = []
    if result["low_confidence"]:
        lines.append(
            f"⚠️  Low confidence (best match {result['confidence']:.3f} below "
            f"threshold) — limited matching content.\n"
        )
    lines.append(result["answer"])
    if result["sources"]:
        lines.append("\nSources offered:")
        for fname, section in result["sources"]:
            import os
            lines.append(f"  - {os.path.basename(fname or 'unknown')} §{section}")
    lines.append(
        f"\n[provider={result['provider']} docs={result['num_docs']} "
        f"confidence={result['confidence']}]"
    )
    return "\n".join(lines)


def main():
    """CLI: answer a question passed as argv, or a default demo question."""
    import sys

    question = " ".join(sys.argv[1:]).strip() or (
        "Why did the acceptance test fail after the cSAEGW-C upgrade, and what "
        "fix is recommended?"
    )
    result = answer_question(question)
    print("\n" + "=" * 70)
    print("Q:", question)
    print("=" * 70)
    print(_format_result(result))


if __name__ == "__main__":
    main()
