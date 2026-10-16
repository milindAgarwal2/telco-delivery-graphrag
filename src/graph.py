"""Backend-agnostic knowledge-graph store (Phase 2).

A small property-graph abstraction over an in-process **NetworkX** directed
multigraph, persisted to a single JSON file. No server, no Docker — right-sized
for this project's ~100-node delivery graph.

Why an abstraction (not raw NetworkX everywhere): extraction and retrieval talk
only to :class:`GraphStore`'s verbs (``add_node``, ``add_edge``, ``neighbors``,
``impacted_subgraph`` …). If the project ever outgrows NetworkX, a Neo4j-backed
``GraphStore`` can implement the same interface and nothing else changes. The
dormant ``neo4j_*`` keys in config.json exist for exactly that future.

Model
-----
- **Nodes** are typed and keyed by a stable string ``id`` (e.g. ``"TC-204"``,
  ``"cSAEGW-C"``). ``type`` is a label like ``TestCase`` / ``NetworkFunction``;
  arbitrary extra properties (``label``, ``status`` …) are allowed.
- **Edges** are directed and labelled by a ``rel`` (e.g. ``blocked_by``,
  ``fixed_in``, ``validates``). We use a MultiDiGraph so two nodes can be linked
  by more than one relationship. ``source_doc`` provenance can be attached.

Persistence
-----------
A plain JSON document ``{"nodes": [...], "edges": [...]}`` — human-readable,
diff-able, and safe to commit for the synthetic graph. ``save()``/``load()``
round-trip it. (NetworkX's own JSON helpers vary across versions, so we use an
explicit, stable schema instead.)
"""

import json
import logging
import os

import networkx as nx

try:
    from .config import get_graph_config
    from .logging_config import setup_logging
except ImportError:  # pragma: no cover
    from config import get_graph_config
    from logging_config import setup_logging

setup_logging()
logger = logging.getLogger("graph")


class GraphStore:
    """A typed, directed property graph backed by ``networkx.MultiDiGraph``.

    Parameters
    ----------
    path : str, optional
        Where ``save()``/``load()`` persist. Defaults to the configured
        ``graph_path`` from config.json.
    """

    def __init__(self, path=None):
        cfg = get_graph_config()
        self.path = path or cfg["path"]
        self.backend = cfg.get("backend", "networkx")
        self._g = nx.MultiDiGraph()

    # ------------------------------------------------------------------ mutate
    def add_node(self, node_id, node_type, **props):
        """Add or update a typed node. Idempotent on ``node_id`` (re-adding
        merges properties, so extraction can safely see the same entity in
        multiple documents)."""
        if not node_id:
            return None
        if self._g.has_node(node_id):
            self._g.nodes[node_id].setdefault("type", node_type)
            # Merge any new/non-empty properties without clobbering existing.
            for k, v in props.items():
                if v not in (None, "") and not self._g.nodes[node_id].get(k):
                    self._g.nodes[node_id][k] = v
        else:
            self._g.add_node(node_id, type=node_type, **props)
        return node_id

    def add_edge(self, src, rel, dst, **props):
        """Add a directed, labelled edge ``src --rel--> dst``.

        De-duplicated on the ``(src, rel, dst)`` triple so re-running extraction
        does not create parallel duplicate edges. Endpoints are auto-created as
        ``Unknown``-typed nodes if missing (extraction should normally create
        them explicitly first)."""
        if not src or not dst or not rel:
            return False
        if not self._g.has_node(src):
            self._g.add_node(src, type="Unknown")
        if not self._g.has_node(dst):
            self._g.add_node(dst, type="Unknown")
        # Use rel as the multigraph edge key -> at most one edge per (src,rel,dst).
        if self._g.has_edge(src, dst, key=rel):
            data = self._g[src][dst][rel]
            for k, v in props.items():
                if v not in (None, "") and not data.get(k):
                    data[k] = v
        else:
            self._g.add_edge(src, dst, key=rel, rel=rel, **props)
        return True

    # ------------------------------------------------------------------- query
    def has_node(self, node_id):
        return self._g.has_node(node_id)

    def node(self, node_id):
        """Return a node's property dict (including ``id``), or None."""
        if not self._g.has_node(node_id):
            return None
        data = dict(self._g.nodes[node_id])
        data["id"] = node_id
        return data

    def neighbors(self, node_id, rel=None, direction="both"):
        """Return neighbouring nodes as ``(neighbor_id, rel, direction)`` tuples.

        direction : "out" (edges from node), "in" (edges to node), or "both".
        rel : if given, only edges with this relationship label are returned.
        """
        if not self._g.has_node(node_id):
            return []
        out = []
        if direction in ("out", "both"):
            for _s, dst, key in self._g.out_edges(node_id, keys=True):
                if rel is None or key == rel:
                    out.append((dst, key, "out"))
        if direction in ("in", "both"):
            for src, _d, key in self._g.in_edges(node_id, keys=True):
                if rel is None or key == rel:
                    out.append((src, key, "in"))
        return out

    def edges(self):
        """Yield all edges as ``(src, rel, dst, props)`` tuples."""
        for src, dst, key, data in self._g.edges(keys=True, data=True):
            props = {k: v for k, v in data.items() if k != "rel"}
            yield (src, key, dst, props)

    def nodes(self):
        """Yield all nodes as ``(id, props)`` tuples."""
        for nid, data in self._g.nodes(data=True):
            yield (nid, dict(data))

    def impacted_subgraph(self, node_id, max_hops=3, rels=None):
        """Return the set of nodes reachable from ``node_id`` within ``max_hops``,
        plus the connecting edges — the "what is impacted / what does this depend
        on" traversal that plain RAG cannot do.

        Traversal follows edges in BOTH directions (impact flows up and down a
        dependency: a defect blocks a test, a test gates FOA, FOA precedes
        Production). Optionally restrict to a set of relationship labels.

        Returns
        -------
        dict with:
            center : node_id
            nodes  : list of node property dicts (incl. hop distance)
            edges  : list of (src, rel, dst) within the reached set
        """
        if not self._g.has_node(node_id):
            return {"center": node_id, "nodes": [], "edges": []}

        # BFS over the underlying undirected view, honouring the rel filter.
        dist = {node_id: 0}
        frontier = [node_id]
        while frontier:
            nxt = []
            for cur in frontier:
                if dist[cur] >= max_hops:
                    continue
                for neigh, rel, _dir in self.neighbors(cur, direction="both"):
                    if rels is not None and rel not in rels:
                        continue
                    if neigh not in dist:
                        dist[neigh] = dist[cur] + 1
                        nxt.append(neigh)
            frontier = nxt

        reached = set(dist)
        nodes = []
        for nid in reached:
            data = self.node(nid) or {"id": nid}
            data["hops"] = dist[nid]
            nodes.append(data)
        nodes.sort(key=lambda d: (d["hops"], d["id"]))

        edges = []
        for src, rel, dst, _p in self.edges():
            if src in reached and dst in reached:
                edges.append((src, rel, dst))
        return {"center": node_id, "nodes": nodes, "edges": edges}

    def stats(self):
        """Return ``{nodes, edges, node_types}`` for quick inspection/eval."""
        type_counts = {}
        for _nid, data in self._g.nodes(data=True):
            t = data.get("type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "nodes": self._g.number_of_nodes(),
            "edges": self._g.number_of_edges(),
            "node_types": type_counts,
        }

    # ------------------------------------------------------------- persistence
    def save(self, path=None):
        """Persist the graph to a stable JSON schema. Creates parent dirs."""
        target = path or self.path
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        doc = {
            "backend": self.backend,
            "nodes": [
                {"id": nid, **{k: v for k, v in data.items()}}
                for nid, data in self._g.nodes(data=True)
            ],
            "edges": [
                {"src": s, "rel": k, "dst": d,
                 **{kk: vv for kk, vv in data.items() if kk != "rel"}}
                for s, d, k, data in self._g.edges(keys=True, data=True)
            ],
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
        logger.info("graph saved: %s (%d nodes, %d edges)",
                    target, self._g.number_of_nodes(), self._g.number_of_edges())
        return target

    def load(self, path=None):
        """Load the graph from JSON, replacing current contents. Missing file
        yields an empty graph (so callers can lazily build-then-save)."""
        target = path or self.path
        self._g = nx.MultiDiGraph()
        try:
            with open(target, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError):
            logger.warning("graph file not found/invalid: %s (empty graph)", target)
            return self
        for n in doc.get("nodes", []):
            nid = n.get("id")
            if nid is None:
                continue
            props = {k: v for k, v in n.items() if k != "id"}
            ntype = props.pop("type", "Unknown")
            self._g.add_node(nid, type=ntype, **props)
        for e in doc.get("edges", []):
            s, rel, d = e.get("src"), e.get("rel"), e.get("dst")
            if not (s and rel and d):
                continue
            props = {k: v for k, v in e.items() if k not in ("src", "rel", "dst")}
            self._g.add_edge(s, d, key=rel, rel=rel, **props)
        logger.info("graph loaded: %s (%d nodes, %d edges)",
                    target, self._g.number_of_nodes(), self._g.number_of_edges())
        return self


def load_graph(path=None):
    """Convenience: construct a GraphStore and load it from disk."""
    return GraphStore(path=path).load(path)
