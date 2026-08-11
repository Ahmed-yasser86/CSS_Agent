"""Test GDELT wrapper tool expansion in detail."""
import asyncio
import os
import sys

sys.path.insert(0, r'c:\Users\DELL\graph-rag-agent\gpt-researcher')

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af0700335640e903ac13e941bbf')
os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-x5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_wrapper_expansion():
    """Test what happens when we call the wrapper tools."""
    print("=" * 60)
    print("Testing GDELT Wrapper Tool Expansion")
    print("=" * 60)
    
    mcp_configs = {
        "gdelt-cloud": {
            "transport": "streamable_http",
            "url": "https://gdelt-cloud-mcp.fastmcp.app/mcp",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('GDELT_MCP_API_KEY')}"
            }
        }
    }
    
    try:
        client = MultiServerMCPClient(mcp_configs)
        all_tools = await client.get_tools()
        print(f"Total tools: {len(all_tools)}")
        
        # Find wrapper tools
        list_tools = [t for t in all_tools if 'tool_list' in t.name.lower()]
        call_tools = [t for t in all_tools if 'tool_call' in t.name.lower()]
        
        print(f"\nList tools: {[t.name for t in list_tools]}")
        print(f"Call tools: {[t.name for t in call_tools]}")
        
        # Find web_research_tool_list specifically
        web_list_tool = next((t for t in all_tools if t.name == 'web_research_tool_list'), None)
        if web_list_tool:
            print(f"\nFound web_research_tool_list: {web_list_tool}")
            print(f"  Description: {web_list_tool.description}")
            
            # Try to call it
            print("\nCalling web_research_tool_list...")
            try:
                result = await web_list_tool.ainvoke({})
                print(f"Result type: {type(result)}")
                print(f"Result: {result}")
                
                # Check if it has the expected structure
                if isinstance(result, dict):
                    print(f"Result keys: {result.keys()}")
                    if 'structured_content' in result:
                        print(f"structured_content: {result['structured_content']}")
                    if 'content' in result:
                        print(f"content: {result['content']}")
            except Exception as e:
                print(f"Error calling tool: {e}")
                import traceback
                traceback.print_exc()
        
        # Test the _build_catalog_tools method
        print("\n" + "=" * 60)
        print("Testing _build_catalog_tools")
        print("=" * 60)
        
        from gpt_researcher.mcp.research import MCPResearchSkill
        
        class MockCfg:
            strategic_llm_model = "mistral-large-latest"
            strategic_llm_provider = "openai"
            llm_kwargs = {}
        
        research_skill = MCPResearchSkill(MockCfg(), None)
        
        # Test with just the list tool
        if web_list_tool:
            print("\nTesting expansion with just list tool...")
            expanded = await research_skill._build_catalog_tools([web_list_tool])
            print(f"Expanded tools: {[t.name for t in expanded]}")
        
        # Test with both list and call tools
        gdelt_list = next((t for t in all_tools if t.name == 'gdelt_cloud_tool_list'), None)
        gdelt_call = next((t for t in all_tools if t.name == 'gdelt_cloud_tool_call'), None)
        web_list = next((t for t in all_tools if t.name == 'web_research_tool_list'), None)
        web_call = next((t for t in all_tools if t.name == 'web_research_tool_call'), None)
        
        if gdelt_list and gdelt_call:
            print("\nTesting expansion with both list and call tools...")
            expanded = await research_skill._build_catalog_tools([gdelt_list, gdelt_call])
            print(f"Expanded GDELT tools: {[t.name for t in expanded]}")
        
        if web_list and web_call:
            print("\nTesting expansion with web_research list and call tools...")
            expanded = await research_skill._build_catalog_tools([web_list, web_call])
            print(f"Expanded web_research tools: {[t.name for t in expanded]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_wrapper_expansion())