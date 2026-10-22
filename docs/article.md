---
title: "When RAG isn't enough: a GraphRAG copilot for telecom network delivery"
---

# When RAG isn't enough: a GraphRAG copilot for telecom network delivery

*By Milind Agarwal · ~12 min read*

> **What this is.** A learning project that explores **GraphRAG** —
> knowledge-graph–augmented retrieval — over the delivery lifecycle of a
> cloud-native 5G packet core. It started as a plain document-RAG chatbot I'd
> built earlier, and grew a knowledge-graph layer on top to answer the
> *relationship* questions that plain retrieval quietly fails at. Everything
> here runs on **synthetic, sanitized data** — invented releases, network
> functions, test cases, and defects that resemble real delivery artifacts in
> *shape* but contain nothing real. The code is open source (MIT).

------------------------------------------------------------------------

## The problem this solves

In telecom network delivery, the work lives across a pile of disconnected
documents: per–network-function release notes, Methods of Procedure (MOPs),
Customer Information Questionnaires (CIQs), test-case catalogs, acceptance-test
results, defect registers, alarm dictionaries, troubleshooting runbooks,
implementation records. Any single document is easy to search. The questions
that actually matter in delivery are the ones that **span many of them at
once**:

> *"If we upgrade this network function, which test cases break, what's blocking
> go-live, and what's the evidence?"*

That is not a retrieval question. It's a **relationship** question. And that
distinction is the whole reason this project exists.

A plain Retrieval-Augmented Generation (RAG) pipeline answers *"what does this
document say?"* beautifully — it embeds chunks of text, finds the ones most
similar to your question, and hands them to a language model. But "what is
*affected* if I change X?" has no good answer in any single chunk of text. The
answer lives in the **connections** between artifacts: a test is *blocked by* a
defect, which was *reported in* a release note, which *documents* a network
function, which is *deployed on* an environment that *gates* go-live. Plain RAG
has no notion of those edges. It can only return paragraphs that happen to look
like your question.

So I built the thing that does: a knowledge graph, sitting next to the vector
store, that makes those relationships explicit and traversable.

------------------------------------------------------------------------

## The big picture (how it works in two layers)

The system has two retrieval layers over the same synthetic corpus, and the
interesting part is how they combine:

1.  **Vector RAG (the baseline).** Documents are chunked, embedded locally, and
    stored in a vector database. A question retrieves the most relevant passages
    and — optionally — a language model synthesizes a grounded, cited answer
    from them. This is the "what does it say?" layer.

2.  **A knowledge graph (the differentiator).** The same corpus is parsed into a
    typed graph: **nodes** are entities (test cases, defects, alarms, network
    functions, software versions, release notes, environments, documents) and
    **edges** are the relationships between them (`validates`, `blocked_by`,
    `fixed_in`, `reports`, `documents`, `certified_with`, `gates`, `precedes`,
    …). This is the "what's connected to what?" layer.

When you ask a question, the system detects which graph entities you mentioned
(by ID like `TC-204`, or by name like a network function), **traverses outward**
from them to pull in the connected neighborhood, and feeds that
relationship context to the answerer *alongside* the vector passages — each edge
carrying the source document it came from, so the graph is just as citable as
the text.

The result: the answer to *"what's impacted by this upgrade and what blocks
go-live?"* is assembled by walking the graph, not by hoping one paragraph
happened to state the whole chain.

------------------------------------------------------------------------

## Why a graph, and why not just a bigger RAG

It's a fair challenge: couldn't you just retrieve more chunks, or write the
dependencies into one big document, and let RAG find it? You can — and it's
brittle. You'd be pre-computing every answer by hand and hoping the phrasing
matches. The moment someone asks about a path you didn't spell out in prose, RAG
is blind to it.

A graph flips that. You state the *facts* once as edges (`TC-204 blocked_by
DEF-1203`, `DEF-1203 reported_in release-note-pcc`), and then **any** traversal
question — one hop, three hops, upstream, downstream — is answerable without
having written that specific answer anywhere. Impact analysis, dependency
tracing, "what else touches this" — these are graph-shaped problems, and a graph
solves a whole *class* of them at once.

I deliberately built it in two phases so the value of the graph is
*demonstrated, not assumed*: first the RAG baseline, then the graph layer on top,
with a toggle to turn the graph off and compare the two answers side by side on
the same question.

------------------------------------------------------------------------

## Modeling reality: release notes are per–network-function

One modeling decision is worth calling out, because it's where the synthetic
data stopped being a toy and started reflecting how delivery actually works.

My first cut had a single, tidy "release note" listing every network function
and its version in one table. Convenient — and wrong. In reality, each network
function ships its **own** release note, on its **own** version cadence, often
from a different vendor team. The "release" as a whole is not a source document
at all; it's an **integration view** that a delivery team *assembles* on top of
many individual notes — essentially a compatibility matrix saying "these
specific versions are certified to run together."

So I split the corpus accordingly: one release note per network function, plus a
separate integration/compatibility matrix. In the graph, the release became a
*derived* node that `includes` each certified `(function, version)` pair, with
`certified_with` and `requires_min_version` edges between versions — each sourced
from the right per-function note.

This isn't cosmetic. It unlocks a question class that was literally impossible
before: *"does this control-plane version require a minimum version of the
policy component?"* is a cross-document, cross-function compatibility question
that no single release note answers — but the graph (or the matrix it models)
does. The graph is, quite literally, doing the integration work a human does by
hand today.

------------------------------------------------------------------------

## The anchor demo: a failed acceptance test after an upgrade

Every demo needs one story told end-to-end. Mine is a failure chain:

An acceptance test (`TC-204`, event-parity on an interface) **fails** after a
control-plane network function is upgraded. Why? The graph traces it:

- `TC-204` is `blocked_by` defect `DEF-1203` (a counter reset on warm restart),
- `DEF-1203` `reported_in` the policy component's release note and `raised` an
  alarm (`ALM-SX-DOWN`),
- `TC-204` `gates` the go-live environment, which `precedes` production —
- so the failure doesn't just fail a test; it **holds the whole rollout**, and
  the recommended fix (a documented workaround + re-run) is reachable through a
  troubleshooting runbook that `references` the same defect and MOP.

Ask that question with the graph off, and you get relevant passages — useful,
but you have to connect the dots yourself. Ask it with the graph on, and the
dependency chain comes back assembled, with a citation on every link.

------------------------------------------------------------------------

## The Impact Explorer: seeing the graph

Answers are one thing; *exploration* is another. The browser GUI has a second
tab — an **Impact Explorer** — that is pure graph, no language model involved.
You pick any entity (a test case, a defect, a network function, a release note),
choose how many hops to traverse, and it renders the connected neighborhood as
an **interactive node-and-edge diagram**: nodes colored by type, the selected
entity highlighted, edges labeled with the relationship, draggable and
hoverable.

This is the single clearest one-screen answer to "why GraphRAG and not just
RAG?" — a reviewer picks an entity and immediately *sees* the slice of the
delivery lifecycle connected to it, which plain document search would never
assemble.

------------------------------------------------------------------------

## A word on the extractor (deterministic, on purpose)

For this synthetic corpus the entity/relationship extraction is **rule-based**,
not LLM-driven: a small set of ID patterns plus a curated, auditable table of
relationships, each carrying the document it came from. For a clean, invented
corpus that's the right call — it's reproducible, needs no API key, and is 100%
faithful to the text. Crucially, the graph layer's *value* (traversal, impact
analysis) is independent of *how* the graph was populated. So for messy
real-world data later, an LLM-assisted extractor can slot in behind the exact
same graph interface without touching retrieval or the UI.

------------------------------------------------------------------------

## Running it

The whole thing is self-contained and local — no server, no Docker, no cloud
required to try it.

```bash
python -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m src.ingest     # embed the synthetic corpus into the vector store
./.venv/bin/python -m src.extract    # build the knowledge graph (~36 nodes, ~69 edges)
./.venv/bin/streamlit run app.py     # browser GUI: Ask a question + Impact Explorer
```

By default the answerer runs in *extractive* mode — it shows the retrieved
passages and the traversed graph relationships with no language model at all, so
it works with zero API keys. Point it at a cloud model or a local small model
for synthesized prose instead; the provider is a one-line config switch.

------------------------------------------------------------------------

## Honest limitations (the questions a sharp reader will ask)

- **The data is synthetic.** It's designed around one clean anchor story so the
  relationships are tidy. Real delivery data is messier — inconsistent naming,
  missing links, contradictory records. Proving the graph adds value on clean
  data first is deliberate; hardening it for real data is a separate job.
- **The extractor is tuned to the corpus vocabulary.** Rule-based extraction is
  faithful but not general; real data needs an LLM-assisted extractor (the
  interface is already built to accept one).
- **Ingestion handles text formats only today.** Real artifacts arrive as PDF,
  Word, and Excel (CIQs are notoriously spreadsheets). PDF/XLSX ingestion plus a
  PII-scrubbing pass are the main gaps before real data could flow in — and real
  data would stay strictly local, never in the shareable repo.
- **The graph is small and in-process.** It uses an in-memory graph persisted to
  a single JSON file — right-sized for ~100 nodes. A server-backed graph store
  could be swapped in behind the same interface if it ever needed to scale; the
  config hooks for that are already present but dormant.

------------------------------------------------------------------------

## Where this fits: the autonomous-network angle

The telecom industry's push toward **autonomous networks** is about
intent-driven, closed-loop operations — and reaching higher levels of autonomy
depends on machines being able to **reason over relationships** between network
state, changes, tests, faults, and knowledge, not just store documents. This
project is a small, concrete demonstration of that reasoning pattern on the
delivery and assurance side: a connected knowledge substrate, plus explainable,
cited answers. The anchor flow — change → failed test → root-cause defect →
recommended fix with evidence — is exactly the *observe → analyze → decide*
portion of a closed loop, applied to acceptance and go-live readiness.

------------------------------------------------------------------------

## Toolset

- **Knowledge graph:** an in-process graph library (file-persisted; no server) —
  right-sized for the problem, with a backend-agnostic interface so a
  server-backed store could replace it later.
- **Vector search:** a local vector database with local, offline embeddings
  (ONNX, no GPU, no PyTorch).
- **Answer engine:** pluggable — a cloud model, a local small model, or an
  extractive no-model fallback that always works.
- **Extraction:** deterministic, rule-based, provenance-carrying (swap in an
  LLM extractor for real data).
- **UI:** a browser app with a Q&A tab and an interactive graph-visualization
  Impact Explorer.
- **Language:** Python. **License:** MIT.

------------------------------------------------------------------------

## Closing thought

Plain RAG is a genuinely great hammer — but not every question is a nail. The
questions that keep delivery teams up at night are about *consequences*: if I
touch this, what else moves? Those are graph questions. Building the graph layer
turned a document search tool into something that can actually trace a failure
from an upgrade all the way to a held production rollout, and show its work at
every step. That's the difference between a chatbot that *finds* text and one
that can *reason* about a delivery program.

*Code and synthetic data: open source (MIT). Built on personal time, with
invented data, for learning and demonstration.*
