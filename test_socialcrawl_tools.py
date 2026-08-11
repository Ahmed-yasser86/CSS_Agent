"""Test SocialCrawl MCP tools to understand their structure."""
import asyncio
import os

os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_socialcrawl_tools():
    mcp_configs = {
        "socialcrawl": {
            "transport": "streamable_http",
            "url": "https://mcp.socialcrawl.dev/mcp",
            "headers": {
                "x-api-key": os.environ.get('SOCIALCRAWL_MCP_API_KEY')
            }
        }
    }
    
    print("Testing SocialCrawl MCP tools...")
    
    try:
        client = MultiServerMCPClient(mcp_configs)
        tools = await client.get_tools()
        
        print(f"Total SocialCrawl tools: {len(tools)}")
        
        print("\n=== ALL SocialCrawl TOOLS ===")
        for tool in tools:
            desc = getattr(tool, 'description', 'No description') or 'No description'
            print(f"\n{tool.name}:")
            print(f"  Description: {desc[:300]}...")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_socialcrawl_tools())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")