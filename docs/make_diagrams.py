"""Generate article diagrams into docs/images/.

Produces three PNGs used by docs/article.md:
  - knowledge-graph.png  : the real graph rendered from graph/telco_graph.json
  - architecture.png     : the two-layer (vector RAG + knowledge graph) flow
  - rag-vs-graphrag.png  : what plain RAG vs graph-augmented retrieval can answer

Run:  ./.venv/bin/python docs/make_diagrams.py
This is a one-off authoring helper, not part of the app.
"""

import json
import os

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "docs", "images")
GRAPH_JSON = os.path.join(ROOT, "graph", "telco_graph.json")

os.makedirs(IMG_DIR, exist_ok=True)

# Node-type palette (matches the GUI's _TYPE_COLORS).
TYPE_COLORS = {
    "TestCase": "#4C9AFF",
    "Defect": "#FF5630",
    "Alarm": "#FF8B00",
    "Document": "#6554C0",
    "ReleaseNote": "#8B5CF6",
    "NetworkFunction": "#36B37E",
    "SoftwareVersion": "#00B8D9",
    "Environment": "#FFC400",
    "Interface": "#8777D9",
    "Release": "#172B4D",
    "Unknown": "#97A0AF",
}


def make_knowledge_graph():
    """Render the actual persisted knowledge graph, colored by node type."""
    with open(GRAPH_JSON, "r", encoding="utf-8") as f:
        doc = json.load(f)

    g = nx.MultiDiGraph()
    node_type = {}
    for n in doc["nodes"]:
        nid = n["id"]
        node_type[nid] = n.get("type", "Unknown")
        g.add_node(nid)
    for e in doc["edges"]:
        g.add_edge(e["src"], e["dst"], rel=e["rel"])

    fig, ax = plt.subplots(figsize=(15, 11))
    pos = nx.spring_layout(g, k=0.9, iterations=200, seed=7)

    colors = [TYPE_COLORS.get(node_type.get(n, "Unknown"), "#97A0AF") for n in g.nodes()]
    nx.draw_networkx_nodes(g, pos, node_color=colors, node_size=900,
                           edgecolors="#172B4D", linewidths=0.8, ax=ax)
    nx.draw_networkx_edges(g, pos, edge_color="#B3BAC5", arrows=True,
                           arrowsize=12, width=1.0, alpha=0.7,
                           connectionstyle="arc3,rad=0.06", ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=7.5, font_color="#091E42", ax=ax)

    # Edge relationship labels (thinned to avoid clutter).
    edge_labels = {}
    for u, v, data in g.edges(data=True):
        edge_labels.setdefault((u, v), data.get("rel", ""))
    nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=5.5,
                                 font_color="#5E6C84", bbox=dict(boxstyle="round,pad=0.1",
                                 fc="white", ec="none", alpha=0.6), ax=ax)

    present = sorted({node_type[n] for n in g.nodes()})
    handles = [mpatches.Patch(color=TYPE_COLORS.get(t, "#97A0AF"), label=t) for t in present]
    ax.legend(handles=handles, loc="upper left", fontsize=9, frameon=True,
              title="Node type", title_fontsize=10)

    ax.set_title("The delivery knowledge graph "
                 f"({g.number_of_nodes()} nodes, {g.number_of_edges()} edges)",
                 fontsize=14, fontweight="bold", color="#172B4D")
    ax.axis("off")
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "knowledge-graph.png")
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", out)


def _box(ax, x, y, w, h, text, fc, ec="#172B4D", fontsize=10, fontcolor="#172B4D"):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.02,rounding_size=0.06",
                 fc=fc, ec=ec, linewidth=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=fontcolor, wrap=True, fontweight="medium")


def _arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#5E6C84", lw=1.8))


def make_architecture():
    """Two-layer architecture: ingest -> (vector store + graph) -> hybrid answer."""
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)

    _box(ax, 0.3, 2.9, 2.0, 1.2, "Synthetic\ndelivery docs\n(release notes, MOP,\nCIQ, tests, defects…)",
         "#DFE1E6", fontsize=8.5)

    _box(ax, 3.1, 4.5, 2.4, 1.0, "Ingestion\n(chunk + embed)", "#B3D4FF", fontsize=9)
    _box(ax, 3.1, 1.3, 2.4, 1.0, "Extraction\n(entities + relations)", "#C0E6D6", fontsize=9)

    _box(ax, 6.2, 4.5, 2.4, 1.0, "Vector store\n(Chroma + embeddings)", "#4C9AFF", fontsize=9, fontcolor="white")
    _box(ax, 6.2, 1.3, 2.4, 1.0, "Knowledge graph\n(NetworkX, file)", "#36B37E", fontsize=9, fontcolor="white")

    _box(ax, 9.2, 2.9, 2.5, 1.2, "Hybrid answer\nvector passages +\ngraph traversal\n+ citations", "#6554C0", fontsize=8.5, fontcolor="white")

    # arrows
    _arrow(ax, 2.3, 3.7, 3.1, 5.0)
    _arrow(ax, 2.3, 3.3, 3.1, 1.8)
    _arrow(ax, 5.5, 5.0, 6.2, 5.0)
    _arrow(ax, 5.5, 1.8, 6.2, 1.8)
    _arrow(ax, 8.6, 5.0, 9.6, 4.1)
    _arrow(ax, 8.6, 1.8, 9.6, 2.9)

    ax.text(6, 6.5, "Two-layer GraphRAG architecture", ha="center",
            fontsize=15, fontweight="bold", color="#172B4D")
    ax.text(6, 0.4, "A question retrieves similar passages (top) AND traverses the "
            "graph from mentioned entities (bottom); both feed the cited answer.",
            ha="center", fontsize=9, color="#5E6C84", style="italic")
    ax.axis("off")
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "architecture.png")
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", out)


def make_rag_vs_graphrag():
    """Side-by-side: what plain RAG returns vs what graph traversal assembles."""
    fig, (axl, axr) = plt.subplots(1, 2, figsize=(13, 6))

    for ax in (axl, axr):
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis("off")

    # Left: plain RAG — isolated passages
    axl.text(5, 9.3, "Plain RAG", ha="center", fontsize=14, fontweight="bold", color="#172B4D")
    axl.text(5, 8.5, '"what does this document say?"', ha="center", fontsize=9.5,
             style="italic", color="#5E6C84")
    for i, (yy, t) in enumerate([(6.6, "passage A"), (4.8, "passage B"), (3.0, "passage C")]):
        _box(axl, 3.2, yy, 3.6, 1.1, t, "#B3D4FF", fontsize=9)
    axl.text(5, 1.4, "Relevant but disconnected.\nYou join the dots yourself.",
             ha="center", fontsize=9.5, color="#DE350B")

    # Right: GraphRAG — connected chain
    axr.text(5, 9.3, "GraphRAG", ha="center", fontsize=14, fontweight="bold", color="#172B4D")
    axr.text(5, 8.5, '"what\'s impacted, and what blocks go-live?"', ha="center",
             fontsize=9.5, style="italic", color="#5E6C84")
    chain = [(7.4, "TC-204\n(test)", "#4C9AFF"), (5.9, "DEF-1203\n(defect)", "#FF5630"),
             (4.4, "ALM-SX-DOWN\n(alarm)", "#FF8B00"), (2.9, "go-live → production\n(gated)", "#FFC400")]
    for yy, t, c in chain:
        fc_text = "white" if c in ("#4C9AFF", "#FF5630") else "#172B4D"
        _box(axr, 3.2, yy, 3.6, 1.0, t, c, fontsize=8.5, fontcolor=fc_text)
    for i in range(len(chain) - 1):
        _arrow(axr, 5.0, chain[i][0], 5.0, chain[i + 1][0] + 1.0)
    axr.text(5, 1.4, "A traversable dependency chain —\ncited at every step.",
             ha="center", fontsize=9.5, color="#00875A")

    fig.suptitle("Retrieval vs. relationship reasoning", fontsize=15,
                 fontweight="bold", color="#172B4D", y=0.99)
    fig.tight_layout()
    out = os.path.join(IMG_DIR, "rag-vs-graphrag.png")
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    make_knowledge_graph()
    make_architecture()
    make_rag_vs_graphrag()
    print("done")
