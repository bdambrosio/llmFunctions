from pyee import AsyncIOEventEmitter
from typing import Dict, Any, List, Optional
from promptrix.promptrixTypes import PromptFunctions, PromptMemory, Tokenizer, Message, RenderedPromptSection
from promptrix.PromptSectionBase import PromptSectionBase
from alphawave_agents.agentTypes import Command
import traceback

class AgentCommandSection(PromptSectionBase):
    def __init__(self, commands: Dict[str, Command], tokens: int = -1, required: bool = True, one_shot=False, syntax = 'JSON'):
        super().__init__(tokens, required)
        self._commands = commands
        self.tokens = tokens
        self.required = required
        self.one_shot = one_shot
        self.syntax = syntax
        
    async def renderAsMessages(self, memory: Any, functions: Any, tokenizer: Any, max_tokens: int) -> Dict[str, Any]:
        # Render commands to message content
        content = 'commands:\n'
        for command in self._commands.values():
            content += f'\t{command.title}:\n'
            content += f'\t\tuse: {command.description}\n'
            if command.inputs:
                content += f'\t\tinputs: {command.inputs}\n'
            if command.output:
                content += f'\t\toutput: {command.output}\n'
            if self.one_shot:
                if self.syntax == 'JSON':
                    content += '\t\tformat: {'+f'"reasoning":"<concise reasons to use {command.title}>","command":'+f'"{command.title}", "inputs":'+'{'
                    args = ''
                    for arg in command.inputs.split(','):
                        key = (arg.split(':'))[0].strip().strip('"\'') # strip key down to bare alpha key (':' elims type info)
                        content += f'"{key}": "<value for {key}>,"'
                        content = content[:-1]+'}}\n' # strip final comma 
                    #print(f'***** AgentCommandSection one-shot prompt: {content}\n')
                else:
                    content += f'\t\tformat:\n[RESPONSE]\nreasoning="<concise reasons to use {command.title}>"\ncommand="{command.title}"\n'
                    args = ''
                    for arg in command.inputs.split(','):
                        key = 'inputs.'+(arg.split(':'))[0].strip().strip('"\'') # strip key down to bare alpha key (':' elims type info)
                        content += f'{key}="<value for {key}>"\n'
                        content +='[STOP]\n'
                    #print(f'***** AgentCommandSection one-shot TOML: {content}\n')
                    
        # Return as system message
        result = None
        try:
            length = len(tokenizer.encode(content))
            result = self.return_messages([{'role': 'system', 'content': content}], length, tokenizer, max_tokens)
        except Exception as e:
            traceback.print_exc()
        return result

