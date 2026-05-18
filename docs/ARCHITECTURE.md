# Architecture

## Overview

RK Gen AI Chatbot is a production-grade RAG-powered chatbot built around three
pillars: a parallel LLM race with always-on fallback, a personal knowledge base
that grounds responses in real artifacts, and a flexible integration surface
(REST + SSE + WebSocket + SDK + widget).

## High-level flow

```
client ──▶ FastAPI (main.py)
            │
            ├─▶ Guardrails (PII, length, rate)
            │
            ├─▶ RAG retriever (FAISS over personal KB)
            │
            ├─▶ LangGraph agent (state + nodes + tools)
            │       │
            │       └─▶ LLM race (parallel providers)
            │             │
            │             └─▶ Fallback chain on failure
            │
            └─▶ Stream response (SSE / WebSocket)
```

## Modules

| Module | Role |
| --- | --- |
| `rk-core/main.py` | FastAPI app, routes, lifecycle |
| `rk-core/agent/` | LangGraph agent (state, nodes, prompts, graph) |
| `rk-core/llm/` | Provider clients + parallel race |
| `rk-core/retriever/` | FAISS vector store + chunking |
| `rk-core/fallback.py` | Always-on fallback chain |
| `rk-core/guardrails.py` | Input/output filtering |
| `rk-core/knowledge_base/` | Markdown KB + GitHub ingest |
| `sdk/` | Python SDK |
| `widget/` | Embeddable JS widget |
| `examples/` | Integration recipes |
