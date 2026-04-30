# RK Gen AI Chatbot — Python SDK

Drop-in client for the RK Gen AI Chatbot backend. Use it from any Python project
(InternOps, Apogee, AI Compliance Copilot, your portfolio backend, etc.) to add
a fast, grounded chatbot about Rajat Kumar.

## Install

```bash
# from this folder
pip install -e .

# or directly from the repo
pip install -e ../sdk
```

The SDK depends only on `httpx`. The backend must be running (default
`http://localhost:5000`). Start it from `../rk-core/`:

```bash
cd ../rk-core && python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

## Quick start

```python
from rkgenaichatbot import Chatbot

bot = Chatbot()                              # uses http://localhost:5000
print(bot.health())

reply = bot.chat("What are Rajat's main skills?")
print(reply["reply"])
print("sources:", reply["sources"])
```

## Streaming

```python
for token in bot.stream("Tell me about InternOps"):
    print(token, end="", flush=True)
print()
```

## Sessions

```python
bot = Chatbot()
sid = bot.create_session()
bot.chat("Hello", session_id=sid)
bot.chat("What did he build at UptoSkills?", session_id=sid)
```

## Async

```python
import asyncio
from rkgenaichatbot import AsyncChatbot

async def main():
    bot = AsyncChatbot()
    reply = await bot.chat("Summarise the AI Compliance Copilot project")
    print(reply["reply"])

asyncio.run(main())
```

## Configuration

```python
bot = Chatbot(
    api_url="https://my-chatbot.example.com",  # custom backend URL
    timeout=60.0,                                # request timeout (seconds)
)
```

## API

- `Chatbot.health() -> dict` — backend health check
- `Chatbot.create_session() -> str` — create a new session, returns session_id
- `Chatbot.chat(message, session_id=None) -> dict` — sync chat, returns full reply
- `Chatbot.stream(message, session_id=None) -> Iterator[str]` — streaming tokens
- `AsyncChatbot` — same API, fully async
