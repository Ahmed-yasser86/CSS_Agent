"""Test the full MCP flow with tool selector and wrapper tool expansion."""
import asyncio
import os
import sys

# Add gpt-researcher to path
sys.path.insert(0, r'c:\Users\DELL\graph-rag-agent\gpt-researcher')

os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_66698ca037010a17f281572b6507876106c81af0700335640e903ac13e941bbf')
os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_WayMlH-5aXtMxcHUTtYMl_3LiUTEaTpQAffLUhZATI')

from langchain_mcp_adapters.client import MultiServerMCPClient

async def test_mcp_tool_selection_flow():
    """Test that tool selector can work with GDELT wrapper tools."""
    print("=" * 60)
    print("Testing MCP Tool Selection Flow")
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
        # Step 1: Get all tools
        print("\n1. Getting all MCP tools...")
        client = MultiServerMCPClient(mcp_configs)
        all_tools = await client.get_tools()
        print(f"   Total tools: {len(all_tools)}")
        
        # Step 2: Show tool names
        print("\n2. Tool names:")
        for tool in all_tools[:10]:
            print(f"   - {tool.name}")
        if len(all_tools) > 10:
            print(f"   ... and {len(all_tools) - 10} more")
        
        # Step 3: Check wrapper tools
        wrapper_tools = [t for t in all_tools if any(
            fragment in t.name.lower() for fragment in 
            ['tool_list', 'tool_get', 'tool_call']
        )]
        print(f"\n3. Wrapper tools found: {len(wrapper_tools)}")
        for wt in wrapper_tools[:5]:
            print(f"   - {wt.name}")
        
        # Step 4: Test tool selector
        print("\n4. Testing tool selector...")
        from gpt_researcher.mcp.tool_selector import MCPToolSelector
        
        class MockCfg:
            strategic_llm_model = "mistral-large-latest"
            strategic_llm_provider = "openai"
            llm_kwargs = {}
        
        selector = MCPToolSelector(MockCfg(), None)
        
        # Test with a query about web research
        query = "What are the latest news about AI?"
        selected = await selector.select_relevant_tools(query, all_tools, max_tools=3)
        
        print(f"   Query: {query}")
        print(f"   Selected tools: {[t.name for t in selected]}")
        
        # Check if wrapper tools are selected
        wrapper_selected = [t for t in selected if any(
            fragment in t.name.lower() for fragment in 
            ['tool_list', 'tool_get', 'tool_call']
        )]
        
        if wrapper_selected:
            print(f"   ✅ Wrapper tools selected: {[t.name for t in wrapper_selected]}")
        else:
            print(f"   ⚠️ No wrapper tools selected (may be OK if direct tools are relevant)")
        
        # Step 5: Test _build_catalog_tools expansion
        print("\n5. Testing catalog tool expansion...")
        from gpt_researcher.mcp.research import MCPResearchSkill
        
        research_skill = MCPResearchSkill(MockCfg(), None)
        
        if wrapper_selected:
            # Try to expand wrapper tools
            try:
                expanded = await research_skill._build_catalog_tools(wrapper_selected)
                print(f"   Expanded tools: {[t.name for t in expanded]}")
                if expanded:
                    print(f"   ✅ Successfully expanded {len(expanded)} catalog tools")
            except Exception as e:
                print(f"   ⚠️ Expansion error: {e}")
        else:
            print("   ⏭️ Skipping expansion (no wrapper tools selected)")
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_tool_selection_flow())
    sys.exit(0 if result else 1)