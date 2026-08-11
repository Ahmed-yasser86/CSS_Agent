"""Test that retrievers config works with 'tavily,mcp'."""
import os
import sys

# Add gpt-researcher to path
sys.path.insert(0, r'c:\Users\DELL\graph-rag-agent\gpt-researcher')

# Set environment
os.environ['TAVILY_API_KEY'] = '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'
os.environ['RETRIEVER'] = 'tavily,mcp'

# Create a mock config object
class MockConfig:
    def __init__(self):
        self.retriever = None
        self.retrievers = None

# Test get_retrievers
from gpt_researcher.actions.retriever import get_retrievers

cfg = MockConfig()
cfg.retrievers = 'tavily,mcp'

headers = {}
retriever_classes = get_retrievers(headers, cfg)

print(f"Retriever classes: {[r.__name__ for r in retriever_classes]}")
print(f"Expected: ['TavilySearch', 'MCPRetriever']")

# Verify
expected = ['TavilySearch', 'MCPRetriever']
actual = [r.__name__ for r in retriever_classes]

if actual == expected:
    print("✅ RETRIEVER=tavily,mcp works correctly!")
else:
    print(f"❌ Expected {expected} but got {actual}")