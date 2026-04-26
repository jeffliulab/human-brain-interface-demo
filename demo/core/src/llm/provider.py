from openai import OpenAI

from src.config import settings


def get_client() -> OpenAI:
    return OpenAI(api_key=settings.api_key, base_url=settings.LLM_BASE_URL)
