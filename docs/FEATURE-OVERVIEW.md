# CNPD Delivery GraphRAG Copilot — Feature Overview

**Author:** Milind Agarwal
**Status:** Working prototype (learning / portfolio project)
**Audience:** Engineering leadership

> **Scope note.** This is a self-built prototype using **only synthetic,
> sanitized data**. It is not a commercial product and contains no real customer,
> subscriber, node, or confidential information. The intent here is to show a
> working capability and how the *pattern* aligns with autonomous-network goals.

---

## 1. What it is (in one line)

A question-answering and impact-analysis copilot over the **delivery lifecycle**
of a cloud-native 5G packet core — it answers not just "what does this document
say?" but "**if we upgrade this network function, what breaks, what's blocked,
and what's the evidence?**"

## 2. The problem it addresses

Delivery and operations teams work across many disconnected artifacts — release
notes (per CNF), MOPs, CIQs, test catalogs, test results, defect registers,
alarm dictionaries, runbooks, implementation records. The hard questions are
**relationship questions** that span several of those documents at once:

- Which test cases and documents are impacted by a given CNF upgrade?
- What is blocking FOA readiness, and why?
- Which release note documents a specific defect fix, and is that version in the
  certified set?

A plain document search (standard RAG) retrieves *similar text*. It cannot
*traverse dependencies*, because the answer is rarely in a single paragraph — it
is in the **connections** between artifacts.

## 3. What was built

Two complementary retrieval layers over the same corpus:

| Layer | Technology | What it does |
|---|---|---|
| **Vector RAG** | Chroma + local embeddings (BGE), pluggable LLM | Retrieves relevant passages and (optionally) synthesizes a grounded, **cited** answer |
| **Knowledge graph** | In-process graph (NetworkX), file-persisted | Models artifacts as typed nodes and their relationships as edges; enables **dependency/impact traversal** |

Key capabilities delivered:

- **GraphRAG hybrid answering** — vector retrieval *plus* graph traversal, so
  answers include the dependency chain with per-source citations.
- **Impact Explorer** — pick any entity (a test case, defect, CNF, release note)
  and see everything connected to it across the lifecycle, rendered as an
  **interactive graph**.
- **Per-CNF release-note modeling** — mirrors reality, where each CNF ships its
  own release note on its own version cadence, and the "release" is an
  **assembled integration/compatibility view**. This unlocks cross-CNF
  questions (certified-together, minimum-version) a single-note model can't
  answer.
- **Browser GUI** — no coding needed to use it; a provider selector, a
  "use knowledge graph" toggle, answers with sources and a confidence signal.
- **Safety by design** — synthetic-only data, prompt-injection fencing of
  retrieved content, and a local-first option (no data leaves the machine).

**Anchor demonstration:** "Why did an acceptance test fail after the SAEGW-C
upgrade, and what fix is supported by the evidence?" The system traces the chain
— upgrade → event-parity test failure → triggering defect → raised alarm → FOA
gate blocked → Production hold — and cites the specific documents for each step.

## 4. Why this matters for the Autonomous Network journey

The telecom industry frames autonomous networks around **intent-driven,
closed-loop operations** across increasing levels of automation. Reaching higher
autonomy levels depends on machines being able to **reason over relationships**
between network state, changes, tests, faults, and knowledge — not just store
documents. This prototype demonstrates that reasoning pattern on the
**delivery/assurance** side:

| Autonomous-network capability | How this prototype contributes |
|---|---|
| **Knowledge-driven reasoning** | A knowledge graph turns scattered delivery artifacts into a connected, queryable model of dependencies — a building block for machine reasoning. |
| **Closed-loop assurance** | The anchor flow (change → test failure → root-cause defect → recommended fix, with evidence) is exactly the *observe → analyze → decide* portion of a closed loop, applied to acceptance/FOA. |
| **Impact & change analysis** | "What is affected if we change X?" is a prerequisite for safe autonomous change execution; the Impact Explorer shows that traversal directly. |
| **Intent / readiness gating** | Modeling gates (lab → FOA → Production) and what blocks them is a step toward machine-checkable readiness rather than manual sign-off. |
| **Explainability & trust** | Every answer is **grounded and cited**, which is essential for operator trust in any autonomous recommendation. |

In short: autonomous operation needs a **connected knowledge substrate** and
**explainable reasoning** over it. This prototype is a small, concrete
demonstration of that substrate for the delivery and acceptance domain.

## 5. Where it could go (if pursued)

- **Real data (private, on-prem):** ingest real artifacts (PDF/Word/Excel CIQs,
  Jira/ALM/ServiceNow exports) with strict sanitization/PII scrubbing; real data
  stays local and never leaves the environment.
- **Live signals:** connect to alarm/fault and change-management systems so the
  graph reflects current state, moving from static documents toward a live
  closed loop.
- **Quantified value:** an evaluation harness comparing standard RAG vs.
  graph-augmented answers, to measure the accuracy gain on relationship
  questions.
- **Deeper compatibility modeling:** multi-release certified-set comparison
  ("what changed between certified version sets").

## 6. Current status

A working end-to-end prototype: corpus ingested, knowledge graph built
(dozens of nodes and relationships over the delivery lifecycle), hybrid
answering and the interactive Impact Explorer both functional via a browser GUI.
Built reusing a prior document-RAG project, with the graph layer and GUI added
on top. Code and synthetic data are in a self-contained repository.

---

*Prepared for internal review. Prototype built on personal time with synthetic
data for learning and demonstration purposes.*
