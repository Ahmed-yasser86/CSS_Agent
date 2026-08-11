import os
print('RETRIEVER=', os.environ.get('RETRIEVER'))
print('TAVILY_API_KEY present=', bool(os.environ.get('TAVILY_API_KEY')))
try:
    import tavily
    print('tavily package importable: yes')
except Exception as e:
    print('tavily package importable: no', type(e), e)
try:
    from gpt_researcher.gpt_researcher.retrievers.tavily import tavily_search as ts
    print('TavilySearch module importable: yes')
    print('TavilySearch class present:', hasattr(ts, 'TavilySearch'))
except Exception as e:
    print('TavilySearch module import error:', type(e), e)
try:
    from gpt_researcher.gpt_researcher.config.variables import default as dv
    print('config default RETRIEVER=', dv.get('RETRIEVER'))
except Exception as e:
    print('could not read config default', type(e), e)
