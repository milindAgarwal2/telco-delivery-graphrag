# 🕸️ DMC Delivery GraphRAG Copilot

A **learning project** exploring **GraphRAG** (knowledge-graph–augmented retrieval)
over the delivery lifecycle of a cloud-native 5G/telecom program — requirements →
design → deployment → upgrade → acceptance testing → incident resolution → handover.

It answers questions a plain document-RAG struggles with — **dependency tracing and
impact analysis** — e.g.:

> *"Why did an acceptance test fail after a 5GC upgrade, and what evidence supports
> the recommended fix?"*
>
> *"Which test cases and documents are impacted by this network-function upgrade,
> and what blocks FOA readiness?"*

Built by reusing the ingestion, LLM-provider abstraction, and Streamlit UI patterns
from [`doc-intelligence-rag`](https://github.com/milindAgarwal2/doc-intelligence-rag),
with a **knowledge graph** layered on top for relationship-aware retrieval.

---

## ⚠️ Data policy (read first)

This is a **learning project** and the repo is intended to be **shareable**. Therefore:

- **Only synthetic / sanitized data is committed** — everything in `data/synthetic/`
  is invented (fake releases, fake network-function names, made-up test cases and
  defects). It resembles real DMC artifacts in *shape* but contains **no real
  customer, subscriber, node, or confidential information**.
- **Real DMC material NEVER goes in the repo.** If you experiment against real
  documents, place them under `data/private/` — which is **git-ignored**. Do not
  commit production logs, customer identifiers, credentials, PCAPs, IMSIs, node
  names, or control-plane addresses.
- Secrets (API keys) live in `.env` (git-ignored); non-secret config in a tracked
  config file — same split as the parent project.

---

## Why GraphRAG (and why not just RAG)

Plain RAG answers *retrieval* questions well ("what does this release note say?").
It struggles with *relationship* questions ("if I upgrade NF X, which test cases,
interfaces, and services are affected?"). Those are **graph-traversal** problems.

This project builds in two phases so the value of the graph is **demonstrated, not
assumed**:

- **Phase 1 — RAG baseline:** ingest the synthetic DMC documents, answer retrieval
  questions. (Reuses the parent project's ingestion + embeddings + LLM providers.)
- **Phase 2 — Graph layer:** extract entities + relationships into a graph and answer
  the dependency/impact questions RAG can't. The anchor demo is the acceptance-test
  failure flow above.

---

## Graph model (entities & relationships)

Nodes:

```
Project · Release · NetworkFunction · SoftwareVersion · Interface/Parameter
TestCase · TestResult · Defect · Alarm · Document (MOP/CIQ/NIR/ReleaseNote)
Environment (Lab/FOA/Production) · Change · Milestone · Owner
```

Example relationships:

```
Release        ──supports──>        DMCRelease
TestCase       ──validates──>       NetworkFunction / Feature
NetworkFunction──runs──>            SoftwareVersion
NetworkFunction──deployed_on──>     Environment
TestCase       ──blocked_by──>      Defect
Defect         ──fixed_in──>        Release
Release        ──requires──>        Document (MOP/CIQ)
LabResult      ──gates──>           FOA
FOA            ──precedes──>        Production
Document       ──describes──>       Configuration
```

---

## Planned architecture (reuse map)

| Piece | Source | Reuse |
|---|---|---|
| Document ingestion / chunking | `doc-intelligence-rag/embeddingEngine.py` | adapt |
| LLM provider abstraction (Claude / local / extractive) | `chatBOT_engine.py` | extract to a module |
| Config / secret split | `config.py` | reuse pattern |
| Structured logging | `logging_config.py` | reuse |
| Streamlit UI shell | `embeddingGUI.py` / `chatBOT_engine.py` | reuse shell |
| **Graph store** | **new** | **Neo4j** (property graph, Cypher) |
| **Graph extraction** | **new** | LLM-assisted entity/relation extraction |
| **Hybrid retrieval** | **new** | vector retrieval + graph traversal |

---

## MVP scope (deliberately small)

- ~10 synthetic DMC-style documents
- ~5 releases, ~1–2 dozen test cases, a handful of defects, 3 environments
- ~50–100 graph nodes, ~100–200 relationships
- **One** anchor workflow answered end-to-end: *acceptance-test failure after upgrade*
- A small eval set (~15–20 questions) comparing RAG-only vs. graph-augmented answers

---

## Running it

### One-time setup

```bash
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m src.ingest     # embed data/synthetic/ into Chroma (~55 chunks)
./.venv/bin/python -m src.extract    # build the knowledge graph (~31 nodes, ~48 edges)
```

### GUI (no Python needed to use it) — recommended

A browser-based front-end with two tabs: **Ask a question** (Q&A with a provider
selector, a *Use knowledge graph* toggle, and answer + sources + confidence) and
**Impact Explorer** (pick an entity like `TC-204` and see what it connects to
across the delivery lifecycle — the dependency/impact traversal plain search
can't do).

```bash
./.venv/bin/streamlit run app.py
```

Then open the URL it prints (default <http://localhost:8501>). The GUI is a thin
layer over the core modules — it changes nothing in `src/`.

### CLI

```bash
./.venv/bin/python -m src.rag --graph "Which test cases and documents are impacted by the cSAEGW-C upgrade, and what blocks FOA readiness?"
./.venv/bin/python -m src.rag --no-graph "Why did the acceptance test fail after the cSAEGW-C upgrade?"
./.venv/bin/python -m src.graph_retrieval TC-204    # impact report for any entity
```

By default the answerer uses the extractive provider (no API key needed). Set
`llm_provider` in `config.json` to `claude` (needs `ANTHROPIC_API_KEY` in `.env`)
or `qwen` (needs a local GGUF) for synthesized prose.

## Status

✅ **Phase 1 (RAG baseline)** and **Phase 2 (NetworkX knowledge graph +
graph-augmented retrieval)** are complete, plus a **Streamlit GUI**. The graph
uses in-process NetworkX (no server/Docker), persisted to `graph/telco_graph.json`.
Backlog: RAG-vs-graph eval harness, per-CNF release-note modeling, and real-data
ingestion (PDF/XLSX + PII scrubbing).

## License

MIT (to be added) — learning/portfolio project.
