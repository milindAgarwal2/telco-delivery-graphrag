# Contributing

Thanks for your interest! This is a small **learning / portfolio** project that
explores GraphRAG over a synthetic 5G/telecom delivery corpus. Contributions,
ideas, and questions are welcome.

## Golden rule: synthetic data only

This repository is intended to be **shareable**. Only synthetic / sanitized data
belongs here (everything under `data/synthetic/` is invented).

- **Never commit real customer, subscriber, node, or confidential data** —
  no production logs, identifiers (IMSIs), credentials, PCAPs, node names, or
  control-plane addresses.
- Put any real experiments under `data/private/` — it is **git-ignored**.
- Secrets (API keys) live in `.env` (git-ignored). Non-secret config lives in
  `config.json`.

If you spot anything sensitive in a PR, flag it before merging.

## Development setup

```bash
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m src.ingest     # embed data/synthetic/ into Chroma
./.venv/bin/python -m src.extract    # build the knowledge graph
```

## Running the app

```bash
./.venv/bin/streamlit run app.py     # browser GUI
# or the CLI:
./.venv/bin/python -m src.rag --graph "your question"
```

## Tests

```bash
./.venv/bin/pip install pytest
./.venv/bin/pytest -q
```

The smoke tests check that the modules import, the graph builds from the
synthetic corpus, and core traversal works. Please keep them passing, and add a
test when you add a feature or fix a bug.

## Pull requests

- Keep changes focused and described clearly (what + why).
- Match the existing style (clear docstrings, small functions, no new heavy
  dependencies without reason).
- Don't commit generated artifacts (`chroma_*/`, `lib/`, `.venv/`) — they are
  git-ignored.

## License

By contributing you agree your contributions are licensed under the project's
[MIT License](LICENSE).
