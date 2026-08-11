"""Check SocialCrawl and GDELT tool descriptions"""
import asyncio
import os

os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-x5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')
os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af07005a6e3c6a3bfea628d2f2a3f')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test():
    mcp_configs = {
        'socialcrawl': {
            'transport': 'streamable_http',
            'url': 'https://mcp.socialcrawl.dev/mcp',
            'headers': {'x-api-key': os.environ.get('SOCIALCRAWL_MCP_API_KEY')}
        },
        'gdelt-cloud': {
            'transport': 'streamable_http',
            'url': 'https://gdelt-cloud-mcp.fastmcp.app/mcp',
            'headers': {'Authorization': f"Bearer {os.environ.get('GDELT_MCP_API_KEY')}"}
        }
    }
    client = MultiServerMCPClient(mcp_configs)
    tools = await client.get_tools()
    print(f'Total tools: {len(tools)}')
    for t in tools:
        desc = t.description or "No description"
        print(f'  - {t.name}: {desc[:150]}...')

asyncio.run(test())