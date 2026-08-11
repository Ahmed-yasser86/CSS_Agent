import asyncio
import os

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af07005a6e3c6a3bfea628d2f2a3f')
os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-x5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_connection():
    mcp_configs = {
        "gdelt-cloud": {
            "transport": "streamable_http",
            "url": "https://gdelt-cloud-mcp.fastmcp.app/mcp",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('GDELT_MCP_API_KEY')}"
            }
        },
        "socialcrawl": {
            "transport": "streamable_http",
            "url": "https://mcp.socialcrawl.dev/mcp",
            "headers": {
                "x-api-key": os.environ.get('SOCIALCRAWL_MCP_API_KEY')
            }
        }
    }
    
    print("Testing MCP connection...")
    print(f"GDELT URL: {mcp_configs['gdelt-cloud']['url']}")
    print(f"SocialCrawl URL: {mcp_configs['socialcrawl']['url']}")
    
    try:
        client = MultiServerMCPClient(mcp_configs)
        print("Client created successfully")
        
        # Try to get tools
        print("Fetching tools...")
        tools = await client.get_tools()
        print(f"Number of tools: {len(tools)}")
        for tool in tools[:10]:  # Show first 10 tools
            print(f"  - {tool.name}: {tool.description[:100] if tool.description else 'No description'}...")
        if len(tools) > 10:
            print(f"  ... and {len(tools) - 10} more tools")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_connection())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")