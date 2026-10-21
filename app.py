"""Streamlit GUI for the DMC Delivery GraphRAG Copilot.

A browser-based front-end so people can ask questions and explore the knowledge
graph WITHOUT touching Python or the CLI. It is a thin presentation layer over
the existing, UI-free core:

  - Q&A tab           -> src.rag.answer_question() (vector RAG + optional graph)
  - Impact Explorer   -> src.graph.GraphStore.impacted_subgraph() (dependency/
                         impact traversal — the thing plain RAG can't do)

Nothing in src/ is changed; this module only reads from it. Run with:

    ./.venv/bin/streamlit run app.py

Then open the URL Streamlit prints (default http://localhost:8501).
"""

import os
import sys
import tempfile

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

# Ensure the repo root is importable when Streamlit runs this file directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import VALID_PROVIDERS, get_graph_config  # noqa: E402
from src.graph import load_graph  # noqa: E402
from src.rag import answer_question  # noqa: E402


# Stable colour per node type so the diagram is readable at a glance.
_TYPE_COLORS = {
    "TestCase": "#4C9AFF",        # blue
    "Defect": "#FF5630",          # red
    "Alarm": "#FF8B00",           # orange
    "Document": "#6554C0",        # purple
    "ReleaseNote": "#8B5CF6",     # light purple (per-CNF release notes)
    "NetworkFunction": "#36B37E",  # green
    "SoftwareVersion": "#00B8D9",  # teal
    "Environment": "#FFC400",     # amber
    "Interface": "#8777D9",       # violet
    "Release": "#172B4D",         # dark navy
    "Unknown": "#97A0AF",         # grey
}


def _subgraph_html(sub, center_id, types):
    """Render an impacted_subgraph dict as an interactive pyvis network and
    return the HTML string. Nodes are coloured by type; the center entity is
    enlarged and outlined; edges are labelled with the relationship."""
    net = Network(
        height="520px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#172B4D",
        notebook=False,
    )
    net.barnes_hut(gravity=-8000, spring_length=160, spring_strength=0.02)

    reached = {n["id"] for n in sub["nodes"]}
    for n in sub["nodes"]:
        nid = n["id"]
        ntype = n.get("type", types.get(nid, "Unknown"))
        is_center = nid == center_id
        net.add_node(
            nid,
            label=nid,
            title=f"{nid}\nType: {ntype}\nHops from center: {n.get('hops', 0)}",
            color={
                "background": _TYPE_COLORS.get(ntype, _TYPE_COLORS["Unknown"]),
                "border": "#172B4D" if is_center else _TYPE_COLORS.get(ntype, "#97A0AF"),
            },
            size=34 if is_center else 20,
            borderWidth=4 if is_center else 1,
            shape="dot",
        )
    for s, rel, d in sub["edges"]:
        if s in reached and d in reached:
            net.add_edge(s, d, label=rel, title=rel, arrowStrikethrough=False,
                         color="#97A0AF", font={"size": 11, "color": "#505F79"})

    # pyvis writes to a file; read it back as a string to embed inline.
    with tempfile.NamedTemporaryFile(
        mode="r", suffix=".html", delete=False, encoding="utf-8"
    ) as tmp:
        path = tmp.name
    net.save_graph(path)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    try:
        os.remove(path)
    except OSError:
        pass
    return html


# ---------------------------------------------------------------------------
# Cached resources (load the graph once per session, not per interaction).
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _graph():
    """Load the persisted knowledge graph once and reuse it."""
    return load_graph()


@st.cache_data(show_spinner=False)
def _node_index():
    """Return (sorted node ids, {id: type}) for the entity picker.

    Cached on data because the graph file is static during a session. Falls back
    gracefully to an empty index if the graph hasn't been built yet.
    """
    g = _graph()
    pairs = sorted(g.nodes())  # [(id, {type,...}), ...]
    ids = [nid for nid, _ in pairs]
    types = {nid: data.get("type", "Unknown") for nid, data in pairs}
    return ids, types


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DMC Delivery GraphRAG Copilot",
    page_icon="🕸️",
    layout="wide",
)

st.title("🕸️ DMC Delivery GraphRAG Copilot")
st.caption(
    "Ask questions over the (synthetic) 5G/telecom delivery corpus, or explore "
    "the knowledge graph's dependency/impact relationships. Synthetic data only."
)

# Sidebar: global controls shared by both tabs.
with st.sidebar:
    st.header("Settings")
    provider = st.selectbox(
        "Answer provider",
        options=list(VALID_PROVIDERS),
        index=list(VALID_PROVIDERS).index("none") if "none" in VALID_PROVIDERS else 0,
        help=(
            "'none' = extractive (shows passages, no LLM; always works). "
            "'claude' needs ANTHROPIC_API_KEY in .env. "
            "'qwen' needs a local GGUF model. Unavailable choices auto-fall back "
            "to extractive."
        ),
    )
    default_graph_on = bool(get_graph_config().get("enabled"))
    use_graph = st.toggle(
        "Use knowledge graph",
        value=default_graph_on,
        help=(
            "When on, the answer is augmented with relationship context "
            "traversed from the graph (for dependency/impact questions)."
        ),
    )
    g_stats = _graph().stats()
    st.divider()
    st.caption(
        f"Graph: **{g_stats['nodes']} nodes**, **{g_stats['edges']} edges**"
        if g_stats["nodes"]
        else "Graph not built yet — run `python -m src.extract`."
    )


qa_tab, impact_tab = st.tabs(["💬 Ask a question", "🔎 Impact Explorer"])


# ---------------------------------------------------------------------------
# Tab 1 — Q&A
# ---------------------------------------------------------------------------
with qa_tab:
    st.subheader("Ask a question")
    st.write(
        "Try a dependency/impact question to see the graph help, e.g. "
        "_“Which test cases and documents are impacted by the cSAEGW-C upgrade, "
        "and what blocks FOA readiness?”_"
    )

    with st.form("qa_form"):
        question = st.text_area(
            "Your question",
            value="Which test cases and documents are impacted by the "
            "cSAEGW-C upgrade, and what blocks FOA readiness?",
            height=90,
        )
        submitted = st.form_submit_button("Ask", type="primary")

    if submitted and question.strip():
        with st.spinner("Retrieving and answering…"):
            result = answer_question(
                question.strip(), provider=provider, use_graph=use_graph
            )

        # --- Metrics row ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Provider (effective)", result["provider"])
        conf = result["confidence"]
        c2.metric("Confidence", f"{conf:.3f}" if conf is not None else "n/a")
        c3.metric(
            "Graph", "on" if result.get("graph_used") else "off",
            delta=(", ".join(result.get("graph_anchors") or [])) or None,
            delta_color="off",
        )

        if result["low_confidence"]:
            st.warning(
                f"Low confidence (best match {conf:.3f} below threshold) — "
                "there may be limited matching content for this question."
            )

        # --- Answer ---
        st.markdown("### Answer")
        st.markdown(result["answer"])

        # --- Graph anchors / relationships (when used) ---
        if result.get("graph_used") and result.get("graph_anchors"):
            with st.expander(
                f"🕸️ Knowledge-graph anchors: {', '.join(result['graph_anchors'])}",
                expanded=True,
            ):
                st.caption(
                    "The graph was traversed from these entities to add "
                    "relationship context to the answer above."
                )

        # --- Sources ---
        if result["sources"]:
            with st.expander(f"📄 Sources ({len(result['sources'])})", expanded=False):
                for fname, section in result["sources"]:
                    base = os.path.basename(fname or "unknown")
                    st.markdown(f"- **{base}** &nbsp;§ {section}")


# ---------------------------------------------------------------------------
# Tab 2 — Impact Explorer
# ---------------------------------------------------------------------------
with impact_tab:
    st.subheader("Impact Explorer")
    st.write(
        "Pick an entity and see what it connects to across the delivery "
        "lifecycle — the dependency/impact traversal that plain document search "
        "cannot do."
    )

    ids, types = _node_index()
    if not ids:
        st.info("The graph is empty. Build it first: `python -m src.extract`.")
    else:
        colA, colB = st.columns([3, 1])
        with colA:
            # Default to the anchor-demo entity if present.
            default_idx = ids.index("TC-204") if "TC-204" in ids else 0
            entity = st.selectbox(
                "Entity",
                options=ids,
                index=default_idx,
                format_func=lambda nid: f"{nid}  ·  {types.get(nid, '?')}",
            )
        with colB:
            max_hops = st.slider("Max hops", min_value=1, max_value=4, value=2)

        sub = _graph().impacted_subgraph(entity, max_hops=max_hops)
        nodes = [n for n in sub["nodes"] if n.get("hops", 0) > 0]
        edges = sub["edges"]

        m1, m2 = st.columns(2)
        m1.metric("Connected entities", len(nodes))
        m2.metric("Relationships", len(edges))

        # --- Interactive graph (the readable, visual view) ---
        if sub["edges"]:
            # Colour legend for the node types actually present.
            present_types = sorted(
                {n.get("type", "Unknown") for n in sub["nodes"]}
            )
            legend = "  ".join(
                f"<span style='color:{_TYPE_COLORS.get(t, '#97A0AF')};"
                f"font-weight:600'>&#9679; {t}</span>"
                for t in present_types
            )
            st.markdown(
                f"**Legend:** {legend}  &nbsp;|&nbsp; "
                "the outlined/larger node is the selected entity. "
                "Drag nodes to rearrange; hover for details.",
                unsafe_allow_html=True,
            )
            html = _subgraph_html(sub, entity, types)
            components.html(html, height=540, scrolling=False)
        else:
            st.caption("No relationships within this hop distance to visualize.")

        # --- Textual detail (kept, but collapsed) ---
        with st.expander("📋 Detail: entities by hop + relationship list", expanded=False):
            st.markdown("**Impacted / related entities**")
            by_hop = {}
            for n in nodes:
                by_hop.setdefault(n["hops"], []).append(n)
            if not by_hop:
                st.caption("No connected entities within this hop distance.")
            for hop in sorted(by_hop):
                label = f"{hop} hop" + ("s" if hop > 1 else "")
                chips = "  ".join(
                    f"`{n['id']}` ({n.get('type', '?')})" for n in by_hop[hop]
                )
                st.markdown(f"**{label} away:** {chips}")

            st.markdown("**Relationships**")
            if edges:
                st.dataframe(
                    {
                        "From": [s for s, _r, _d in edges],
                        "Relationship": [r for _s, r, _d in edges],
                        "To": [d for _s, _r, d in edges],
                    },
                    width="stretch",
                    hide_index=True,
                )
            else:
                st.caption("No relationships within this hop distance.")
