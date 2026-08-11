import os
import sys

# Set test keys
os.environ.setdefault('GDELT_MCP_API_KEY', 'gdelt_sk_test')
os.environ.setdefault('SOCIALCRAWL_MCP_API_KEY', 'sc_test')
os.environ.setdefault('MCP_API_KEY', 'gdelt_sk_test')

# Add the tests directory to path
sys.path.insert(0, r'C:\Users\DELL\graph-rag-agent\Retrival_Pipline\Graph\Chains\tests')

from mcp_config import build_audience_mcp_configs
configs = build_audience_mcp_configs()
print('Number of configs:', len(configs))
for c in configs:
    print(f'  - {c.get("name")}: {c.get("connection_url")}')