# RK Gen AI Chatbot

> Your personal, always-on AI assistant. Drop into any project, run anywhere, answer in milliseconds.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)]()
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)]()

A self-hosted, ultra-fast chatbot that knows everything about **Rajat Kumar** — skills, projects (InternOps, Apogee, AI Compliance Copilot, BrainBox AI, Quintern, and more), experience at UptoSkills, NCC leadership, education, certifications, and contact info. Built with FastAPI, LangGraph, parallel multi-provider LLM racing, SSE streaming, and a smart KB-only fallback so the bot is **never unavailable**.

---

## ⚡ Features

| | |
|---|---|
| **Always-on** | KB-only fallback fires when every LLM is down. The bot is *never* unreachable. |
| **Parallel LLM racing** | Groq, Gemini, DeepSeek, OpenAI fired in parallel — first success wins. Fastest wins. |
| **Token streaming** | Server-Sent Events + Groq streaming → first token in ~300-500ms. |
| **Smart RAG** | Intent-aware retrieval with source boosting — `skills.md` wins for skills queries, InternOps repo wins for InternOps queries. |
| **WebSocket** | Real-time bidirectional chat at `/api/ws/chat`. |
| **Python SDK** | `pip install -e ./sdk` → `from rkgenaichatbot import Chatbot` |
| **JS embed widget** | Single 10 KB file — `<script src="rk-chatbot-widget.js"></script>` |
| **Discord / Slack** | Drop-in bot examples in `examples/`. |
| **Docker** | `docker compose up` and you're live. |
| **Personal KB** | 7 hand-written docs + 13 GitHub repos auto-ingested. |

---

## 🚀 Quick Start

```bash
# 1. Clone and configure
git clone <repo>
cd "RK Gen AI Chatbot"
cp rk-core/.env.example rk-core/.env
# Edit rk-core/.env and add at least one of:
#   GROQ_API_KEY=...   (free at https://console.groq.com/keys — fastest)
#   GEMINI_API_KEY=...
#   OPENAI_API_KEY=...
#   DEEPSEEK_API_KEY=...

# 2. Run
cd rk-core
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

Open http://localhost:5000 for the chat UI, or call the API:

```bash
curl -X POST http://localhost:5000/api/integrate/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about InternOps"}'
```

Or with Docker:

```bash
docker compose up
```

---

## 🧩 Integration (drop into any project)

### Python SDK

```bash
pip install -e ./sdk
```

```python
from rkgenaichatbot import Chatbot
bot = Chatbot()                              # defaults to http://localhost:5000

# Sync
print(bot.chat("What are Rajat's skills?")["reply"])

# Streaming
for token in bot.stream("Tell me about InternOps"):
    print(token, end="", flush=True)
```

### Embed widget (any website)

```html
<script src="https://your-host/widget/rk-chatbot-widget.js"
        data-api-url="https://chatbot.example.com"
        data-title="Ask about Rajat"
        data-theme="dark"
        data-accent="#ff6d34"></script>
```

### REST API

```bash
POST /api/integrate/chat       # simple, no auth
POST /api/chat                  # full agentic pipeline
POST /api/chat/stream           # SSE token streaming
WS   /api/ws/chat               # real-time bidirectional
```

See `examples/` for cURL, Python, JavaScript, Discord, and Slack integrations.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vite + React)                 │
│              AIAssistant.jsx  •  SSE consumer               │
└────────────────────────┬────────────────────────────────────┘
                         │ fetch / SSE / WS
┌────────────────────────▼────────────────────────────────────┐
│                FastAPI  (rk-core/main.py)                   │
│  /api/chat  /api/chat/stream  /api/ws/chat  /api/integrate │
└──────┬─────────────────────────┬────────────────────────┬───┘
       │                         │                        │
┌──────▼──────┐         ┌────────▼────────┐      ┌────────▼────────┐
│   Retriever │         │  Parallel LLM    │      │    Fallback     │
│  (RAG)      │         │     Race         │      │ (KB-only,       │
│ • keyword   │         │  ┌──────────┐    │      │  always-on)     │
│ • embeddings│         │  │ groq     │    │      │                 │
│   (HF)      │         │  │ gemini   │    │      │  Intent detect  │
│ • source    │         │  │ deepseek │    │      │  Source boost   │
│   boost     │         │  │ openai   │    │      │  Smart format   │
│ • intent    │         │  └──────────┘    │      │                 │
│   force     │         │  first wins      │      │                 │
└─────────────┘         └──────────────────┘      └─────────────────┘
```

### Speed stack
- Pre-computed keyword index → sub-10ms retrieval
- httpx async with connection pooling → no TCP handshake overhead
- Groq streaming → first token in ~300ms
- Parallel LLM racing → fastest provider wins, no sequential fallback
- Response caching for repeated queries
- Streaming SSE to the browser → instant perceived response

### Reliability stack
- `race_chat` tries every enabled provider, falls back to KB-only on total failure
- `stream_chat` catches streaming errors and falls back to KB-only
- Timeout (25s) → KB-only response
- KB-only fallback works with **zero LLM keys** — the bot is always reachable

---

## 📁 Project layout

```
RK Gen AI Chatbot/
├── rk-core/                # The chatbot engine
│   ├── main.py             # FastAPI app, all routes
│   ├── fallback.py         # KB-only response generator (always-on)
│   ├── embeddings.py       # HF Inference API client
│   ├── retriever/          # Keyword + embedding vectorstore
│   ├── llm/                # Providers + parallel race
│   ├── agent/              # LangGraph agentic graph
│   ├── knowledge_base/     # Personal KB (resume + 13 GitHub repos)
│   ├── data/               # Cached embeddings (gitignored)
│   ├── scripts/            # ingest_github.py, build_embeddings.py
│   ├── .env                # API keys (gitignored)
│   └── requirements.txt
├── frontend/               # React + Vite chat UI
│   └── src/AIAssistant.jsx # SSE streaming chat
├── sdk/                    # pip-installable Python SDK
│   └── rkgenaichatbot/
├── widget/                 # Single-file JS embed widget
│   └── rk-chatbot-widget.js
├── examples/               # cURL, Python, JS, Discord, Slack
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Groq API key (free, fastest) |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `DEEPSEEK_API_KEY` | — | DeepSeek API key |
| `HUGGINGFACE_API_KEY` | — | Enables semantic embeddings (optional) |
| `GITHUB_TOKEN` | — | Auto-ingest GitHub repos into KB |
| `GITHUB_USERNAME` | — | Your GitHub username |
| `LLM_PROVIDERS` | `groq,gemini,deepseek,openai` | Race order |
| `LLM_RACE_TIMEOUT_S` | `20` | Race timeout per request |
| `PORT` | `5000` | HTTP port |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🔌 API Reference

### `POST /api/chat`
Full agentic pipeline (guardrails → RAG → parallel LLM race → fallback).
```json
{ "message": "Tell me about InternOps", "session_id": "optional-uuid" }
```

### `POST /api/chat/stream`
Server-Sent Events streaming. Each event is `data: {json}\n\n`:
- `{type: "start", session_id}` — stream begins
- `{type: "sources", sources: [...]}` — retrieved KB files
- `{type: "token", content, provider}` — each streamed token
- `{type: "done", session_id, provider}` — stream ends
- `{type: "error", message}` — on failure (fallback still runs)

### `POST /api/integrate/chat`
Same as `/api/chat` but intended for SDKs and the embed widget (CORS-friendly).

### `WS /api/ws/chat`
Bidirectional WebSocket. Send `{message, session_id}`, receive token events.

### `GET /api/health`
```json
{"status":"ok","service":"RK Gen AI Chatbot","llm_providers":["groq"]}
```

### `GET /api/session` → `{session_id}`

### Frontend bootstrap (used by `AIAssistant.jsx`)
- `GET /api/ai/suggestions`
- `GET /api/ai/capabilities`
- `GET /api/ai/welcome-message`

---

## 🛡 Security

- `.env` is gitignored — never commit API keys
- All endpoints support CORS for browser access
- Input guardrails block jailbreak prompts, SQL injection, oversized input
- No auth required for the integration endpoints (designed for public chatbots about a public persona); add a reverse proxy for production

---

## 🔄 Updating the knowledge base

```bash
# Re-fetch GitHub data
cd rk-core
python scripts/ingest_github.py

# Re-build embeddings (requires HUGGINGFACE_API_KEY)
python scripts/build_embeddings.py

# Edit the .md files in knowledge_base/ directly — they're picked up on restart
```

---

## 📜 License

MIT

---

## ⚠️ About the API keys in `rk-core/.env`

The API keys currently in `rk-core/.env` were shared in a development chat and are **publicly exposed**. They will be rotated. For production deployment, generate fresh keys and store them in a secrets manager (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, etc.) — never in plaintext.
