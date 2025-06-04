import asyncio
from ev_bot.ai_agent import AiAgent

async def main():
    agent = AiAgent()
    PROMPT = "Find me best travel ideas from my current location."
    ideas = await agent.run_agent(PROMPT)
    print(ideas)

if __name__ == "__main__":
    asyncio.run(main())