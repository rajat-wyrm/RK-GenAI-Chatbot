"""
main.py — RK Gen AI Chatbot backend.

FastAPI app exposing:
  - Chat (sync, full agentic LangGraph pipeline, parallel-provider LLM racing)
  - Chat stream (SSE, token-by-token)
  - WebSocket chat
  - Integration endpoint (simple, for SDK / embed widget)
  - AI bootstrap endpoints (frontend compat)
  - Health / session / suggest / capabilities

The retrieval layer uses Hugging Face Inference API embeddings with a
keyword fallback. The LLM layer races Groq, Gemini, DeepSeek, and OpenAI
in parallel and returns the fastest successful response.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Optional
from collections import defaultdict

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()
from logging_config import setup_logging  # noqa: E402
from guardrails import validate_input, detect_language  # noqa: E402
from cache import create_cache  # noqa: E402
from database import SessionLocal, ChatSession  # noqa: E402
from retriever.vectorstore import build_vectorstore  # noqa: E402
from agent.nodes import set_dependencies  # noqa: E402
from agent.graph import build_graph  # noqa: E402
from llm import aget_llm_response, stream_chat  # noqa: E402
from llm import providers as llm_providers  # noqa: E402

setup_logging()
logger = logging.getLogger("skillnova.main")

APP_NAME = os.getenv("APP_NAME", "RK Gen AI Chatbot")

# ---------------------------------------------------------------------------
# Robustness: rate limiting, request IDs, uptime
# ---------------------------------------------------------------------------
_startup_time = time.time()
_rate_buckets: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))


def _check_rate_limit(client_ip: str) -> bool:
    """Sliding-window per-IP rate limiter. Returns True if allowed."""
    now = time.time()
    bucket = [t for t in _rate_buckets.get(client_ip, []) if now - t < 60]
    if len(bucket) >= RATE_LIMIT_PER_MIN:
        _rate_buckets[client_ip] = bucket
        return False
    bucket.append(now)
    _rate_buckets[client_ip] = bucket
    return True


def rate_limit_dep(request: Request):
    """FastAPI dependency: 429s the client if they exceed the per-minute limit."""
    ip = (request.client.host if request.client else "unknown")
    if not _check_rate_limit(ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
            headers={"Retry-After": "60"},
        )


# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
agent_graph = None
vectorstore = None
_response_cache = None
_executor = None
_agent_semaphore = asyncio.Semaphore(12)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_chat_history(session_id: str) -> str:
    db = None
    try:
        db = SessionLocal()
        chats = (
            db.query(ChatSession)
            .filter_by(session_id=session_id)
            .order_by("turn_number")
            .limit(10)
            .all()
        )
        return "\n".join(f"User: {c.user_message}\nBot: {c.bot_response}" for c in chats)
    except Exception as e:
        logger.error(f"[DB READ ERROR] {e}")
        return ""
    finally:
        if db:
            db.close()


def save_chat_turn(session_id: str, user_msg: str, bot_msg: str):
    db = None
    try:
        db = SessionLocal()
        turn = db.query(ChatSession).filter_by(session_id=session_id).count() + 1
        db.add(ChatSession(
            session_id=session_id, user_message=user_msg,
            bot_response=bot_msg, turn_number=turn,
        ))
        db.commit()
    except Exception as e:
        logger.error(f"[DB WRITE ERROR] {e}")
    finally:
        if db:
            db.close()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
def init_pipeline():
    global agent_graph, vectorstore, _response_cache, _executor
    from concurrent.futures import ThreadPoolExecutor

    logger.info(f"[INIT] Starting {APP_NAME} pipeline...")
    vectorstore = build_vectorstore()
    set_dependencies(vectorstore)
    agent_graph = build_graph()
    _response_cache, _ = create_cache(redis_enabled=False)
    _executor = ThreadPoolExecutor(max_workers=12)
    enabled = llm_providers.enabled_providers()
    logger.info(f"[INIT] LLM providers enabled: {enabled}")
    logger.info(f"[INIT] Pipeline ready (providers={enabled})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pipeline()
    yield
    await llm_providers.aclose()


app = FastAPI(title=APP_NAME, version="2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a short X-Request-ID to every request for log/debug correlation."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    role: str = "Intern"


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    confidence: float = 0.0
    sources: List[str] = []
    error: bool = False
    provider: Optional[str] = None
    latency_ms: Optional[float] = None


# ---------------------------------------------------------------------------
# Core agentic chat (sync)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _split_into_stream_chunks(text: str, chunk_size: int = 8) -> list[str]:
    """Split text into small chunks for streaming-render feel."""
    words = text.split(" ")
    chunks: list[str] = []
    buf: list[str] = []
    for w in words:
        buf.append(w)
        if len(buf) >= chunk_size:
            chunks.append(" ".join(buf) + " ")
            buf = []
    if buf:
        chunks.append(" ".join(buf))
    return chunks


def _format_context(docs) -> str:
    if not docs:
        return ""
    parts = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "unknown")
        parts.append(f"[{i}] (source: {src})\n{d.page_content}")
    return "\n\n".join(parts)


def _build_prompt(question: str, context: str, history: str, language: str) -> str:
    return f"""You are the personal AI assistant for Rajat Kumar (also known as RK).
You answer questions about Rajat's background, skills, projects, experience, and achievements.
You can be conversational and friendly, but always stay grounded in the provided context.

Language: {language}

Conversation history:
{history or "(no prior history)"}

Reference context from Rajat's knowledge base:
{context or "(no relevant context found)"}

User question: {question}

Instructions:
- Answer based ONLY on the reference context and conversation history.
- If the answer is not in the context, say you don't have that information and suggest contacting Rajat directly.
- Be concise but informative. Use bullet points when listing items.
- Refer to Rajat in the third person unless the user is Rajat himself.

Answer:"""


async def _run_agent_chat(req: ChatRequest) -> ChatResponse:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    session_id = req.session_id or str(uuid.uuid4())

    try:
        start = time.time()

        valid, msg = validate_input(req.message)
        if not valid:
            return ChatResponse(reply=msg, session_id=session_id, error=True)

        lang = detect_language(req.message) or "en"

        cache_key = f"{req.message}:{lang}"
        if _response_cache:
            try:
                cached = _response_cache.get(cache_key)
                if cached:
                    cached["session_id"] = session_id
                    return ChatResponse(**cached)
            except Exception:
                logger.warning("[CACHE READ FAILED]")

        history = get_chat_history(session_id)

        # Retrieve context
        docs = vectorstore.similarity_search(req.message.strip(), k=5) if vectorstore else []
        context = _format_context(docs)
        prompt = _build_prompt(req.message.strip(), context, history, lang)

        # LLM race (with KB fallback if all providers fail)
        try:
            provider, text, latency = await asyncio.wait_for(
                aget_llm_response(prompt, question=req.message, vectorstore=vectorstore),
                timeout=25,
            )
        except asyncio.TimeoutError:
            # Hard timeout — still try the KB fallback
            from fallback import generate
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fb = ex.submit(generate, req.message, vectorstore).result()
            return ChatResponse(
                reply=fb["reply"],
                session_id=session_id,
                confidence=0.5,
                sources=fb.get("sources", []),
                error=False,
                provider="kb-fallback-timeout",
                latency_ms=0,
            )

        # Collect sources
        sources: List[str] = []
        for d in docs:
            src = d.metadata.get("source") if hasattr(d, "metadata") else None
            if src and src not in sources:
                sources.append(src)

        response_data = {
            "reply": text.strip(),
            "session_id": session_id,
            "confidence": 0.9 if docs else 0.6,
            "sources": sources,
            "error": False,
            "provider": provider,
            "latency_ms": round(latency, 1),
        }

        if _response_cache:
            try:
                _response_cache.set(cache_key, {**response_data, "session_id": session_id}, ttl=300)
            except Exception:
                pass

        save_chat_turn(session_id, req.message, response_data["reply"])
        logger.info(f"[CHAT] {int((time.time()-start)*1000)}ms provider={provider}")
        return ChatResponse(**response_data)

    except HTTPException:
        raise
    except Exception:
        logger.exception("[FINAL CHAT ERROR]")
        return ChatResponse(
            reply="I hit an unexpected error. Please try again.",
            session_id=session_id, error=True,
        )


# ---------------------------------------------------------------------------
# SSE streaming chat
# ---------------------------------------------------------------------------
async def _sse_stream(req: ChatRequest) -> AsyncIterator[bytes]:
    if not req.message.strip():
        yield f"data: {json.dumps({'type': 'error', 'message': 'Empty message'})}\n\n".encode()
        return

    session_id = req.session_id or str(uuid.uuid4())
    yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n".encode()

    try:
        valid, msg = validate_input(req.message)
        if not valid:
            yield f"data: {json.dumps({'type': 'token', 'content': msg, 'error': True})}\n\n".encode()
            yield f"data: {json.dumps({'type': 'done'})}\n\n".encode()
            return

        lang = detect_language(req.message) or "en"
        history = get_chat_history(session_id)

        # Yield retrieval results first (so UI can show "thinking")
        docs = vectorstore.similarity_search(req.message.strip(), k=5) if vectorstore else []
        context = _format_context(docs)
        sources: List[str] = []
        for d in docs:
            src = d.metadata.get("source") if hasattr(d, "metadata") else None
            if src and src not in sources:
                sources.append(src)
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n".encode()

        prompt = _build_prompt(req.message.strip(), context, history, lang)

        # Stream tokens, then fall back to KB-only response if streaming fails
        full_reply_parts: list[str] = []
        provider_name = ""
        try:
            async for provider, token in stream_chat(prompt):
                provider_name = provider
                full_reply_parts.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token, 'provider': provider})}\n\n".encode()
        except Exception as stream_err:
            logger.warning(f"[STREAM] streaming failed: {stream_err} — using KB fallback")
            from fallback import generate
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fb = ex.submit(generate, req.message, vectorstore).result()
            for chunk in _split_into_stream_chunks(fb["reply"]):
                yield f"data: {json.dumps({'type': 'token', 'content': chunk, 'provider': 'kb-fallback'})}\n\n".encode()
            full_reply_parts = [fb["reply"]]
            provider_name = "kb-fallback"

        full_reply = "".join(full_reply_parts).strip()
        save_chat_turn(session_id, req.message, full_reply)
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'provider': provider_name, 'sources': sources})}\n\n".encode()
    except Exception as e:
        logger.exception("[STREAM ERROR]")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n".encode()
        yield f"data: {json.dumps({'type': 'done'})}\n\n".encode()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "running", "service": APP_NAME}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": "2.0",
        "uptime_s": round(time.time() - _startup_time, 1),
        "components": {
            "vectorstore": vectorstore is not None,
            "agent_graph": agent_graph is not None,
            "cache": _response_cache is not None,
            "llm_providers": llm_providers.enabled_providers(),
        },
        "kb_chunks": (
            len(vectorstore.primary.matrix) if vectorstore and getattr(vectorstore, "primary", None) is not None
            else (len(vectorstore.fallback.docs) if vectorstore and getattr(vectorstore, "fallback", None) is not None else 0)
        ),
    }


@app.get("/api/session")
def create_session():
    return {"session_id": str(uuid.uuid4())}


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit_dep)])
async def chat(req: ChatRequest):
    return await _run_agent_chat(req)


@app.post("/api/ai/chat", response_model=ChatResponse, dependencies=[Depends(rate_limit_dep)])
async def ai_chat(req: ChatRequest):
    return await _run_agent_chat(req)


@app.post("/api/chat/stream", dependencies=[Depends(rate_limit_dep)])
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        _sse_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# Frontend bootstrap endpoints
_SUGGESTIONS = [
    "What are Rajat's main technical skills?",
    "Tell me about InternOps",
    "What did he do as Senior Team Lead at UptoSkills?",
    "Describe the AI Compliance Copilot project",
    "What is his educational background?",
    "Tell me about his NCC leadership experience",
    "What certifications does he have?",
    "How can I contact Rajat?",
]

_CAPABILITIES = [
    "Answers questions about Rajat's skills, experience, and projects",
    "Grounded in his personal knowledge base (resume + GitHub)",
    "Streams responses token-by-token for instant feedback",
    "Cites the source document for every answer",
    "Supports English (and detects Hindi)",
    "Integrates into any project via REST, WebSocket, or SDK",
]


@app.get("/api/ai/suggestions")
def ai_suggestions():
    return {"data": _SUGGESTIONS}


@app.get("/api/ai/capabilities")
def ai_capabilities():
    return {"data": _CAPABILITIES}


@app.get("/api/ai/welcome-message")
def ai_welcome_message():
    return {
        "message": (
            "Hi! I'm Rajat's personal AI assistant. "
            "Ask me about his skills, projects at UptoSkills, InternOps, "
            "the AI Compliance Copilot, Apogee, certifications, or how to reach him."
        )
    }


# Integration endpoint for SDK / embed widget (simple, CORS-friendly)
@app.post("/api/integrate/chat", dependencies=[Depends(rate_limit_dep)])
async def integrate_chat(req: ChatRequest):
    return await _run_agent_chat(req)


@app.post("/api/integrate/stream", dependencies=[Depends(rate_limit_dep)])
async def integrate_stream(req: ChatRequest):
    return StreamingResponse(
        _sse_stream(req),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# WebSocket
@app.websocket("/api/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            msg = data.get("message", "")
            session_id = data.get("session_id") or str(uuid.uuid4())
            if not msg.strip():
                await ws.send_json({"type": "error", "message": "Empty message"})
                continue
            valid, err = validate_input(msg)
            if not valid:
                await ws.send_json({"type": "error", "message": err})
                continue
            lang = detect_language(msg) or "en"
            history = ""
            docs = vectorstore.similarity_search(msg.strip(), k=5) if vectorstore else []
            context = _format_context(docs)
            prompt = _build_prompt(msg.strip(), context, history, lang)
            await ws.send_json({"type": "start", "session_id": session_id})
            full = []
            async for provider, token in stream_chat(prompt):
                full.append(token)
                await ws.send_json({"type": "token", "content": token, "provider": provider})
            reply = "".join(full).strip()
            save_chat_turn(session_id, msg, reply)
            await ws.send_json({"type": "done", "session_id": session_id})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("[WS ERROR]")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "5000")), reload=False)
