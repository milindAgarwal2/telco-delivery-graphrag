"""telco-delivery-graphrag — Phase 1 RAG baseline (src package).

Modules:
  config          — non-secret config (config.json) + secret split (.env)
  logging_config  — shared logging setup
  ingest          — vectorstore, chunking, content-hash upsert, doc ingesters
  retrieval       — MMR retrieval, confidence probe, context builder, injection fence
  providers       — LLM provider abstraction (claude | qwen | none)
  rag             — UI-free answer function tying retrieval + providers together
"""
