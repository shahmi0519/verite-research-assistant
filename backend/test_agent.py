import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from agent import VeriteAgent

agent = VeriteAgent()

async def test():
    tests = [
        "Hello!",
        "What does Verité say about labour rights?",
        "Who won the IPL 2024?",
        "What is forced labour?",
    ]
    for msg in tests:
        print(f"\n👤 User: {msg}")
        result = await agent.chat(msg)
        print(f"🤖 Vera: {result['reply'][:200]}")
        print(f"   Search used: {result['search_used']} | Sources: {len(result['sources'])}")

asyncio.run(test())