from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from pyee import AsyncIOEventEmitter
from jsonschema import validate
from promptrix.promptrixTypes import PromptMemory, PromptFunctions, Tokenizer

class Command(ABC):
    title: str
    description: str
    inputs: Optional[str]
    output: Optional[str]

    @abstractmethod
    async def execute(self, input: Dict[str, Any], memory: 'PromptMemory', functions: 'PromptFunctions', tokenizer: 'Tokenizer') -> Any:
        pass

    @abstractmethod
    async def validate(self, input: Dict[str, Any], memory: 'PromptMemory', functions: 'PromptFunctions', tokenizer: 'Tokenizer') -> 'Validation':
        pass

TaskResponseStatus = Union['PromptResponseStatus', 'input_needed', 'too_many_steps']

@dataclass
class TaskResponse:
    type: str = 'TaskResponse'
    status: TaskResponseStatus = 'PromptResponseStatus'
    message: str = ''

class AgentThought:
    thoughts: Dict[str, str]
    command: Dict[str, Any]

AgentThoughtSchemaJSON: Dict[str,str] = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "command": {"type": "string"},
        "inputs": {"type": "object"},
    },
    "required": ["reasoning", "command"]
}

AgentThoughtSchemaTOML = {
    "reasoning": {
        "type":"string",
        "meta":"I want this field",
        "required": True
    },
    "command": {
        "type":"string",
        "required":True
    },
    "inputs":{
        "type":"dict",
        "keysrules": {"type": "string"}
    }
}
