# DMC Delivery GraphRAG — Document Inventory

**Project:** telco-delivery-graphrag (learning/portfolio GraphRAG over a 5G/telecom DMC delivery lifecycle)
**Purpose of this document:** A complete list of the documents the project uses today, plus the document types the model expects or anticipates — so real-world comparative documents can be scouted.

> Note on data policy: Only synthetic/sanitized data lives in the repo (`data/synthetic/`). Any real documents must go in the git-ignored `data/private/` and must never be committed.

---

## Part 1 — Documents that exist today (the 10 in `data/synthetic/`)

These are the 10 synthetic files currently ingested and modeled into the knowledge graph.

| # | Synthetic file | Type | Content it carries | Real comparative to look for |
|---|---|---|---|---|
| 1 | release-note-dmc-24.3.md | Release Note | NF versions, features, known issues, required procedures, gating | Vendor CNF/program release notes, software bulletins, CPI docs (PDF) |
| 2 | mop-5521-upgrade-csaegw-c.md | MOP | Upgrade steps, prerequisites, rollback, post-checks | Method of Procedure / change runbook (ServiceNow/Remedy change record, Word/PDF) |
| 3 | ciq-8807-foa-parameters.md | CIQ | Per-environment parameters (pool size, heartbeat, policy profile, endpoints) | Customer Information Questionnaire — usually Excel/XLSX |
| 4 | nir-3310-implementation-record.md | NIR | Deployment topology, NFs per env, interfaces, environment progression | Network Implementation Record / As-Built / LLD |
| 5 | hld-packet-core-24.x.md | HLD | NFs, interfaces, environment model, delivery lifecycle | High-Level Design / solution design (Word/PDF + Visio) |
| 6 | aat-test-results-dmc-24.3.md | Test Results | Pass/fail per test case, failure analysis, FOA readiness | AAT/UAT acceptance test report (ALM/qTest/Xray/TestRail export, Excel/PDF) |
| 7 | test-case-catalog-dmc-24.3.md | Test Catalog | Test cases with validates/preconditions/pass criteria | Test plan / test repository (ALM/Xray/TestRail, Excel) |
| 8 | defect-register-dmc-24.3.md | Defect Register | Defects with severity, status, fixed_in, blocks | Jira / ServiceNow / vendor trouble-ticket (TR/CSR) export |
| 9 | alarm-catalog-packet-core.md | Alarm Catalog | Alarm definitions, causes, first actions | Vendor alarm/FM dictionary, or live EMS/NMS alarm export |
| 10 | runbook-77-sx-event-parity.md | Runbook | When-to-use, diagnosis steps, recommended fix | Ops runbook / KB article / SOP |

---

## Part 2 — Document types the model expects but does not have yet

These came out of design discussions and the graph's structure. They are not in the repo, but the model anticipates them — strong candidates for real comparatives.

### A. Per-CNF release notes

Real release notes are published per CNF (containerized network function) by the vendor, not as one consolidated DMC note. So instead of file #1 above, reality gives you:

- release-note-cSAEGW-C-<ver> (control plane)
- release-note-cSAEGW-U-<ver> (user plane)
- release-note-cMME-<ver>
- release-note-PCC-<ver>
- release-note-PCG-<ver>
- Plus an integration / compatibility matrix the delivery team assembles (which CNF versions are certified together). This is often a spreadsheet.

### B. Documents implied by the graph but with no source doc yet

The graph references these entities; in real life each has backing paperwork:

- Change records / maintenance-window tickets — the ticket wrapping each MOP execution (ServiceNow/Remedy).
- Rollback / back-out plans — sometimes separate from the MOP.
- FOA readiness / go-no-go sign-off — the gate decision document (the model has `gates`/`precedes` edges but no sign-off doc).
- Compatibility / interoperability matrix — cross-CNF version compatibility (ties to the per-CNF notes above).
- Network inventory / CMDB export — what is actually deployed where (backs the NIR's topology).

### C. Real-world telco delivery document types not yet modeled

Worth knowing these exist, if scope is extended later:

- CIQ response / site survey (the filled-in CIQ per site)
- SOW / contract or program scope document
- Requirements / feature specification (the "Requirements" lifecycle stage; HLD references it but there is no doc)
- Acceptance criteria / Definition of Done document
- Handover / operational-readiness package (the "Handover" lifecycle stage)
- PCAP / trace captures and log bundles (diagnostic evidence behind defects — already gitignored as sensitive)
- KPI / performance baseline report (what "pass" means numerically)

---

## Part 3 — Prioritized shortlist for scouting real comparatives

If collecting real documents, these give the most graph value per document because they are full of cross-referenced IDs:

1. Defect register / Jira export — richest relationship source (blocks, fixed_in, affects).
2. Test results + test catalog — the validates / blocked_by backbone.
3. Per-CNF release notes + compatibility matrix — the integration story.
4. CIQ (Excel) — highest-value structured doc; also the biggest format gap (needs XLSX ingestion).
5. MOP + its change record — the action that triggers the whole impact chain.

The narrative docs (HLD, runbook) are useful but plain RAG already handles them; the five above are where the graph earns its keep.

---

## Practical note for when real documents are collected

Four of the highest-value real documents (CIQ, test catalog, test results, defect register) typically arrive as Excel or tool exports, and release notes / HLDs as PDF or Word. Current ingestion only reads `.md`, `.txt`, and `.json` — so collecting real comparatives in those formats is also the trigger to build PDF/XLSX ingestion. Anything real goes in the gitignored `data/private/`, never the repo.
