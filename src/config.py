"""Shared application configuration (tracked in git, non-secret).

Config lives in ``config.json`` at the repo root so every entrypoint (ingestion,
retrieval, the RAG answerer, and later the graph layer) reads a single source of
truth. Secrets (e.g. ANTHROPIC_API_KEY, NEO4J_PASSWORD) stay in ``.env`` — this
file and config.json are only for NON-secret settings such as which LLM provider
to use, the low-confidence threshold, logging, and non-secret graph/Neo4j knobs.

This module is ported from the parent ``ChatBOT`` project's ``config.py`` and
keeps the same proven pattern: ``load_config()``/``save_config()`` merge over
``DEFAULTS`` and run ``_normalize_*`` validators so a hand-edited config.json can
never crash the app. The ChatBOT-specific Streamlit/widget UI keys were dropped
(this project is UI-free for now); graph/Neo4j keys were added for Phase 2.
"""

import json
import os

# config.json lives at the REPO ROOT (one level up from this src/ package), so
# all tools and both phases share one file.
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)

# Allowed LLM providers for answering.
#   "claude"     -> Anthropic Claude (needs ANTHROPIC_API_KEY)
#   "qwen"       -> local Qwen2.5-1.5B GGUF via llama-cpp-python (needs the .gguf)
#   "none"       -> extractive: show retrieved passages verbatim (no generation)
VALID_PROVIDERS = ("claude", "qwen", "none")

# Confidence signal. If the single best retrieval relevance score for a query
# falls below this floor, the answerer flags "low confidence" (non-blocking).
# The value is a cosine *relevance* score in [0, 1] (higher = more similar); it
# is model- and corpus-dependent and should be retuned via an eval harness.
LOW_CONFIDENCE_MIN = 0.0
LOW_CONFIDENCE_MAX = 1.0

VALID_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

DEFAULTS = {
    # --- Retrieval / answering (Phase 1 RAG baseline) ---
    "llm_provider": "none",
    "low_confidence_threshold": 0.63,
    # --- Logging ---
    "log_level": "INFO",
    "log_file": "",            # "" -> console/stderr only; a path -> also append there
    # --- Vector store (Chroma) ---
    # Kept non-secret and configurable so ingestion and retrieval always agree.
    "chroma_collection": "telco_delivery",
    "chroma_persist_dir": "./chroma_telco",
    "embedding_model": "BAAI/bge-small-en-v1.5",
    # --- Graph (Phase 2) ---
    # The graph layer uses an in-process NetworkX store persisted to a single
    # JSON file (no server, no Docker). "graph_enabled" lets Phase 1 run with
    # the graph layer entirely off. "graph_backend" selects the implementation
    # ("networkx" today); the DORMANT neo4j_* keys below remain so a
    # server-backed backend could be added later WITHOUT a config migration —
    # the Neo4j PASSWORD would then come from .env (NEO4J_PASSWORD), never here.
    "graph_enabled": False,
    "graph_backend": "networkx",
    "graph_path": "./graph/telco_graph.json",
    "neo4j_uri": "bolt://localhost:7687",
    "neo4j_user": "neo4j",
    "neo4j_database": "neo4j",
}

# Supported graph backends. "networkx" = in-process, file-persisted (current).
# "neo4j" is reserved for a future server-backed implementation.
VALID_GRAPH_BACKENDS = ("networkx", "neo4j")


def _clamp_threshold(value, fallback=0.63):
    """Coerce ``value`` to a float in [LOW_CONFIDENCE_MIN, LOW_CONFIDENCE_MAX].

    A missing/non-numeric value falls back to ``fallback`` so a hand-edited
    config.json can never crash the app or produce a nonsensical cutoff.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if v < LOW_CONFIDENCE_MIN:
        return LOW_CONFIDENCE_MIN
    if v > LOW_CONFIDENCE_MAX:
        return LOW_CONFIDENCE_MAX
    return v


def _normalize_log_level(value, fallback="INFO"):
    """Coerce ``value`` to a valid log-level name (uppercased). Bad values fall
    back so a hand-edited config.json can't break logging setup."""
    if not isinstance(value, str):
        return fallback
    v = value.strip().upper()
    return v if v in VALID_LOG_LEVELS else fallback


def _normalize_str(cfg, key):
    """Ensure a config string key is a non-empty string, else restore default."""
    v = cfg.get(key)
    if not isinstance(v, str) or not v.strip():
        cfg[key] = DEFAULTS[key]
    else:
        cfg[key] = v.strip()


def _normalize_graph(cfg):
    """Validate graph keys in-place: enabled is a real bool; backend is a known
    value (else default); graph_path and neo4j_* are non-empty strings (else
    default). The Neo4j password is NOT here (it's a secret from .env)."""
    cfg["graph_enabled"] = bool(cfg.get("graph_enabled", DEFAULTS["graph_enabled"]))
    backend = cfg.get("graph_backend")
    if not isinstance(backend, str) or backend.strip().lower() not in VALID_GRAPH_BACKENDS:
        cfg["graph_backend"] = DEFAULTS["graph_backend"]
    else:
        cfg["graph_backend"] = backend.strip().lower()
    for key in ("graph_path", "neo4j_uri", "neo4j_user", "neo4j_database"):
        _normalize_str(cfg, key)


def load_config():
    """Return the config dict, merged over defaults. Never raises: a missing or
    malformed file yields the defaults so the app always runs.
    """
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
    except (OSError, ValueError):
        pass
    # Normalize the provider to a known value.
    if cfg.get("llm_provider") not in VALID_PROVIDERS:
        cfg["llm_provider"] = DEFAULTS["llm_provider"]
    # Clamp the confidence threshold into [0, 1].
    cfg["low_confidence_threshold"] = _clamp_threshold(
        cfg.get("low_confidence_threshold"), DEFAULTS["low_confidence_threshold"]
    )
    # Normalize logging settings.
    cfg["log_level"] = _normalize_log_level(cfg.get("log_level"), DEFAULTS["log_level"])
    if not isinstance(cfg.get("log_file"), str):
        cfg["log_file"] = DEFAULTS["log_file"]
    # Vector-store knobs: non-empty strings.
    for key in ("chroma_collection", "chroma_persist_dir", "embedding_model"):
        _normalize_str(cfg, key)
    # Graph / Neo4j knobs.
    _normalize_graph(cfg)
    return cfg


def save_config(updates):
    """Merge ``updates`` into the current config and write config.json.

    Returns the written (normalized) config dict. Re-runs the same validators as
    load_config() so what we persist is always well-formed.
    """
    cfg = load_config()
    for k, v in (updates or {}).items():
        cfg[k] = v
    if cfg.get("llm_provider") not in VALID_PROVIDERS:
        cfg["llm_provider"] = DEFAULTS["llm_provider"]
    cfg["low_confidence_threshold"] = _clamp_threshold(
        cfg.get("low_confidence_threshold"), DEFAULTS["low_confidence_threshold"]
    )
    cfg["log_level"] = _normalize_log_level(cfg.get("log_level"), DEFAULTS["log_level"])
    if not isinstance(cfg.get("log_file"), str):
        cfg["log_file"] = DEFAULTS["log_file"]
    for key in ("chroma_collection", "chroma_persist_dir", "embedding_model"):
        _normalize_str(cfg, key)
    _normalize_graph(cfg)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return cfg


# --- Convenience accessors (read fresh each call; config.json is the source) ---

def get_llm_provider():
    """Return the configured provider string."""
    return load_config()["llm_provider"]


def get_low_confidence_threshold():
    """Return the configured low-confidence threshold (float in [0, 1])."""
    return load_config()["low_confidence_threshold"]


def get_log_level():
    """Return the configured log level name (from config.json)."""
    return load_config()["log_level"]


def get_log_file():
    """Return the configured log-file path ("" = console only)."""
    return load_config()["log_file"]


def get_vectorstore_config():
    """Return the vector-store settings (collection, persist dir, embed model)."""
    cfg = load_config()
    return {
        "collection": cfg["chroma_collection"],
        "persist_dir": cfg["chroma_persist_dir"],
        "embedding_model": cfg["embedding_model"],
    }


def get_graph_config():
    """Return the NON-secret graph settings. For the NetworkX backend only
    ``enabled``/``backend``/``path`` are used; the neo4j_* keys are dormant and
    returned for a future server-backed backend (whose password would come from
    the environment, .env NEO4J_PASSWORD, never from here)."""
    cfg = load_config()
    return {
        "enabled": cfg["graph_enabled"],
        "backend": cfg["graph_backend"],
        "path": cfg["graph_path"],
        "uri": cfg["neo4j_uri"],
        "user": cfg["neo4j_user"],
        "database": cfg["neo4j_database"],
    }
