"""
Signal Generator for the Reputational Stress-Test Simulator.

Uses LLM to generate realistic, scenario-specific social signals
organized by velocity/intensity levels for the simulation.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from .llm_client import get_llm_client, LLMClient

logger = logging.getLogger(__name__)


# =============================================================================
# Schema for Generated Signals
# =============================================================================

class GeneratedSignal(BaseModel):
    """A single generated social signal."""
    content: str
    platform: str  # x_style, reddit_style, news_portal
    sentiment: float  # -1.0 to 1.0
    virality: int  # 0-100
    author_type: str  # customer, influencer, journalist, bot


class SignalBatch(BaseModel):
    """Batch of signals for a single velocity level."""
    signals: list[GeneratedSignal]


# =============================================================================
# Prompt Templates
# =============================================================================

SYSTEM_PROMPT = """You are a social media content simulator for a bank crisis training exercise.
Generate realistic social media posts that would appear during a reputational crisis.

The bank is Mashreq Bank, a major UAE bank. Posts should feel authentic to the UAE/Gulf region.

For each post, specify:
- content: The actual post text (include emojis, hashtags naturally)
- platform: One of "x_style", "reddit_style", or "news_portal"
- sentiment: Float from -1.0 (very negative) to 1.0 (positive)
- virality: Integer 0-100 indicating viral potential
- author_type: One of "customer", "influencer", "journalist", "bot"

Generate diverse posts from different perspectives and platforms."""


LEVEL_PROMPTS = {
    "low": """Generate {count} social media posts for the EARLY/LOW INTENSITY phase of a "{scenario}" crisis.

This is the CONFUSION phase - people are just becoming aware. Include:
- Genuine questions and mild concerns ("Is anyone else experiencing...?")
- Some defenders ("Works fine for me")
- Curious bystanders
- Initial reports without full context

Sentiment should mostly be -0.2 to -0.5 (mildly negative to neutral).
Virality should be 10-45 (low to moderate).

Return as JSON array of signals.""",

    "medium": """Generate {count} social media posts for the MEDIUM INTENSITY phase of a "{scenario}" crisis.

This is the FRUSTRATION phase - the issue is confirmed and spreading. Include:
- Validated complaints from affected customers
- People sharing their negative experiences
- Industry watchers commenting
- No more defenders - consensus is forming
- Some people considering switching banks

Sentiment should be -0.4 to -0.75 (notably negative).
Virality should be 35-70 (moderate to high).

Return as JSON array of signals.""",

    "high": """Generate {count} social media posts for the HIGH INTENSITY/PEAK phase of a "{scenario}" crisis.

This is the OUTRAGE phase - full viral crisis. Include:
- Angry customers demanding action
- Calls to action ("Everyone report them!", "Time to switch banks!")
- People tagging regulators (@CBUAE, @UAEGov)
- Journalists covering the story
- Potential influencers amplifying
- Some possible bot-like coordinated messaging

Sentiment should be -0.7 to -1.0 (very negative).
Virality should be 60-95 (high to viral).

Include hashtags like #MashreqFail, #{scenario relevant hashtag}, #BankingCrisis, etc.

Return as JSON array of signals.""",
}


SCENARIO_CONTEXT = {
    "Data Leak": "Customer data has allegedly been exposed or leaked. Posts should reference concerns about personal information, account security, passwords, and potential identity theft.",
    "Outage": "Banking services are down - app, website, ATMs not working. Posts should reference inability to access money, failed transactions, and service reliability.",
    "Deepfake": "A viral video allegedly shows the bank CEO making damaging statements. Posts should reference the video, questions about authenticity, and reputation concerns.",
}


# =============================================================================
# Signal Generator
# =============================================================================

class SignalGenerator:
    """
    Generates realistic social signals using LLM.
    
    Signals are organized into three velocity levels (low, medium, high)
    to match the simulation's crisis intensity.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._llm_client = llm_client
        self._cache: dict[str, dict] = {}  # scenario -> signals by level

    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = get_llm_client()
        return self._llm_client

    def _get_scenario_key(self, scenario_name: str) -> str:
        """Map scenario name to known scenario type."""
        scenario_lower = scenario_name.lower()
        for key in SCENARIO_CONTEXT.keys():
            if key.lower() in scenario_lower:
                return key
        return "Data Leak"  # Default

    async def _generate_level(
        self, 
        scenario_name: str,
        level: str,
        count: int = 15
    ) -> list[dict]:
        """Generate signals for a single velocity level."""
        scenario_key = self._get_scenario_key(scenario_name)
        context = SCENARIO_CONTEXT.get(scenario_key, SCENARIO_CONTEXT["Data Leak"])
        
        prompt = LEVEL_PROMPTS[level].format(
            count=count,
            scenario=scenario_key
        )
        prompt += f"\n\nScenario context: {context}"

        try:
            result = await self.llm_client.async_complete_json(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.9,  # Higher for variety
                max_tokens=2048,
            )

            # Handle different response formats
            if isinstance(result, list):
                signals = result
            elif isinstance(result, dict):
                signals = result.get("signals", result.get("posts", []))
            else:
                signals = []

            # Normalize and validate
            normalized = []
            for sig in signals[:count]:
                normalized.append({
                    "content_text": sig.get("content", sig.get("text", "")),
                    "platform_source": sig.get("platform", "x_style"),
                    "gt_sentiment": float(sig.get("sentiment", -0.5)),
                    "gt_virality_potential": int(sig.get("virality", 50)),
                    "author_type": sig.get("author_type", "customer"),
                    "id": f"gen-{level}-{random.randint(1000, 9999)}",
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                    "hashtags": self._extract_hashtags(sig.get("content", "")),
                })
            
            logger.info(f"Generated {len(normalized)} signals for {scenario_name} at {level} level")
            return normalized

        except Exception as e:
            logger.error(f"Failed to generate signals for {level}: {e}")
            return self._get_fallback_signals(scenario_name, level, count)

    def _extract_hashtags(self, text: str) -> list[str]:
        """Extract hashtags from text."""
        import re
        return re.findall(r'#(\w+)', text)

    def _get_fallback_signals(self, scenario_name: str, level: str, count: int) -> list[dict]:
        """Fallback signals if LLM fails."""
        scenario_key = self._get_scenario_key(scenario_name)
        
        fallbacks = {
            "Data Leak": {
                "low": [
                    "Is anyone else having trouble logging into Mashreq today? Getting weird errors",
                    "My Mashreq app is asking me to reverify my account - is this normal?",
                    "Heard something about Mashreq security? Anyone know what's going on?",
                ],
                "medium": [
                    "Multiple reports of Mashreq accounts being compromised. Changed my password just in case",
                    "This is the second time Mashreq has had security issues this year. Unacceptable.",
                    "r/dubai thread on the Mashreq situation is blowing up. Not looking good.",
                ],
                "high": [
                    "UNACCEPTABLE @MashreqBank! My personal data may be exposed and you're silent?? #MashreqFail",
                    "Everyone affected by the Mashreq breach should report to @CBUAE immediately! #DataBreach",
                    "Time to move my money. Can't trust Mashreq with basic security. #SwitchBanks",
                ],
            },
            "Outage": {
                "low": [
                    "Mashreq app not loading for me. Anyone else?",
                    "Can't check my balance on Mashreq. Is it maintenance?",
                    "Works fine on my end. Try restarting your phone?",
                ],
                "medium": [
                    "Mashreq down for 3 hours now. This is getting ridiculous.",
                    "Had an important payment to make and Mashreq is completely down. Thanks a lot.",
                    "Third outage this month. Mashreq needs to invest in their infrastructure.",
                ],
                "high": [
                    "12 HOURS without access to MY MONEY! @MashreqBank this is criminal! #MashreqDown",
                    "Filing a complaint with @CBUAE. This level of service failure is unacceptable. #BankingCrisis",
                    "BREAKING: Mashreq Bank reports major system failure affecting thousands across UAE",
                ],
            },
            "Deepfake": {
                "low": [
                    "Did anyone see that Mashreq CEO video going around? Looks sus to me",
                    "What's this video about Mashreq circulating on WhatsApp?",
                    "Could be deepfake but idk, the video looks pretty real",
                ],
                "medium": [
                    "Whether the Mashreq video is real or fake, this is a PR disaster",
                    "Tech friends saying the CEO video has deepfake markers. But damage is done.",
                    "Mashreq stock dropping after that viral video. Company needs to respond ASAP.",
                ],
                "high": [
                    "SHOCKING: Mashreq CEO caught on video - real or AI? The bank MUST respond NOW! #MashreqScandal",
                    "If this is a deepfake attack on Mashreq, why hasn't the bank said ANYTHING? #Fraud",
                    "Withdrew all my savings from Mashreq. Not taking any chances. #TrustNoOne",
                ],
            },
        }

        base = fallbacks.get(scenario_key, fallbacks["Data Leak"])
        templates = base.get(level, base["medium"])

        signals = []
        sentiment_ranges = {"low": (-0.5, -0.2), "medium": (-0.75, -0.4), "high": (-1.0, -0.7)}
        virality_ranges = {"low": (15, 40), "medium": (40, 65), "high": (65, 95)}

        for i, content in enumerate(templates * ((count // len(templates)) + 1)):
            if len(signals) >= count:
                break
            s_range = sentiment_ranges[level]
            v_range = virality_ranges[level]
            signals.append({
                "content_text": content,
                "platform_source": random.choice(["x_style", "reddit_style", "news_portal"]),
                "gt_sentiment": round(random.uniform(*s_range), 2),
                "gt_virality_potential": random.randint(*v_range),
                "author_type": random.choice(["customer", "influencer", "journalist"]),
                "id": f"fallback-{level}-{i}",
                "timestamp": datetime.now().isoformat(),
                "hashtags": self._extract_hashtags(content),
            })

        return signals

    async def generate_all_levels(
        self,
        scenario_name: str,
        count_per_level: int = 15
    ) -> dict[str, list[dict]]:
        """
        Generate signals for all three velocity levels in parallel.
        
        Returns dict with keys: "low", "medium", "high"
        """
        # Check cache first
        cache_key = f"{scenario_name}_{count_per_level}"
        if cache_key in self._cache:
            logger.info(f"Using cached signals for {scenario_name}")
            return self._cache[cache_key]

        # Generate all levels in parallel
        logger.info(f"Generating signals for scenario: {scenario_name}")
        
        results = await asyncio.gather(
            self._generate_level(scenario_name, "low", count_per_level),
            self._generate_level(scenario_name, "medium", count_per_level),
            self._generate_level(scenario_name, "high", count_per_level),
            return_exceptions=True
        )

        signals = {
            "low": results[0] if not isinstance(results[0], Exception) else self._get_fallback_signals(scenario_name, "low", count_per_level),
            "medium": results[1] if not isinstance(results[1], Exception) else self._get_fallback_signals(scenario_name, "medium", count_per_level),
            "high": results[2] if not isinstance(results[2], Exception) else self._get_fallback_signals(scenario_name, "high", count_per_level),
        }

        # Cache the result
        self._cache[cache_key] = signals
        
        total = sum(len(v) for v in signals.values())
        logger.info(f"Generated {total} total signals for {scenario_name}")
        
        return signals


# =============================================================================
# Singleton
# =============================================================================

_signal_generator: Optional[SignalGenerator] = None


def get_signal_generator() -> SignalGenerator:
    """Get singleton SignalGenerator instance."""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = SignalGenerator()
    return _signal_generator
