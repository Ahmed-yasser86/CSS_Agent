"""Quick test to verify MCP tools are called in real workflow."""
import asyncio
import os
import sys

sys.path.insert(0, r'c:\Users\DELL\graph-rag-agent\gpt-researcher')

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af0700335640e903ac13e941bbf')
os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')

from gpt_researcher import GPTResearcher
from gpt_researcher.config import ResearchConfig

async def test():
    print("Running subject intelligence agent...")
    r = GPTResearcher()
    config = ResearchConfig(
        query="What are the latest AI news?",
        report_type="subject_intelligence",
        agent_type="subject"
    )
    await r.run(config)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test())