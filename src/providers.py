"""LLM provider abstraction for the Phase-1 RAG baseline.

Extracted from the parent ChatBOT project's ``chatBOT_engine.py`` provider
layer, decoupled from Streamlit (no ``st.cache_resource``, no streaming into a
UI). Each generator here is a plain function that returns the full answer text.

Providers:
  - "claude" : Anthropic Claude (needs ANTHROPIC_API_KEY in env/.env)
  - "qwen"   : local Qwen2.5-1.5B GGUF via llama-cpp-python (needs the .gguf)
  - "none"   : extractive — return the retrieved passages verbatim (no generation)

``resolve_provider()`` auto-falls back to "none" so answering never hard-fails
when a model/key is missing.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

try:
    from .config import VALID_PROVIDERS
    from .logging_config import setup_logging
    from .retrieval import SYNTH_SYSTEM, fence_context, build_context
except ImportError:  # pragma: no cover
    from config import VALID_PROVIDERS
    from logging_config import setup_logging
    from retrieval import SYNTH_SYSTEM, fence_context, build_context

setup_logging()
logger = logging.getLogger("providers")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
QWEN_GGUF_PATH = os.getenv(
    "QWEN_GGUF_PATH", os.path.join("models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")
)

# A simple module-level cache for the loaded Qwen model (replaces st.cache_resource).
_QWEN_LLM = None


def provider_available(name):
    """Return True if the given provider can actually run right now.

    - claude: an ANTHROPIC_API_KEY is set
    - qwen:   llama-cpp-python importable AND the GGUF model file exists
    - none:   always available (extractive needs no generation)
    """
    if name == "claude":
        return bool(os.getenv("ANTHROPIC_API_KEY"))
    if name == "qwen":
        if not os.path.isfile(QWEN_GGUF_PATH):
            return False
        try:
            import llama_cpp  # noqa: F401
            return True
        except ImportError:
            return False
    if name == "none":
        return True
    return False


def resolve_provider(requested):
    """Resolve the effective provider with auto-fallback so answering never
    breaks. Unavailable -> fall back to extractive ("none")."""
    if requested not in VALID_PROVIDERS:
        requested = "none"
    if provider_available(requested):
        return requested
    if requested != "none":
        logger.warning("provider '%s' unavailable; falling back to extractive", requested)
    return "none"


# ---------------------------------------------------------------------------
# Extractive (provider = "none")
# ---------------------------------------------------------------------------
def render_extractive(docs):
    """Return the retrieved passages verbatim, each under a [<file> §<section>]
    header. No LLM involved. Mirrors ChatBOT's extractive renderer."""
    import os as _os

    if not docs:
        return "I couldn't find anything relevant in the indexed documents."
    lines = [
        "_No answer-generation model is configured, so here are the most "
        "relevant passages from your documents:_\n"
    ]
    seen = set()
    for d in docs:
        fname = _os.path.basename(d.metadata.get("file_name", "unknown"))
        section = d.metadata.get("section", "?")
        key = (fname, section, d.page_content[:60])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"**[{fname} §{section}]**\n\n{d.page_content.strip()}\n")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude (provider = "claude")
# ---------------------------------------------------------------------------
def generate_claude(user_question, docs):
    """Synthesize a grounded, cited answer with Anthropic Claude. Returns the
    full answer text (non-streaming). On error returns an error string so the
    caller never hangs."""
    import anthropic

    context, _sources = build_context(docs)
    system_prompt = f"{SYNTH_SYSTEM}\n\nContext:\n{fence_context(context)}"
    try:
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        # NOTE: anthropic 1.11.0 messages.create() does not accept temperature.
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_question}],
        )
        parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
        return "".join(parts).strip() or "_(empty response)_"
    except Exception as ex:  # pragma: no cover - network/credential errors
        return f"_Error generating answer (Claude): {type(ex).__name__}: {ex}_"


# ---------------------------------------------------------------------------
# Qwen local SLM (provider = "qwen")
# ---------------------------------------------------------------------------
_QWEN_CITATION_REINFORCE = (
    "\n\nCITATION RULES (follow exactly):\n"
    "- After EVERY sentence or bullet, append the source marker in square "
    "brackets copied verbatim from the matching [Source: <filename> §<section>] "
    "line, written as [<filename> §<section>].\n"
)


def _qwen_llm():
    """Load the Qwen GGUF once per process (module-level cache)."""
    global _QWEN_LLM
    if _QWEN_LLM is None:
        from llama_cpp import Llama

        _QWEN_LLM = Llama(
            model_path=QWEN_GGUF_PATH,
            n_ctx=4096,
            n_threads=max(1, (os.cpu_count() or 2) - 1),
            verbose=False,
            chat_format="qwen",
        )
    return _QWEN_LLM


def generate_qwen(user_question, docs):
    """Synthesize a grounded answer with the local Qwen SLM. Returns full text."""
    context, _sources = build_context(docs)
    system_prompt = (
        f"{SYNTH_SYSTEM}{_QWEN_CITATION_REINFORCE}\n\nContext:\n{fence_context(context)}"
    )
    user_msg = (
        f"{user_question}\n\n"
        "Remember: end every sentence and bullet with its [<filename> §<section>] "
        "citation copied from the context's [Source: ...] markers."
    )
    try:
        llm = _qwen_llm()
        out = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1024,
            temperature=0.2,
        )
        return out["choices"][0]["message"]["content"].strip()
    except Exception as ex:  # pragma: no cover
        return f"_Error generating answer (Qwen): {type(ex).__name__}: {ex}_"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
def generate_answer(provider, user_question, docs):
    """Generate an answer with the resolved provider. ``provider`` should already
    be resolved via resolve_provider(). Returns the full answer text."""
    if provider == "claude":
        return generate_claude(user_question, docs)
    if provider == "qwen":
        return generate_qwen(user_question, docs)
    return render_extractive(docs)
