"""
RK Gen AI Chatbot — Slack webhook integration example.

Listens on /rk-chat (POST) and forwards the message to the chatbot, then
posts the streaming reply back to the Slack channel via the incoming webhook.

Requirements:
  pip install fastapi uvicorn httpx
  SLACK_WEBHOOK_URL=... python examples/slack_webhook.py
"""
from __future__ import annotations

import os
import sys
import httpx
from fastapi import FastAPI, Request

sys.path.insert(0, "sdk")
from rkgenaichatbot import Chatbot  # noqa: E402

API = os.getenv("API", "http://localhost:5000")
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK_URL"]
CHATBOT = Chatbot(api_url=API)

app = FastAPI()


@app.post("/rk-chat")
async def rk_chat(req: Request):
    payload = await req.json()
    text = payload.get("text", "").strip()
    if not text:
        return {"ok": False, "error": "empty message"}
    reply = CHATBOT.chat(text).get("reply", "(no response)")
    async with httpx.AsyncClient() as c:
        await c.post(SLACK_WEBHOOK, json={"text": reply})
    return {"ok": True, "reply": reply[:200] + "..."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8765")))
