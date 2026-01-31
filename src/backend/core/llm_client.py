"""
LLM Client for the Reputational Stress-Test Simulator.

Provides a unified interface to OpenAI/Gemini for:
- Signal classification
- Agent decision simulation  
- Causal attribution
- Response generation
"""

import json
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper for LLM API calls with structured output support.
    Uses OpenAI by default, can be extended for Gemini.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
    ):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var.")

        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

        logger.info(f"LLMClient initialized with model: {model}")

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Simple completion - returns raw text response.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""

    async def async_complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Async version of complete for parallel agent processing.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""

    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """
        Completion with JSON output parsing.
        """
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\n\nRespond only with valid JSON."

        response = self.complete(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Clean markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {response}")
            return {"error": str(e), "raw": response}

    async def async_complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """
        Async version of complete_json.
        """
        json_system = (system_prompt or "") + "\n\nRespond only with valid JSON."

        response = await self.async_complete(
            prompt=prompt,
            system_prompt=json_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": str(e), "raw": response}

    def complete_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> BaseModel:
        """
        Completion with Pydantic model validation.
        Returns a validated Pydantic object.
        """
        # Get JSON schema from Pydantic model
        schema = response_model.model_json_schema()

        system = f"""{system_prompt or ''}

You must respond with a JSON object that matches this schema:
{json.dumps(schema, indent=2)}

Respond only with valid JSON matching the schema."""

        result = self.complete_json(
            prompt=prompt,
            system_prompt=system,
            temperature=temperature,
        )

        return response_model.model_validate(result)

    async def async_complete_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> BaseModel:
        """
        Async version of complete_structured.
        """
        schema = response_model.model_json_schema()

        system = f"""{system_prompt or ''}

You must respond with a JSON object that matches this schema:
{json.dumps(schema, indent=2)}

Respond only with valid JSON matching the schema."""

        result = await self.async_complete_json(
            prompt=prompt,
            system_prompt=system,
            temperature=temperature,
        )

        return response_model.model_validate(result)


# =============================================================================
# Pre-defined System Prompts
# =============================================================================

SYSTEM_PROMPTS = {
    "signal_classifier": """You are an expert risk analyst for a major UAE bank (Mashreq Bank).
Your task is to analyze social media signals and classify them into risk categories.

You must be:
- Precise: Distinguish between genuine concerns and noise
- Cautious: When uncertain, flag for human review
- Explainable: Always provide reasoning for your classification

Categories:
- Fraud_Rumor: Claims of security breaches, scams, hacking
- Service_Outage: Reports of app/ATM/service failures
- Competitor_News: Comparisons to other banks, switching intent
- Positive_Neutral: Praise, neutral mentions, questions
- Irrelevant: Off-topic, spam, unrelated content""",

    "agent_simulator": """You are roleplaying as a synthetic customer of Mashreq Bank in the UAE.
You will be given a persona with specific traits (skepticism, brand loyalty, values) and
asked to decide how you would react to a social media post about the bank.

Your decision must be consistent with your persona's traits:
- High skepticism = need more proof before sharing
- High brand loyalty = likely to defend the bank
- Low financial literacy = more susceptible to scams

Available actions: IGNORE, LIKE, SHARE, COMMENT, REPORT

Always explain your reasoning from the perspective of your persona.""",

    "causal_analyst": """You are a senior risk intelligence analyst performing root cause analysis.
Given a cluster of social signals, you must determine the most likely cause:

Possible causes:
- Coordinated Attack: Bot networks, competitor sabotage, organized FUD
- Genuine Concern: Real customer experiences, legitimate complaints
- Service Issue: Actual technical problems or outages
- Misinformation: False claims spreading organically
- Random Noise: Coincidental clustering of unrelated posts

Provide probability estimates and identify gaps in evidence.""",

    "adversarial_critic": """You are a devil's advocate AI tasked with finding flaws in risk predictions.
Your job is to challenge every conclusion and identify:

1. Logical gaps in the reasoning
2. Alternative explanations not considered
3. Missing evidence that would change the conclusion
4. Potential biases in the analysis

Be thorough but constructive. If the prediction is solid, acknowledge it.""",

    "response_generator": """You are a crisis communications expert for a major bank.
Given a risk analysis, you must generate an appropriate response strategy.

Guidelines:
- Never recommend public posting (zero-action protocol)
- Always recommend human review
- Be proportionate to the risk level
- Consider regulatory implications
- Prioritize customer safety and trust

Output structured recommendations with clear steps.""",

    "briefing_writer": """You are a senior executive communications specialist.
Your task is to distill complex technical risk analyses into clear, actionable briefings
for C-suite executives.

Guidelines:
- Lead with the bottom line
- Use plain language, avoid jargon
- Include confidence levels and uncertainties
- Present clear options, not just problems
- Keep it under 300 words""",
}


# =============================================================================
# Singleton Instance
# =============================================================================

_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
