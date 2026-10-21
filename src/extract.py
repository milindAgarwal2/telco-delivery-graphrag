"""Deterministic entity + relationship extractor (Phase 2).

Builds the delivery knowledge graph from the synthetic DMC corpus and persists
it via :class:`src.graph.GraphStore`.

Why deterministic (not LLM-assisted) for this corpus
----------------------------------------------------
The synthetic documents use a small, consistent vocabulary of **typed IDs**
(``TC-204``, ``DEF-1203``, ``ALM-SX-DOWN``, ``MOP-5521``, ``CIQ-8807``,
``NIR-3310``, ``RUN-77``), named **network functions** (cSAEGW-C/-U, cMME, PCC,
PCG), **software versions** (``24.3.0-cp`` …), **environments** (Lab/FOA/
Production) and a fixed set of **relationship verbs** (validates, blocked_by,
fixed_in, requires, gates, precedes, deployed_on, observed_on, describes …).

For a corpus this clean a rule-based pass is **reproducible, needs no API key,
and is 100% faithful to the text** — exactly what a trustworthy demo wants. The
graph layer's value (traversal, impact analysis) is independent of HOW the graph
was populated, so an LLM extractor could be swapped in later for messy real data
without changing :mod:`src.graph` or :mod:`src.graph_retrieval`.

Entity ID patterns
-------------------
    TC-\\d+      TestCase          DEF-\\d+     Defect
    ALM-[A-Z0-9-]+ Alarm           MOP-\\d+     Document (MOP)
    CIQ-\\d+     Document (CIQ)     NIR-\\d+     Document (NIR)
    RUN-\\d+     Document (Runbook) HLD         Document (HLD)
    network functions, software versions, environments: fixed vocab (below)
"""

import logging
import os
import re

try:
    from .graph import GraphStore
    from .logging_config import setup_logging
except ImportError:  # pragma: no cover
    from graph import GraphStore
    from logging_config import setup_logging

setup_logging()
logger = logging.getLogger("extract")

SYNTHETIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "synthetic"
)

# --- Fixed vocabularies (grounded in the synthetic corpus) ------------------
NETWORK_FUNCTIONS = ["cSAEGW-C", "cSAEGW-U", "cMME", "PCC", "PCG"]
ENVIRONMENTS = ["Lab", "FOA", "Production"]
INTERFACES = ["Sx", "S1-AP"]

# ID regexes -> (node_type, optional_subtype_for_documents)
ID_PATTERNS = [
    (re.compile(r"\bTC-\d+\b"), "TestCase", None),
    (re.compile(r"\bDEF-\d+\b"), "Defect", None),
    (re.compile(r"\bALM-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"), "Alarm", None),
    (re.compile(r"\bMOP-\d+\b"), "Document", "MOP"),
    (re.compile(r"\bCIQ-\d+\b"), "Document", "CIQ"),
    (re.compile(r"\bNIR-\d+\b"), "Document", "NIR"),
    (re.compile(r"\bRUN-\d+\b"), "Document", "Runbook"),
]
# Software versions like 24.3.0-cp, 24.3.1, 7.2.0
VERSION_RE = re.compile(r"\b\d+\.\d+(?:\.\d+)?(?:-[a-z]+)?\b")

# Document node for the release itself.
RELEASE_ID = "DMC-24.3"

# Per-CNF release notes (Option-1 modeling). Each is a ReleaseNote node that
# documents exactly one CNF + its certified version. Keyed id -> (label, file,
# nf, version). The consolidated DMC release note no longer exists; the program
# view is assembled by the integration matrix below.
INTEGRATION_MATRIX_FILE = "dmc-24.3-integration-matrix.md"
RELEASE_NOTES = {
    "RN-cSAEGW-C-24.3.0-cp": ("cSAEGW-C 24.3.0-cp release note",
                              "release-note-csaegw-c-24.3.0-cp.md", "cSAEGW-C", "24.3.0-cp"),
    "RN-cSAEGW-U-24.3.0-up": ("cSAEGW-U 24.3.0-up release note",
                              "release-note-csaegw-u-24.3.0-up.md", "cSAEGW-U", "24.3.0-up"),
    "RN-cMME-24.3.1": ("cMME 24.3.1 release note",
                       "release-note-cmme-24.3.1.md", "cMME", "24.3.1"),
    "RN-PCC-7.2.0": ("PCC 7.2.0 release note",
                     "release-note-pcc-7.2.0.md", "PCC", "7.2.0"),
    "RN-PCG-7.2.0": ("PCG 7.2.0 release note",
                     "release-note-pcg-7.2.0.md", "PCG", "7.2.0"),
}


def _iter_docs():
    """Yield ``(file_name, text)`` for each synthetic markdown doc."""
    for name in sorted(os.listdir(SYNTHETIC_DIR)):
        if not name.endswith((".md", ".markdown", ".txt")):
            continue
        path = os.path.join(SYNTHETIC_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            yield name, f.read()


def _find_ids(text):
    """Return a set of ``(id, type, subtype)`` for every typed ID in ``text``."""
    found = set()
    for rx, ntype, subtype in ID_PATTERNS:
        for m in rx.findall(text):
            found.add((m, ntype, subtype))
    return found


def extract_entities(graph, docs):
    """First pass: create all nodes (documents, releases, NFs, versions,
    environments, interfaces, and every typed ID encountered)."""
    # Core fixed-vocabulary entities (present across the corpus).
    graph.add_node(RELEASE_ID, "Release", label="DMC Release 24.3")
    graph.add_node("ECDS-7.2", "Release", label="ECDS Release 7.2")
    for nf in NETWORK_FUNCTIONS:
        graph.add_node(nf, "NetworkFunction", label=nf)
    for env in ENVIRONMENTS:
        graph.add_node(env, "Environment", label=env)
    for itf in INTERFACES:
        graph.add_node(itf, "Interface", label=itf)

    # Per-CNF release-note documents (Option-1 modeling).
    for rn_id, (label, file, _nf, _ver) in RELEASE_NOTES.items():
        graph.add_node(rn_id, "ReleaseNote", label=label, source_doc=file, doc_type="ReleaseNote")

    # Typed IDs from every document (+ a Document node per source file).
    for name, text in docs:
        for nid, ntype, subtype in _find_ids(text):
            props = {}
            if subtype:
                props["doc_type"] = subtype
            graph.add_node(nid, ntype, source_doc=name, **props)
        # Software versions (only attach the well-known ones to avoid noise).
        for ver in set(VERSION_RE.findall(text)):
            if ver in ("24.3.0-cp", "24.3.0-up", "24.3.1", "7.2.0"):
                graph.add_node(ver, "SoftwareVersion", label=ver)


# --- Relationship rules -----------------------------------------------------
# Each rule is grounded in explicit statements in the corpus. We keep them as
# data so the mapping from text -> graph is auditable at a glance.
RELATIONSHIPS = [
    # (src, rel, dst, provenance_doc)
    # --- Release composition / versions (now sourced from the integration
    #     matrix, which assembles the per-CNF versions into DMC 24.3) ---
    ("ECDS-7.2", "supports", "DMC-24.3", INTEGRATION_MATRIX_FILE),
    ("DMC-24.3", "includes", "24.3.0-cp", INTEGRATION_MATRIX_FILE),
    ("DMC-24.3", "includes", "24.3.0-up", INTEGRATION_MATRIX_FILE),
    ("DMC-24.3", "includes", "24.3.1", INTEGRATION_MATRIX_FILE),
    ("DMC-24.3", "includes", "7.2.0", INTEGRATION_MATRIX_FILE),
    # Cross-CNF compatibility (certified_with) — from the integration matrix.
    ("24.3.0-cp", "certified_with", "24.3.0-up", INTEGRATION_MATRIX_FILE),
    ("24.3.0-cp", "certified_with", "7.2.0", INTEGRATION_MATRIX_FILE),
    # Minimum-version requirements (cross-CNF) — from the integration matrix.
    ("24.3.0-cp", "requires_min_version", "7.2.0", INTEGRATION_MATRIX_FILE),
    # --- NF -> version (now sourced from each per-CNF release note) ---
    ("cSAEGW-C", "runs", "24.3.0-cp", "release-note-csaegw-c-24.3.0-cp.md"),
    ("cSAEGW-U", "runs", "24.3.0-up", "release-note-csaegw-u-24.3.0-up.md"),
    ("cMME", "runs", "24.3.1", "release-note-cmme-24.3.1.md"),
    ("PCC", "runs", "7.2.0", "release-note-pcc-7.2.0.md"),
    ("PCG", "runs", "7.2.0", "release-note-pcg-7.2.0.md"),
    # --- Each ReleaseNote documents its CNF + version; PCC/CNF notes report
    #     their own defects (provenance now correctly per-CNF) ---
    ("RN-cSAEGW-C-24.3.0-cp", "documents", "cSAEGW-C", "release-note-csaegw-c-24.3.0-cp.md"),
    ("RN-cSAEGW-C-24.3.0-cp", "documents", "24.3.0-cp", "release-note-csaegw-c-24.3.0-cp.md"),
    ("RN-cSAEGW-C-24.3.0-cp", "reports", "DEF-1187", "release-note-csaegw-c-24.3.0-cp.md"),
    ("RN-cSAEGW-U-24.3.0-up", "documents", "cSAEGW-U", "release-note-csaegw-u-24.3.0-up.md"),
    ("RN-cSAEGW-U-24.3.0-up", "documents", "24.3.0-up", "release-note-csaegw-u-24.3.0-up.md"),
    ("RN-cMME-24.3.1", "documents", "cMME", "release-note-cmme-24.3.1.md"),
    ("RN-cMME-24.3.1", "documents", "24.3.1", "release-note-cmme-24.3.1.md"),
    ("RN-cMME-24.3.1", "reports", "DEF-1250", "release-note-cmme-24.3.1.md"),
    ("RN-PCC-7.2.0", "documents", "PCC", "release-note-pcc-7.2.0.md"),
    ("RN-PCC-7.2.0", "documents", "7.2.0", "release-note-pcc-7.2.0.md"),
    ("RN-PCC-7.2.0", "reports", "DEF-1203", "release-note-pcc-7.2.0.md"),
    ("RN-PCG-7.2.0", "documents", "PCG", "release-note-pcg-7.2.0.md"),
    ("RN-PCG-7.2.0", "documents", "7.2.0", "release-note-pcg-7.2.0.md"),
    # Required procedures / documents for the release (now via integration matrix)
    ("DMC-24.3", "requires", "MOP-5521", INTEGRATION_MATRIX_FILE),
    ("DMC-24.3", "requires", "CIQ-8807", INTEGRATION_MATRIX_FILE),
    ("DMC-24.3", "requires", "NIR-3310", INTEGRATION_MATRIX_FILE),
    # MOP describes the cSAEGW-C upgrade to 24.3.0-cp
    ("MOP-5521", "upgrades", "cSAEGW-C", "mop-5521-upgrade-csaegw-c.md"),
    ("MOP-5521", "applies_version", "24.3.0-cp", "mop-5521-upgrade-csaegw-c.md"),
    ("CIQ-8807", "describes", "MOP-5521", "ciq-8807-foa-parameters.md"),
    # Test cases validate NFs / features
    ("TC-204", "validates", "cSAEGW-C", "test-case-catalog-dmc-24.3.md"),
    ("TC-204", "validates", "Sx", "test-case-catalog-dmc-24.3.md"),
    ("TC-205", "validates", "cSAEGW-C", "test-case-catalog-dmc-24.3.md"),
    ("TC-205", "validates", "MOP-5521", "test-case-catalog-dmc-24.3.md"),
    ("TC-209", "validates", "PCC", "test-case-catalog-dmc-24.3.md"),
    ("TC-311", "validates", "cMME", "test-case-catalog-dmc-24.3.md"),
    ("TC-311", "validates", "S1-AP", "test-case-catalog-dmc-24.3.md"),
    # Defects: status / affects / fixed_in / blocks
    ("DEF-1187", "fixed_in", "24.3.0-cp", "defect-register-dmc-24.3.md"),
    ("DEF-1250", "fixed_in", "24.3.1", "defect-register-dmc-24.3.md"),
    ("DEF-1250", "validated_by", "TC-311", "defect-register-dmc-24.3.md"),
    ("DEF-1203", "affects", "PCC", "defect-register-dmc-24.3.md"),
    ("DEF-1203", "observed_alarm", "ALM-SX-DOWN", "defect-register-dmc-24.3.md"),
    # The anchor failure chain
    ("TC-204", "blocked_by", "DEF-1203", "aat-test-results-dmc-24.3.md"),
    ("TC-209", "blocked_by", "DEF-1203", "aat-test-results-dmc-24.3.md"),
    ("TC-204", "raised_alarm", "ALM-SX-DOWN", "aat-test-results-dmc-24.3.md"),
    ("TC-204", "tested_in", "FOA", "aat-test-results-dmc-24.3.md"),
    ("DEF-1203", "fixed_in_release", "DMC-24.4", "defect-register-dmc-24.3.md"),
    # Runbook / troubleshooting
    ("RUN-77", "diagnoses", "ALM-SX-DOWN", "runbook-77-sx-event-parity.md"),
    ("RUN-77", "diagnoses", "TC-204", "runbook-77-sx-event-parity.md"),
    ("RUN-77", "references", "DEF-1203", "runbook-77-sx-event-parity.md"),
    ("RUN-77", "references", "MOP-5521", "runbook-77-sx-event-parity.md"),
    # Alarms observed on NFs / interfaces
    ("ALM-SX-DOWN", "observed_on", "cSAEGW-C", "alarm-catalog-packet-core.md"),
    ("ALM-SX-DOWN", "monitors", "Sx", "alarm-catalog-packet-core.md"),
    ("ALM-S1AP-TIMER", "observed_on", "cMME", "alarm-catalog-packet-core.md"),
    ("ALM-S1AP-TIMER", "monitors", "S1-AP", "alarm-catalog-packet-core.md"),
    ("ALM-PCG-CHG", "observed_on", "PCG", "alarm-catalog-packet-core.md"),
    # Interfaces between NFs
    ("Sx", "between", "cSAEGW-C", "hld-packet-core-24.x.md"),
    ("Sx", "between", "cSAEGW-U", "hld-packet-core-24.x.md"),
    ("S1-AP", "between", "cMME", "hld-packet-core-24.x.md"),
    # Deployment topology (NIR): NFs deployed on environments
    ("cSAEGW-C", "deployed_on", "FOA", "nir-3310-implementation-record.md"),
    ("cSAEGW-U", "deployed_on", "FOA", "nir-3310-implementation-record.md"),
    ("cMME", "deployed_on", "FOA", "nir-3310-implementation-record.md"),
    ("PCC", "deployed_on", "FOA", "nir-3310-implementation-record.md"),
    ("PCG", "deployed_on", "FOA", "nir-3310-implementation-record.md"),
    # Gating / environment progression (the impact spine)
    ("TC-204", "gates", "FOA", "aat-test-results-dmc-24.3.md"),
    ("Lab", "gates", "FOA", "nir-3310-implementation-record.md"),
    ("FOA", "precedes", "Production", "nir-3310-implementation-record.md"),
]


def extract_relationships(graph):
    """Second pass: add the curated, text-grounded relationships. Each edge
    carries its provenance document so answers can cite where a link came
    from. Also ensure any version/release endpoints exist."""
    # Make sure release endpoints referenced only in rules exist.
    graph.add_node("DMC-24.4", "Release", label="DMC Release 24.4 (future)")
    for src, rel, dst, doc in RELATIONSHIPS:
        graph.add_edge(src, rel, dst, source_doc=doc)


def build_graph(path=None, persist=True):
    """Build the full knowledge graph from the synthetic corpus and (by default)
    persist it. Returns the populated :class:`GraphStore`."""
    graph = GraphStore(path=path)
    docs = list(_iter_docs())
    logger.info("extracting from %d synthetic documents", len(docs))
    extract_entities(graph, docs)
    extract_relationships(graph)
    stats = graph.stats()
    logger.info("graph built: %(nodes)d nodes, %(edges)d edges", stats)
    if persist:
        graph.save()
    return graph


def main():
    """CLI: build and persist the graph, then print a short summary."""
    graph = build_graph()
    stats = graph.stats()
    print("\n" + "=" * 60)
    print("Knowledge graph built from data/synthetic/")
    print("=" * 60)
    print(f"Nodes: {stats['nodes']}   Edges: {stats['edges']}")
    print("Node types:")
    for t, c in sorted(stats["node_types"].items()):
        print(f"  {t:<16} {c}")
    print(f"\nPersisted to: {graph.path}")


if __name__ == "__main__":
    main()
