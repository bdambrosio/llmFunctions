import asyncio
import aiounittest, unittest
import os
from promptrix.VolatileMemory import VolatileMemory
from promptrix.FunctionRegistry import FunctionRegistry
from promptrix.GPT3Tokenizer import GPT3Tokenizer
from alphawave_pyexts.SearchCommand import SearchCommand
from alphawave.OpenAIClient import OpenAIClient
from alphawave.OSClient import OSClient
from alphawave_agents.Agent import Agent, AgentOptions
from alphawave_pyexts.SearchCommand import SearchCommand

# Create a client
#client = OpenAIClient(apiKey=os.getenv('OPENAI_API_KEY'), logRequests=True)
client = OSClient(apiKey=os.getenv('OPENAI_API_KEY'), logRequests=True)

class TestSearchCommand(aiounittest.AsyncTestCase):
    def setUp(self):
        self.memory = VolatileMemory()
        self.functions = FunctionRegistry()
        self.tokenizer = GPT3Tokenizer()

    def test_constructor(self):
        command = SearchCommand(client, 'gpt-3.5-turbo')
        self.assertEqual(command.title, 'search')
        self.assertEqual(command.description, 'web search for provided query')
        self.assertEqual(command.inputs, '"query":"<web query string>"')
        self.assertEqual(command.output, 'search result')

        command = SearchCommand(client, 'gpt-3.5-turbo', title='custom title', name='custom name', description='custom description')
        #self.assertEqual(command.title, 'custom title')
        self.assertEqual(command.description, 'custom description')
        self.assertEqual(command.inputs, '"query":"<web query string>"')
        self.assertEqual(command.output, 'search result')

    async def test_validate(self):
        command = SearchCommand(client, 'gpt-3.5-turbo')
        input = {
            'query': 'what is the weather today'
        }
        result = await command.validate(input, self.memory, self.functions, self.tokenizer)
        self.assertEqual(result['valid'], True)
        self.assertEqual(result['value'], input)

    async def test_execute(self):
        command = SearchCommand(client, 'gpt-3.5-turbo')
        input = {
            'query': 'what will the weather be today in Berkeley, CA'
        }
        result = await command.execute(input, self.memory, self.functions, self.tokenizer)
        self.assertEqual(result, 10)
        input = {
            'code': '7 +'
        }
        result = await command.execute(input, self.memory, self.functions, self.tokenizer)
        print(f'Test execute response \n\n{result}\n\n' )
        #self.assertEqual(result['message'], 'invalid syntax (<string>, line 1)')

if __name__ == '__main__':
    unittest.main()
