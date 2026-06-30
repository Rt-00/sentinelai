from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from sentinelai.domain.ports.llm_port import LLMPort


class OllamaAdapter(LLMPort):
    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        temperature: float = 0.0,
        num_predict: int = 2048,
    ) -> None:
        self._llm = ChatOllama(model=model, temperature=temperature, num_predict=num_predict)

    async def invoke(self, prompt: str) -> str:
        response = await self._llm.ainvoke([HumanMessage(content=prompt)])
        return str(response.content)

    async def invoke_structured(self, prompt: str, output_schema: type[BaseModel]) -> BaseModel:
        structured_llm = self._llm.with_structured_output(output_schema)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])
