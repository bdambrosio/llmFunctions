import requests
import json
import openai
import sys
import os
import socket
import time
import string
import webbrowser
#from urllib.request import urlopen
from datetime import date
from datetime import datetime
import traceback
import random
import readline as rl
import concurrent.futures
from promptrix.VolatileMemory import VolatileMemory
from promptrix.FunctionRegistry import FunctionRegistry
from promptrix.GPT3Tokenizer import GPT3Tokenizer
from alphawave_pyexts.SearchCommand import SearchCommand
from alphawave.OpenAIClient import OpenAIClient
from alphawave.OSClient import OSClient
from alphawave_agents.Agent import Agent, AgentOptions
from alphawave_pyexts.SearchCommand import SearchCommand
from alphawave_pyexts import utilityV2 as ut
from alphawave_pyexts.llmsearch import google_search_concurrent as gs
import tracemalloc
import asyncio

async def run_chat(client, query_string, model,  memory, functions, tokenizer, search_level=gs.QUICK_SEARCH):
  #tracemalloc.start()
  response_text = ''
  storeInteraction = True
  try:
    #
    #### 
    #
    query_phrase, keywords = await ut.get_search_phrase_and_keywords(client, query_string, model, memory, functions, tokenizer)

    try:
      google_text, urls_all, index, urls_used, tried_index, urls_tried = \
        await gs.search_google(query_string, gs.QUICK_SEARCH, query_phrase, keywords, client, model, memory, functions, tokenizer)
    except:
      traceback.print_exc()
      return ''
    return google_text
  except KeyboardInterrupt:
    sys.exit(-1)
  except:
    traceback.print_exc()
  return ''

if __name__ == '__main__' :

  client = OpenAIClient(apiKey=os.getenv('OPENAI_API_KEY'), logRequests=True)
  #client = OSClient(apiKey=os.getenv('OPENAI_API_KEY'), logRequests=True)
  model = 'gpt-3.5-turbo'
  memory = VolatileMemory()
  functions = FunctionRegistry()
  tokenizer = GPT3Tokenizer()

while True:
  #async def run_chat(client, query_string, model,  memory, functions, tokenizer, search_level=gs.QUICK_SEARCH):
  asyncio.run(run_chat(client, input('Yes?'),model, memory, functions, tokenizer))
