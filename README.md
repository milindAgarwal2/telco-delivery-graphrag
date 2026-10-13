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

## Status

🚧 Scaffolding. Nothing functional yet — this README is the charter.

## License

MIT (to be added) — learning/portfolio project.
