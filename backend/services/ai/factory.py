"""AI Provider Factory — returns the configured provider instance."""

from config import settings
from services.ai.base import AIProvider
from services.ai.mock_provider import MockAIProvider


def get_ai_provider() -> AIProvider:
    """
    Factory function returning the active AI provider.

    Default: MockAIProvider (template-based, no API key needed)
    Can be extended to support OpenAI, Gemini, etc.
    """
    provider_name = settings.AI_PROVIDER.lower()

    if provider_name == "mock":
        return MockAIProvider()
    # Future providers:
    # elif provider_name == "openai":
    #     from services.ai.openai_provider import OpenAIProvider
    #     return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
    else:
        # Fallback to mock
        return MockAIProvider()
