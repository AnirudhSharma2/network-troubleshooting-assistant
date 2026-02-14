"""
Abstract base class for AI providers.

This defines the pluggable interface for AI-powered features.
The core diagnostic logic is ALWAYS rule-based; AI only handles:
1. Human-friendly explanation generation
2. Learning mode explanations
3. Practice scenario generation
"""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract interface for AI providers (mock, OpenAI, Gemini, etc.)."""

    @abstractmethod
    def generate_explanation(self, issues: list[dict[str, Any]], score: float) -> str:
        """
        Convert rule engine output into a plain English explanation.

        Args:
            issues: List of issue dicts from the rule engine
            score: Health score (0–100)

        Returns:
            Human-friendly explanation string
        """
        pass

    @abstractmethod
    def generate_learning_content(self, issue: dict[str, Any]) -> dict[str, str]:
        """
        Generate educational content explaining WHY a fix works.

        Args:
            issue: Single issue dict from the rule engine

        Returns:
            Dict with 'concept', 'explanation', 'why_fix_works', 'analogy'
        """
        pass

    @abstractmethod
    def generate_scenario(self, scenario_type: str, difficulty: str) -> dict[str, Any]:
        """
        Generate a broken network scenario for practice.

        Args:
            scenario_type: 'routing', 'vlan', 'interface', 'ip', or 'mixed'
            difficulty: 'easy', 'medium', or 'hard'

        Returns:
            Dict with 'title', 'description', 'network_config',
            'expected_issues', 'instructions'
        """
        pass
