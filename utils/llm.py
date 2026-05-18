"""
Centralized LLM Initialization Module.

Uses the raw Groq Python SDK, wrapped in a minimal LangChain-compatible
BaseChatModel so CrewAI agents can consume it directly. This avoids ALL
version conflicts between langchain-core, langchain-groq, litellm, and openai.
"""

import os
import json
from typing import Any, List, Optional
from groq import Groq
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from utils.logger import get_logger

logger = get_logger(__name__)


class GroqChatLLM(BaseChatModel):
    """Minimal LangChain-compatible wrapper around the raw Groq SDK."""

    client: Any = None
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", temperature: float = 0.7, **kwargs):
        super().__init__(**kwargs)
        self.client = Groq(api_key=api_key)
        self.model_name = model
        self.temperature = temperature

    def _convert_messages(self, messages: List[BaseMessage]) -> list:
        """Convert LangChain message objects to Groq-compatible dicts."""
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})
            else:
                result.append({"role": "user", "content": msg.content})
        return result

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs) -> ChatResult:
        """Core generation method called by LangChain/CrewAI."""
        groq_messages = self._convert_messages(messages)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=groq_messages,
            temperature=self.temperature,
            stop=stop
        )
        content = response.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    @property
    def _llm_type(self) -> str:
        return "groq-chat"


def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.7) -> GroqChatLLM:
    """
    Returns a Groq-backed LLM compatible with CrewAI agents.

    Args:
        model: Groq model identifier.
        temperature: Creativity dial.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not found; using local MockLLM fallback for development.")

        class MockLLM:
            """Lightweight LLM-like object that returns a deterministic JSON payload.

            This avoids raising errors when an API key isn't present and enables
            running the app locally for testing or demo purposes.
            """
            def __init__(self, model, temperature):
                self.model_name = model
                self.temperature = temperature

            def invoke(self, messages):
                # Return an object with a `content` attribute similar to Groq responses
                payload = {
                    "experience": "I engaged with the topic in a structured manner, reviewing core concepts and examples.",
                    "feelings": "I felt curious and motivated to explore further.",
                    "learning": "a) Concept A explained\nb) Concept B explained\nc) Concept C explained",
                    "application": "• Apply technique A in project X\n• Use framework B for scenario Y",
                    "conclusion": "This reflection highlights key insights and next steps for continued learning."
                }

                class Resp:
                    def __init__(self, content):
                        self.content = content

                # Local import to avoid any module-level import issues on deployed workers
                import json as _json
                return Resp(content=_json.dumps(payload))

        return MockLLM(model=model, temperature=temperature)

    llm = GroqChatLLM(api_key=api_key, model=model, temperature=temperature)
    logger.info(f"Groq LLM initialized: model={model}, temperature={temperature}")
    return llm