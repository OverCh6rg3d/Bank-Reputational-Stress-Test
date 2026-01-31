"""
LLM Client - OpenAI Integration
Handles all LLM API calls for high-quality data generation
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("LLM_MODEL", "gpt-4o")


def generate_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None
) -> str:
    """Generate a single completion from OpenAI."""
    try:
        kwargs = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"OpenAI API error: {e}")
        raise


def generate_json_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 2000
) -> Dict[str, Any]:
    """Generate a JSON completion from OpenAI."""
    response = generate_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"}
    )
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {response[:200]}...")
        raise


def generate_batch_completions(
    system_prompt: str,
    user_prompts: List[str],
    temperature: float = 0.8,
    max_tokens: int = 2000,
    batch_size: int = 10,
    delay_between_batches: float = 0.5
) -> List[str]:
    """Generate multiple completions with rate limiting."""
    results = []
    total = len(user_prompts)
    
    for i in range(0, total, batch_size):
        batch = user_prompts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"  Processing batch {batch_num}/{total_batches}...")
        
        for prompt in batch:
            result = generate_completion(
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            results.append(result)
        
        # Rate limiting delay between batches
        if i + batch_size < total:
            time.sleep(delay_between_batches)
    
    return results


def generate_batch_json_completions(
    system_prompt: str,
    user_prompts: List[str],
    temperature: float = 0.8,
    max_tokens: int = 2000,
    batch_size: int = 10,
    delay_between_batches: float = 0.5
) -> List[Dict[str, Any]]:
    """Generate multiple JSON completions with rate limiting."""
    results = []
    total = len(user_prompts)
    failed = 0
    
    for i in range(0, total, batch_size):
        batch = user_prompts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"  Processing batch {batch_num}/{total_batches}...")
        
        for prompt in batch:
            try:
                result = generate_json_completion(
                    system_prompt=system_prompt,
                    user_prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                results.append(result)
            except Exception as e:
                print(f"  Warning: Batch item failed: {e}")
                failed += 1
                results.append(None)
        
        # Rate limiting delay between batches
        if i + batch_size < total:
            time.sleep(delay_between_batches)
    
    if failed > 0:
        print(f"  ⚠ {failed} items failed out of {total}")
    
    return results


# Pre-defined system prompts for different generation tasks
SYSTEM_PROMPTS = {
    "archetype": """You are an expert in behavioral psychology and consumer segmentation for the UAE banking sector.
Your task is to create realistic, detailed customer personas (archetypes) for a bank's stress-test simulation.

Each persona should feel like a real person with:
- Authentic motivations and fears
- Realistic financial behaviors
- Cultural context appropriate to the UAE
- Clear personality traits that affect how they react to banking news

Be creative and specific. Avoid generic descriptions.""",

    "social_post": """You are a social media content simulator for a UAE banking crisis simulation.
Your task is to generate highly realistic social media posts that could appear during a reputational crisis.

Rules:
1. Match the exact platform style (X/Twitter = short/punchy, Reddit = detailed/analytical, LinkedIn = professional, News = formal)
2. Match the language requested (English, Arabic Gulf dialect, or Mixed/code-switching)
3. Match the emotional tone of the category (Fraud = fear/anger, Outage = frustration, etc.)
4. Include realistic typos, hashtags, mentions as appropriate
5. Reference "Mashreq" or "MashreqBank" as the bank
6. Make it feel like a real person wrote it

For Arabic: Use Gulf dialect (UAE/Dubai style), not formal Arabic.
For Mixed: Natural English-Arabic code-switching common in UAE.""",

    "knowledge_fact": """You are a banking compliance and communications expert for a UAE bank.
Your task is to create official fact statements that could appear in a bank's FAQ or knowledge base.

Each fact should be:
- Clear and unambiguous
- Professionally worded
- Useful for debunking misinformation
- Accurate to how UAE banks actually operate
- Include specific details (numbers, timeframes, etc.)"""
}


def test_connection():
    """Test the OpenAI connection."""
    try:
        response = generate_completion(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Connection successful!' in exactly 2 words.",
            max_tokens=10
        )
        print(f"✓ OpenAI connection test: {response.strip()}")
        return True
    except Exception as e:
        print(f"✗ OpenAI connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
