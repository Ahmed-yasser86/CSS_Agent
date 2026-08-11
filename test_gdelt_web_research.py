"""
Test GDELT web_research_tool_list to see what actual tools it returns.
This helps understand if GDELT has general-purpose web search tools.
"""
import asyncio
import os

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af0700335640e903ac13e941bbf')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_gdelt_web_research_tools():
    mcp_configs = {
        "gdelt-cloud": {
            "transport": "streamable_http",
            "url": "https://gdelt-cloud-mcp.fastmcp.app/mcp",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('GDELT_MCP_API_KEY')}"
            }
        }
    }
    
    print("Testing GDELT web_research_tool_list...")
    
    try:
        client = MultiServerMCPClient(mcp_configs)
        tools = await client.get_tools()
        
        # Find web_research tools
        web_research_tools = [t for t in tools if 'web_research' in t.name.lower()]
        print(f"\n=== Web Research Tools ===")
        for tool in web_research_tools:
            print(f"\n{tool.name}:")
            print(f"  Description: {tool.description[:500] if tool.description else 'None'}")
        
        # Find energy tools (to compare)
        energy_tools = [t for t in tools if 'energy' in t.name.lower()]
        print(f"\n=== Energy Tools ({len(energy_tools)}) ===")
        for tool in energy_tools[:5]:
            print(f"\n{tool.name}:")
            print(f"  Description: {tool.description[:300] if tool.description else 'None'}...")
        
        # Try to call web_research_tool_list to see what it returns
        print("\n\n=== Calling web_research_tool_list ===")
        
        # Find the tool
        list_tool = None
        for tool in tools:
            if tool.name == 'web_research_tool_list':
                list_tool = tool
                break
        
        if list_tool:
            print(f"Found {list_tool.name}")
            print(f"Description: {list_tool.description}")
            
            # Try to call it
            try:
                # Call without arguments first
                result = await list_tool.ainvoke({})
                print(f"\nResult from web_research_tool_list:")
                print(str(result)[:3000])
            except Exception as e:
                print(f"Error calling tool: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("web_research_tool_list not found!")
            print("\nAll tool names:")
            for t in tools:
                print(f"  - {t.name}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_gdelt_web_research_tools())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")