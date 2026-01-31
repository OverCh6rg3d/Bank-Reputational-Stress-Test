"""
Synthetic Signal Generator - The "Genesis" Engine.

Generates high-fidelity synthetic social media signals (tweets, Reddit posts, news)
using LLMs to simulate realistic reputational threats.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from backend.core.llm_client import get_llm_client, SYSTEM_PROMPTS
from backend.models.schemas import (
    MediaType,
    PlatformSource,
    Scenario,
    SeverityLevel,
    SignalCategory,
    SocialSignal,
)

logger = logging.getLogger(__name__)

# Specialized prompt for signal generation
SIGNAL_GENERATION_PROMPT = """You are a "Social Listening Simulator" for Mashreq Bank.
Generate {count} realistic {platform} post(s) related to the following scenario:

SCENARIO: {scenario_name}
DESCRIPTION: {description}
KEY NARRATIVES: {narratives}
INTENDED SENTIMENT: {sentiment} (Score: {sentiment_score})
INTENDED CATEGORY: {category}

The content should be:
- Authentic to the platform style (hashtags, slang for Twitter/X; longer technical detail for Reddit; formal for News).
- Varied in tone (panic, anger, confusion, asking for help).
- Specific mention of "Mashreq Bank" or "Mashreq".

Respond with a JSON array of objects, each containing:
{{
    "content_text": "The actual post content...",
    "hashtags": ["tag1", "tag2"],
    "mentions": ["@mashreq", "@centralbank"],
    "virality_score": 0-100 (how likely it is to spread)
}}"""


class SyntheticSignalGenerator:
    """
    Generates synthetic social signals on demand using LLMs.
    """

    def __init__(self):
        self.llm = get_llm_client()

    async def generate_signals(
        self,
        scenario: Scenario,
        count: int = 5,
        platform_distribution: Optional[dict[PlatformSource, float]] = None,
    ) -> List[SocialSignal]:
        """
        Generate a batch of synthetic signals for a given scenario.

        Args:
            scenario: The threat scenario context.
            count: Total number of signals to generate.
            platform_distribution: Dict mapping platform to percentage (default: equal split).

        Returns:
            List of SocialSignal objects ready for ingestion.
        """
        if platform_distribution is None:
            # Default distribution
            platform_distribution = {
                PlatformSource.X_STYLE: 0.5,
                PlatformSource.REDDIT_STYLE: 0.3,
                PlatformSource.NEWS_PORTAL: 0.1,
                PlatformSource.LINKEDIN_STYLE: 0.1,
            }

        signals = []
        tasks = []

        # Determine counts per platform
        remaining = count
        for platform, percentage in platform_distribution.items():
            if remaining <= 0:
                break
            
            plat_count = int(count * percentage)
            if plat_count > remaining:
                plat_count = remaining
            
            if plat_count > 0:
                tasks.append(
                    self._generate_batch_for_platform(scenario, platform, plat_count)
                )
                remaining -= plat_count
        
        # Fill remainder with dominant platform (X)
        if remaining > 0:
             tasks.append(
                    self._generate_batch_for_platform(scenario, PlatformSource.X_STYLE, remaining)
                )

        # Run generation in parallel
        results = await asyncio.gather(*tasks)
        for batch in results:
            signals.extend(batch)

        return signals

    async def _generate_batch_for_platform(
        self, scenario: Scenario, platform: PlatformSource, count: int
    ) -> List[SocialSignal]:
        """Generate a batch of signals for a specific platform."""
        
        narratives = ", ".join(scenario.key_narratives)
        
        # Determine sentiment based on severity
        sentiment_score = -0.1
        if scenario.severity_level in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
            sentiment_score = -0.8
        elif scenario.severity_level == SeverityLevel.MEDIUM:
            sentiment_score = -0.5
            
        sentiment_desc = "Negative/Concerned" if sentiment_score < 0 else "Neutral"

        prompt = SIGNAL_GENERATION_PROMPT.format(
            count=count,
            platform=platform.value,
            scenario_name=scenario.scenario_name,
            description=scenario.description,
            narratives=narratives,
            sentiment=sentiment_desc,
            sentiment_score=sentiment_score,
            category=scenario.trigger_category.value,
        )

        try:
            response = await self.llm.async_complete_json(
                prompt=prompt,
                temperature=0.8, # High creativity for variation
            )
            
            raw_items = response if isinstance(response, list) else response.get("signals", [])
            if not raw_items and isinstance(response, dict):
                 # Handle case where LLM returns single object instead of list or wrapped list
                 raw_items = [response]

        except Exception as e:
            logger.error(f"Failed to generate signals for {platform}: {e}")
            return []

        signals = []
        for item in raw_items:
            # Create proper SocialSignal object
            try:
                sig = SocialSignal(
                    signal_id=uuid4(),
                    timestamp=datetime.now(), # Real-time generation
                    platform_source=platform,
                    author_id=uuid4(), # Anonymous/Random author
                    content_text=item.get("content_text", "Content unavailable"),
                    thread_id=uuid4(),
                    media_type=MediaType.NONE,
                    hashtags=item.get("hashtags", []),
                    mentions=item.get("mentions", []),
                    gt_category=scenario.trigger_category,
                    gt_sentiment=sentiment_score + random.uniform(-0.1, 0.1), # Add some noise
                    gt_is_misinformation=False, # Default to honest concern unless specified
                    gt_virality_potential=int(item.get("virality_score", 50)),
                )
                signals.append(sig)
            except Exception as e:
                logger.warning(f"Error parsing generated signal item: {e}")
                continue

        return signals

# Integration Test
if __name__ == "__main__":
    async def main():
        print("Testing Synthetic Signal Generator...")
        
        # Mock Scenario
        scenario = Scenario(
            scenario_id=uuid4(),
            created_at=datetime.now(),
            scenario_name="Data Leak Rumor",
            description="Rumors circulating about a potential data breach exposing customer emails.",
            trigger_category=SignalCategory.FRAUD_RUMOR,
            target_segment="All",
            severity_level=SeverityLevel.HIGH,
            expected_velocity_peak=85,
            recommended_response_time_hours=2.0,
            key_narratives=["I received a weird phishing email", "Is Mashreq hacked?", "My data is on the dark web"],
            monitoring_keywords=["hack", "leak", "breach"],
        )
        
        generator = SyntheticSignalGenerator()
        signals = await generator.generate_signals(scenario, count=3)
        
        for s in signals:
            print(f"\n[{s.platform_source.value}] {s.timestamp}")
            print(f"Content: {s.content_text}")
            print(f"Virality: {s.gt_virality_potential}")

    asyncio.run(main())
