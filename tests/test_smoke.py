"""Smoke tests for the DMC Delivery GraphRAG project.

These are fast, dependency-light checks that the core wiring holds together:
- every src module imports,
- the knowledge graph builds from the synthetic corpus,
- the anchor dependency chain is traversable,
- the backend-agnostic GraphStore round-trips to JSON.

They deliberately avoid the vector store (Chroma) so they run quickly without an
ingest step. Run with:  ./.venv/bin/pytest -q
"""

import os
import sys

import pytest

# Make the repo root importable.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_all_src_modules_import():
    """Every core module should import without error."""
    import src.config          # noqa: F401
    import src.logging_config  # noqa: F401
    import src.graph           # noqa: F401
    import src.extract         # noqa: F401
    import src.graph_retrieval  # noqa: F401
    # retrieval/providers/rag/ingest pull in heavier deps but should still import
    import src.retrieval       # noqa: F401
    import src.providers       # noqa: F401
    import src.rag             # noqa: F401
    import src.ingest          # noqa: F401


def test_graph_builds_from_synthetic():
    """Building the graph from data/synthetic should yield a non-trivial graph
    with the expected node types and no isolated nodes."""
    from src.extract import build_graph

    g = build_graph(persist=False)
    stats = g.stats()
    assert stats["nodes"] >= 30, stats
    assert stats["edges"] >= 50, stats
    # Expected entity types are present.
    for t in ("TestCase", "Defect", "Alarm", "NetworkFunction", "ReleaseNote"):
        assert t in stats["node_types"], (t, stats["node_types"])
    # No orphaned/isolated nodes.
    isolated = [nid for nid, _ in g.nodes() if not g.neighbors(nid)]
    assert isolated == [], f"isolated nodes: {isolated}"


def test_anchor_impact_chain_traversable():
    """The anchor failure chain must be reachable from the cSAEGW-C upgrade."""
    from src.extract import build_graph

    g = build_graph(persist=False)
    reached = {n["id"] for n in g.impacted_subgraph("cSAEGW-C", max_hops=4)["nodes"]}
    for entity in ("TC-204", "DEF-1203", "ALM-SX-DOWN", "FOA", "Production"):
        assert entity in reached, f"{entity} not reachable from cSAEGW-C"


def test_per_cnf_provenance():
    """DEF-1203 should be reported by the PCC release note (per-CNF provenance)."""
    from src.extract import build_graph

    g = build_graph(persist=False)
    reporters = [
        (s, p.get("source_doc"))
        for s, rel, d, p in g.edges()
        if rel == "reports" and d == "DEF-1203"
    ]
    assert reporters, "no 'reports' edge for DEF-1203"
    assert any("pcc" in (src or "").lower() for src, _doc in reporters), reporters


def test_graphstore_json_roundtrip(tmp_path):
    """GraphStore should save and reload identically."""
    from src.graph import GraphStore

    path = str(tmp_path / "g.json")
    g = GraphStore(path=path)
    g.add_node("A", "TestCase")
    g.add_node("B", "Defect")
    g.add_edge("A", "blocked_by", "B")
    g.add_edge("A", "blocked_by", "B")  # dedup
    g.save()

    g2 = GraphStore(path=path).load()
    assert g2.stats()["nodes"] == 2
    assert g2.stats()["edges"] == 1  # the duplicate was de-duplicated
    # neighbors() returns (neighbor_id, rel, direction) — from A, the out-edge
    # leads to B.
    assert ("B", "blocked_by", "out") in g2.neighbors("A")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
