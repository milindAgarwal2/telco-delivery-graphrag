"""Graph-augmented retrieval (Phase 2).

Turns the knowledge graph into extra, relationship-aware context for the
answerer. This is the piece that lets the system answer *dependency / impact*
questions that plain vector RAG cannot:

    "Which test cases and documents are impacted by the SAEGW-C upgrade,
     and what blocks FOA readiness?"

Vector RAG retrieves passages that are *textually similar* to the question. It
has no notion that TC-204 is ``blocked_by`` DEF-1203 which ``observed_alarm``
ALM-SX-DOWN which ``gates`` FOA — unless some single passage happens to state
the whole chain. The graph makes that chain explicit and traversable.

Flow
----
1. **Anchor detection** — find graph entities mentioned in the question (by ID
   like ``TC-204`` or by known name/alias like ``SAEGW-C``). If none are found
   in the question text, fall back to anchors mentioned in the vector hits'
   metadata/content so the graph still contributes.
2. **Traversal** — for each anchor, pull its ``impacted_subgraph`` (bidirectional
   BFS to ``max_hops``).
3. **Serialization** — render the reached relationships as compact, cited lines
   (``TC-204 --blocked_by--> DEF-1203  [source: aat-test-results-cnpd-24.3.md]``)
   that slot into the LLM context next to the vector passages.

The graph context is produced as plain text so it reuses the exact same
prompt-injection fencing and provider abstraction as Phase 1 — no new trust
surface.
"""

import logging
import re

try:
    from .graph import load_graph
    from .logging_config import setup_logging
except ImportError:  # pragma: no cover
    from graph import load_graph
    from logging_config import setup_logging

setup_logging()
logger = logging.getLogger("graph_retrieval")

# Typed-ID pattern (matches the extractor's vocabulary) for anchor detection.
_ID_RE = re.compile(
    r"\b(?:TC|DEF|MOP|CIQ|NIR|RUN)-\d+\b|\bALM-[A-Z0-9]+(?:-[A-Z0-9]+)*\b"
)

# Named entities that aren't ID-shaped, with lightweight aliases so natural
# phrasing still anchors ("the SAE gateway control plane" -> SAEGW-C).
_NAME_ALIASES = {
    "SAEGW-C": ["saegw-c", "csaegw-c", "saegw control", "control plane of the combined sae"],
    "SAEGW-U": ["saegw-u", "csaegw-u", "user plane of the combined sae"],
    "MME": ["mme", "cmme", "mobility management"],
    "PCC": ["pcc", "policy control"],
    "PCG": ["pcg", "charging gateway"],
    "FOA": ["foa", "first office application"],
    "Production": ["production", "prod rollout"],
    "Lab": ["lab acceptance", "lab environment"],
    "Sx": ["sx interface", "sx event", "event-parity", "event parity"],
    "S1-AP": ["s1-ap", "s1ap"],
    "CNPD-24.3": ["cnpd 24.3", "release 24.3", "cnpd release 24.3"],
}


def detect_anchors(text, graph):
    """Return a de-duplicated, ordered list of graph node-ids mentioned in
    ``text`` — by typed ID or by known name/alias. Only ids present in the
    graph are returned."""
    if not text:
        return []
    found = []
    seen = set()

    # 1) Typed IDs (exact).
    for m in _ID_RE.findall(text):
        if m in seen:
            continue
        if graph.has_node(m):
            seen.add(m)
            found.append(m)

    # 2) Named entities / aliases (case-insensitive substring).
    low = text.lower()
    for node_id, aliases in _NAME_ALIASES.items():
        if node_id in seen or not graph.has_node(node_id):
            continue
        if node_id.lower() in low or any(a in low for a in aliases):
            seen.add(node_id)
            found.append(node_id)

    return found


def _anchors_from_docs(docs, graph, limit=4):
    """Fallback anchors: scan vector-hit content/metadata for graph entities."""
    seen = set()
    anchors = []
    for d in docs:
        blob = (d.page_content or "") + " " + " ".join(
            str(v) for v in (d.metadata or {}).values()
        )
        for a in detect_anchors(blob, graph):
            if a not in seen:
                seen.add(a)
                anchors.append(a)
                if len(anchors) >= limit:
                    return anchors
    return anchors


def graph_context(question, docs=None, max_hops=2, max_anchors=4, max_edges=40):
    """Build graph-derived context for a question.

    Parameters
    ----------
    question : str
    docs : list, optional
        Vector hits (LangChain Documents) used only as a fallback source of
        anchors when the question names no entity directly.
    max_hops : int
        Traversal depth from each anchor.

    Returns
    -------
    dict with:
        anchors : list of anchor node-ids used
        text    : serialized, cited relationship lines (str; "" if no anchors)
        edges   : list of (src, rel, dst) included
    """
    graph = load_graph()
    if graph.stats()["nodes"] == 0:
        logger.warning("graph is empty; run `python -m src.extract` first")
        return {"anchors": [], "text": "", "edges": []}

    anchors = detect_anchors(question, graph)
    if not anchors and docs:
        anchors = _anchors_from_docs(docs, graph)
    anchors = anchors[:max_anchors]
    if not anchors:
        return {"anchors": [], "text": "", "edges": []}

    # Union the impacted subgraphs of all anchors (dedupe edges).
    edge_set = []
    seen_edges = set()
    reached_nodes = {}
    for a in anchors:
        sub = graph.impacted_subgraph(a, max_hops=max_hops)
        for n in sub["nodes"]:
            reached_nodes.setdefault(n["id"], n)
        for s, rel, d in sub["edges"]:
            key = (s, rel, d)
            if key not in seen_edges:
                seen_edges.add(key)
                edge_set.append(key)
            if len(edge_set) >= max_edges:
                break

    # Serialize with provenance so the LLM can cite the graph just like a doc.
    lines = []
    for s, rel, d in edge_set:
        # Recover provenance for this specific edge if present.
        prov = ""
        for es, erel, ed, props in graph.edges():
            if (es, erel, ed) == (s, rel, d):
                prov = props.get("source_doc", "")
                break
        tail = f"  [source: {prov}]" if prov else ""
        lines.append(f"{s} --{rel}--> {d}{tail}")

    header = (
        "KNOWLEDGE-GRAPH RELATIONSHIPS (anchors: "
        + ", ".join(anchors)
        + f"; traversal depth {max_hops}):"
    )
    text = header + "\n" + "\n".join(lines) if lines else ""
    logger.info("graph_context | anchors=%s edges=%d", anchors, len(edge_set))
    return {"anchors": anchors, "text": text, "edges": edge_set}


def format_impact_report(node_id, max_hops=3):
    """Human-readable impact report for a single entity (CLI/eval helper)."""
    graph = load_graph()
    if not graph.has_node(node_id):
        return f"'{node_id}' is not in the graph."
    sub = graph.impacted_subgraph(node_id, max_hops=max_hops)
    lines = [f"Impact analysis for {node_id} (up to {max_hops} hops):", ""]
    by_hop = {}
    for n in sub["nodes"]:
        by_hop.setdefault(n["hops"], []).append(n)
    for hop in sorted(by_hop):
        if hop == 0:
            continue
        label = f"{hop} hop" + ("s" if hop > 1 else "")
        items = ", ".join(f"{n['id']}({n.get('type','?')})" for n in by_hop[hop])
        lines.append(f"  {label}: {items}")
    lines.append("")
    lines.append("Relationships:")
    for s, rel, d in sub["edges"]:
        lines.append(f"  {s} --{rel}--> {d}")
    return "\n".join(lines)


def main():
    """CLI: print an impact report for an entity (default: TC-204)."""
    import sys

    node = sys.argv[1] if len(sys.argv) > 1 else "TC-204"
    print(format_impact_report(node))


if __name__ == "__main__":
    main()
