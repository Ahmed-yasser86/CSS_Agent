import asyncio
import os
import json

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af07005a6e3c6a3bfea628d2f2a3f')
os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-x5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_tool_selection():
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
    
    print("Testing MCP tool selection...")
    
    try:
        client = MultiServerMCPClient(mcp_configs)
        tools = await client.get_tools()
        
        print(f"Total tools: {len(tools)}")
        
        # Filter out tool_list and tool_get tools (like the MCPToolSelector does)
        filtered_tools = [
            tool for tool in tools
            if not any(
                fragment in str(getattr(tool, "name", "") or "").lower()
                for fragment in [
                    "tool_list",
                    "tool_catalog",
                    "tool_get",
                    "tool_call",
                    "list_tools",
                    "list_tool",
                    "get_tool",
                    "call_tool",
                    "invoke_tool",
                ]
            )
        ]
        
        print(f"Filtered tools (excluding tool_list/tool_get): {len(filtered_tools)}")
        
        # Show all filtered tool names
        print("\nFiltered tool names:")
        for tool in filtered_tools:
            desc = getattr(tool, 'description', 'No description') or 'No description'
            print(f"  - {tool.name}: {desc[:100]}...")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_tool_selection())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")