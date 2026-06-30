from abc import ABC, abstractmethod

from pydantic import BaseModel


class LLMPort(ABC):
    @abstractmethod
    async def invoke(self, prompt: str) -> str: ...

    @abstractmethod
    async def invoke_structured(self, prompt: str, output_schema: type[BaseModel]) -> BaseModel: ...
