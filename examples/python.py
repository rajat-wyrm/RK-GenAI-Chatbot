"""
RK Gen AI Chatbot — Python integration example.

Shows four ways to call the chatbot from any Python project:
  1. Sync chat via the bundled SDK
  2. Streaming chat (generator of tokens)
  3. Raw HTTP via requests (no SDK)
  4. Async streaming with AsyncChatbot

Run from the project root:
    pip install -e ./sdk
    python examples/python.py
"""
from __future__ import annotations

import json
import sys
import urllib.request

# Make the SDK importable when running from the project root
sys.path.insert(0, "sdk")
from rkgenaichatbot import Chatbot, AsyncChatbot  # noqa: E402

API = "http://localhost:5000"


def section(title: str) -> None:
    print(f"\n── {title} ──")


# ── 1. SDK: sync chat ─────────────────────────────────────────────
section("1. SDK sync chat")
bot = Chatbot(api_url=API)
reply = bot.chat("What are Rajat's main technical skills?")
print(f"provider : {reply.get('provider')}")
print(f"sources  : {reply.get('sources', [])[:3]}")
print(f"reply    : {reply['reply'][:200]}...")


# ── 2. SDK: streaming chat ────────────────────────────────────────
section("2. SDK streaming chat")
print("stream  : ", end="", flush=True)
for token in bot.stream("Tell me about the AI Compliance Copilot"):
    print(token, end="", flush=True)
print()


# ── 3. Raw HTTP via urllib (zero deps) ────────────────────────────
section("3. Raw HTTP / no SDK")
req = urllib.request.Request(
    f"{API}/api/integrate/chat",
    data=json.dumps({"message": "How can I contact Rajat?"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read())
print(f"reply   : {data['reply'][:200]}...")


# ── 4. Async streaming ─────────────────────────────────────────────
section("4. Async streaming")
import asyncio


async def main():
    bot = AsyncChatbot(api_url=API)
    print("async   : ", end="", flush=True)
    async for token in bot.stream("What did he do as Senior TL?"):
        print(token, end="", flush=True)
    print()
    await bot.aclose()


asyncio.run(main())
