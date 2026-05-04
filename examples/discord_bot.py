"""
RK Gen AI Chatbot — Discord bot integration example.

Drops the chatbot into any Discord server. The bot:
  - Listens for @mentions or DMs
  - Streams the reply token-by-token back to the channel
  - Falls back to the KB-only response if the LLM is down

Requirements:
  pip install discord.py
  DISCORD_BOT_TOKEN=... python examples/discord_bot.py
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, "sdk")
sys.path.insert(0, "rk-core")

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("Install discord.py first: pip install discord.py", file=sys.stderr)
    raise

from rkgenaichatbot import AsyncChatbot  # noqa: E402

API = os.getenv("API", "http://localhost:5000")
TOKEN = os.environ["DISCORD_BOT_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
chatbot = AsyncChatbot(api_url=API)


@bot.event
async def on_ready():
    print(f"[bot] logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if bot.user not in message.mentions and not isinstance(message.channel, discord.DMChannel):
        return

    prompt = message.content.replace(f"@{bot.user.display_name}", "").strip()
    if not prompt:
        return

    async with message.channel.typing():
        try:
            chunks: list[str] = []
            async for token in chatbot.stream(prompt):
                chunks.append(token)
            reply = "".join(chunks).strip() or "(no response)"
        except Exception as e:
            reply = f"Sorry, the chatbot is unavailable: `{e}`"

    # Discord has a 2000-char limit — chunk if needed
    for i in range(0, len(reply), 1900):
        await message.channel.send(reply[i : i + 1900])


bot.run(TOKEN)
