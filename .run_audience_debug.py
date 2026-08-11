import os
import logging
import runpy

logging.basicConfig(level=logging.DEBUG)
# Shorter timeouts for debugging
os.environ['RESEARCH_TIMEOUT'] = os.environ.get('RESEARCH_TIMEOUT', '120')
os.environ['RETRIEVER_TIMEOUT'] = os.environ.get('RETRIEVER_TIMEOUT', '30')

print('Env RESEARCH_TIMEOUT=', os.environ['RESEARCH_TIMEOUT'])
print('Env RETRIEVER_TIMEOUT=', os.environ['RETRIEVER_TIMEOUT'])

runpy.run_path('Retrival_Pipline\\Graph\\Chains\\tests\\Audience_Profile_Layer.py', run_name='__main__')
