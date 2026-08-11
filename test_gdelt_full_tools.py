import asyncio
import os

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af07005a6e3c6a3bfea628d2f2a3f')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_gdelt_full_tools():
    mcp_configs = {
        "gdelt-cloud": {
            "transport": "streamable_http",
            "url": "https://gdelt-cloud-mcp.fastmcp.app/mcp",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('GDELT_MCP_API_KEY')}"
            }
        }
    }
    
    print("Testing GDELT MCP - Full Tool List...")
    
    try:
        client = MultiServerMCPClient(mcp_configs)
        tools = await client.get_tools()
        
        print(f"Total GDELT tools: {len(tools)}")
        
        # Show ALL tool names and descriptions
        print("\n=== ALL GDELT TOOLS ===")
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
    result = asyncio.run(test_gdelt_full_tools())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")