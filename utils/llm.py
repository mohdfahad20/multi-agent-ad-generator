"""
utils/llm.py
Creates a shared CrewAI-compatible LLM using OpenRouter as the provider.
OpenRouter exposes an OpenAI-compatible API, so we use langchain_openai.ChatOpenAI.
"""

from crewai import LLM

from config import settings
from utils.logger import get_logger

logger = get_logger("llm")


def get_llm() -> LLM:
    """
    Returns a CrewAI LLM instance backed by OpenRouter.
    Any free model on https://openrouter.ai/models?q=free can be used.
    """
    logger.info(f"Initialising LLM: {settings.OPENROUTER_MODEL}")

    llm = LLM(
        model=f"openrouter/{settings.OPENROUTER_MODEL}",
        base_url=settings.OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        temperature=0.7,
        max_tokens=4096,
    )
    return llm