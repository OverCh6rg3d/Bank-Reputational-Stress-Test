"""
LLM-Enhanced Social Signal Generator
Generates high-quality synthetic social media posts using GPT-4
"""

import json
import uuid
import random
import csv
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .llm_client import generate_json_completion, SYSTEM_PROMPTS

# Thread-safe counter
class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

# Load templates
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def load_distributions() -> Dict[str, Any]:
    """Load value distributions from JSON template."""
    with open(TEMPLATE_DIR / "value_distributions.json", "r") as f:
        return json.load(f)


# Category context for prompts
CATEGORY_CONTEXTS = {
    "Fraud_Rumor": {
        "themes": [
            "OTP/PIN phishing scams",
            "Data breach rumors",
            "Account hacking claims",
            "Fake bank employee calls",
            "SMS phishing attempts",
            "App security vulnerabilities",
            "Card skimming incidents",
            "Social engineering attacks",
            "Unauthorized transactions",
            "Identity theft concerns"
        ],
        "emotions": ["fear", "anger", "panic", "distrust", "urgency"],
        "sentiment_range": (-1.0, -0.3),
        "virality_range": (50, 95)
    },
    "Service_Outage": {
        "themes": [
            "App not working/loading",
            "Can't login to account",
            "Transfer stuck/pending",
            "Salary not credited",
            "ATM out of order",
            "Card declined unexpectedly",
            "Website down",
            "Slow transaction processing",
            "Face ID/biometric issues",
            "Payment failures"
        ],
        "emotions": ["frustration", "anger", "desperation", "disappointment"],
        "sentiment_range": (-0.9, -0.2),
        "virality_range": (30, 80)
    },
    "Competitor_News": {
        "themes": [
            "Better interest rates elsewhere",
            "Competitor app is superior",
            "Lower fees at other banks",
            "Faster loan approval at competitor",
            "Better customer service elsewhere",
            "New features at competitor banks",
            "Switching bank experience",
            "Rate/fee comparisons",
            "Reward program comparisons",
            "Cashback offers from competitors"
        ],
        "emotions": ["comparison", "curiosity", "slight frustration", "neutral"],
        "sentiment_range": (-0.5, 0.3),
        "virality_range": (20, 60)
    },
    "Positive_Neutral": {
        "themes": [
            "Great customer service experience",
            "Easy account opening",
            "Fast loan approval",
            "Helpful app features",
            "Efficient problem resolution",
            "Long-time customer satisfaction",
            "New feature appreciation",
            "Seamless transfer experience",
            "Card rewards benefits",
            "Security features appreciation"
        ],
        "emotions": ["satisfaction", "gratitude", "relief", "recommendation"],
        "sentiment_range": (0.2, 1.0),
        "virality_range": (10, 50)
    },
    "Irrelevant": {
        "themes": [
            "Dubai weather/lifestyle",
            "UAE traffic",
            "Food recommendations",
            "Weekend activities",
            "Shopping/sales",
            "Sports events",
            "Entertainment/movies",
            "General life updates",
            "Travel in UAE",
            "Local news unrelated to banking"
        ],
        "emotions": ["neutral", "happy", "casual", "excited"],
        "sentiment_range": (-0.2, 0.3),
        "virality_range": (5, 30)
    }
}

PLATFORM_CONFIGS = {
    "X_Style": {
        "max_length": 280,
        "description": "Twitter/X style - short, punchy, emotional, hashtags, mentions, possible typos",
        "example": "🚨 Just got a suspicious call from 'Mashreq support' asking for my OTP. DO NOT FALL FOR THIS! #Scam #MashreqBank"
    },
    "Reddit_Style": {
        "max_length": 1500,
        "description": "Reddit style - detailed, analytical, skeptical, question-asking, technical discussions",
        "example": "Has anyone else noticed issues with Mashreq's app lately? I've been trying to transfer money for 3 hours and it keeps timing out. Starting to wonder if there's a bigger issue going on."
    },
    "News_Portal": {
        "max_length": 500,
        "description": "News style - formal, journalistic, neutral tone, headline + summary format",
        "example": "UAE BANKING: Mashreq Bank customers report intermittent service disruptions. The bank has not yet issued an official statement regarding the matter."
    },
    "LinkedIn_Style": {
        "max_length": 1200,
        "description": "LinkedIn style - professional, personal anecdotes, thought leadership, industry insights",
        "example": "A valuable lesson in digital banking security today. Received a call claiming to be from Mashreq - red flags everywhere. Here's what you should watch out for..."
    }
}

LANGUAGE_CONFIGS = {
    "en": "English - natural, conversational English as used in the UAE expat community",
    "ar": "Arabic - Gulf dialect (UAE/Dubai style) with Arabic script. NOT formal/classical Arabic. Use natural Gulf expressions.",
    "mix": "Mixed/Code-switching - natural blend of English and Arabic as commonly used in UAE social media, e.g., 'The app is down والله تعبنا!'"
}


class LLMSocialSignalGenerator:
    def __init__(self):
        self.distributions = load_distributions()
        self.generated_hashes = set()
        self.archetypes = []
        self.counter = Counter()
        
    def load_archetypes(self, archetypes_path: Path):
        """Load archetypes from CSV file."""
        if archetypes_path.exists():
            with open(archetypes_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.archetypes = list(reader)
            print(f"Loaded {len(self.archetypes)} archetypes")
        
    def select_author(self, platform: str) -> Optional[str]:
        """Select an author archetype that prefers this platform."""
        if not self.archetypes:
            return None
        matching = [a for a in self.archetypes if a["preferred_platform"] == platform]
        if matching and random.random() < 0.7:
            return random.choice(matching)["agent_id"]
        return random.choice(self.archetypes)["agent_id"]
    
    def build_generation_prompt(
        self,
        category: str,
        platform: str,
        language: str,
        theme: Optional[str] = None
    ) -> str:
        """Build the prompt for generating a social post."""
        cat_config = CATEGORY_CONTEXTS[category]
        plat_config = PLATFORM_CONFIGS[platform]
        lang_desc = LANGUAGE_CONFIGS[language]
        
        if theme is None:
            theme = random.choice(cat_config["themes"])
        
        emotion = random.choice(cat_config["emotions"])
        
        prompt = f"""Generate a realistic social media post with the following specifications:

PLATFORM: {platform}
- Style: {plat_config["description"]}
- Max length: {plat_config["max_length"]} characters
- Example style: "{plat_config["example"]}"

CATEGORY: {category}
- Theme: {theme}
- Emotional tone: {emotion}

LANGUAGE: {language}
- {lang_desc}

BANK REFERENCE: Use "Mashreq" or "MashreqBank" or "@MashreqBank" as the bank name.

Generate a completely unique, realistic post that sounds like it was written by a real person in the UAE.

Return as JSON with these exact fields:
{{
    "content_text": "the post content",
    "hashtags": ["list", "of", "hashtags"],
    "mentions": ["@mentions"],
    "emotional_tone": "primary emotion",
    "is_misinformation": true/false (for Fraud_Rumor: true if the post makes FALSE claims about the bank, false if it's a GENUINE warning)
}}"""
        
        return prompt
    
    def generate_single_post(
        self,
        category: str = None,
        platform: str = None,
        language: str = None,
        base_time: datetime = None,
        parent_id: str = None,
        thread_id: str = None,
        theme: str = None
    ) -> Optional[Dict[str, Any]]:
        """Generate a single social signal using LLM."""
        
        # Select random values if not provided
        if category is None:
            dist = self.distributions["post_category_distribution"]
            category = random.choices(list(dist.keys()), list(dist.values()))[0]
        
        if language is None:
            dist = self.distributions["language_distribution"]
            language = random.choices(list(dist.keys()), list(dist.values()))[0]
        
        if platform is None:
            platforms = list(PLATFORM_CONFIGS.keys())
            platform = random.choice(platforms)
        
        if base_time is None:
            base_time = datetime.now()
        
        # Generate via LLM
        prompt = self.build_generation_prompt(category, platform, language, theme)
        
        try:
            response = generate_json_completion(
                system_prompt=SYSTEM_PROMPTS["social_post"],
                user_prompt=prompt,
                temperature=0.9,
                max_tokens=800
            )
        except Exception as e:
            print(f"  LLM generation failed: {e}")
            return None
        
        # Extract fields
        content = response.get("content_text", "")
        if not content:
            return None
        
        # Deduplication check
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.generated_hashes:
            return None  # Skip duplicate
        self.generated_hashes.add(content_hash)
        
        # Generate metadata
        cat_config = CATEGORY_CONTEXTS[category]
        min_sent, max_sent = cat_config["sentiment_range"]
        min_vir, max_vir = cat_config["virality_range"]
        
        sentiment = round(random.uniform(min_sent, max_sent), 2)
        virality = random.randint(min_vir, max_vir)
        
        # Boost virality for certain keywords
        for keyword in ["BREAKING", "WARNING", "urgent", "hacked", "scam", "انتبهوا"]:
            if keyword.lower() in content.lower():
                virality = min(100, virality + 10)
        
        # Generate timestamp
        hours_ago = random.uniform(0, 168)
        timestamp = base_time - timedelta(hours=hours_ago)
        
        # IDs
        signal_id = str(uuid.uuid4())
        author_id = self.select_author(platform)
        
        if parent_id is None:
            thread_id = signal_id
        
        # Media type
        media_types = ["None", "Image", "Video_Link"]
        media_type = random.choices(media_types, [0.7, 0.2, 0.1])[0]
        
        return {
            "signal_id": signal_id,
            "timestamp": timestamp.isoformat(),
            "platform_source": platform,
            "author_id": author_id or "",
            "content_text": content,
            "parent_id": parent_id or "",
            "thread_id": thread_id or signal_id,
            "media_type": media_type,
            "language": language,
            "hashtags": json.dumps(response.get("hashtags", [])),
            "mentions": json.dumps(response.get("mentions", [])),
            "gt_category": category,
            "gt_sentiment": sentiment,
            "gt_is_misinformation": response.get("is_misinformation", False),
            "gt_virality_potential": virality
        }
    
    def generate_thread(
        self,
        root_category: str,
        min_replies: int = 2,
        max_replies: int = 6,
        base_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Generate a conversational thread."""
        if base_time is None:
            base_time = datetime.now()
        
        signals = []
        
        # Generate root post
        root = self.generate_single_post(category=root_category, base_time=base_time)
        if not root:
            return []
        
        signals.append(root)
        thread_id = root["signal_id"]
        root_time = datetime.fromisoformat(root["timestamp"])
        
        # Generate replies
        num_replies = random.randint(min_replies, max_replies)
        reply_parents = [root["signal_id"]]
        
        for i in range(num_replies):
            reply_time = root_time + timedelta(minutes=random.randint(5, 120 * (i + 1)))
            
            # Reply category - can be supporting, contradicting, or neutral
            if root_category in ["Fraud_Rumor", "Service_Outage"]:
                reply_category = random.choice([root_category, root_category, "Positive_Neutral"])
            else:
                reply_category = root_category
            
            parent_id = random.choice(reply_parents)
            language = root["language"] if random.random() < 0.7 else None
            
            reply = self.generate_single_post(
                category=reply_category,
                language=language,
                platform=root["platform_source"],
                base_time=reply_time,
                parent_id=parent_id,
                thread_id=thread_id
            )
            
            if reply:
                signals.append(reply)
                reply_parents.append(reply["signal_id"])
        
        return signals
    
    def generate_batch(
        self,
        target_count: int = 5000,
        thread_probability: float = 0.2,
        max_workers: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate a batch of social signals with parallel processing."""
        signals = []
        base_time = datetime.now()
        
        # Calculate distribution
        estimated_thread_signals = int(target_count * thread_probability)
        standalone_count = target_count - estimated_thread_signals
        num_threads = estimated_thread_signals // 4
        
        print(f"Generating ~{standalone_count} standalone posts and ~{num_threads} threads using GPT-4o...")
        print(f"This may take a while. Estimated API calls: {standalone_count + num_threads * 5}")
        
        # Generate standalone signals
        print(f"\n📝 Generating {standalone_count} standalone posts...")
        
        def generate_with_progress():
            post = self.generate_single_post(base_time=base_time)
            count = self.counter.increment()
            if count % 50 == 0:
                print(f"  Generated {count}/{standalone_count} posts...")
            return post
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(generate_with_progress) for _ in range(standalone_count)]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    signals.append(result)
        
        print(f"  ✓ Generated {len(signals)} standalone posts")
        
        # Generate threads
        print(f"\n🧵 Generating {num_threads} threads...")
        categories = list(CATEGORY_CONTEXTS.keys())
        
        for i in range(num_threads):
            if (i + 1) % 20 == 0:
                print(f"  Generated {i + 1}/{num_threads} threads...")
            
            root_category = random.choices(
                categories,
                weights=[0.3, 0.35, 0.15, 0.1, 0.1]
            )[0]
            
            thread = self.generate_thread(root_category, base_time=base_time)
            signals.extend(thread)
        
        print(f"  ✓ Generated {num_threads} threads")
        
        return signals


def save_signals_csv(signals: List[Dict[str, Any]], output_path: Path):
    """Save signals to CSV file."""
    if not signals:
        print("No signals to save!")
        return
    
    fieldnames = [
        "signal_id", "timestamp", "platform_source", "author_id",
        "content_text", "parent_id", "thread_id", "media_type",
        "language", "hashtags", "mentions", "gt_category",
        "gt_sentiment", "gt_is_misinformation", "gt_virality_potential"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(signals)
    
    print(f"✓ Saved {len(signals)} social signals to {output_path}")


def main(target_count: int = 5000):
    """Main entry point for LLM social signal generation."""
    print("=" * 60)
    print("LLM-Enhanced Social Signal Generator (GPT-4o)")
    print("=" * 60)
    
    generator = LLMSocialSignalGenerator()
    
    # Load archetypes if available
    datasets_dir = Path(__file__).parent.parent.parent / "datasets"
    archetypes_path = datasets_dir / "agent_archetypes.csv"
    generator.load_archetypes(archetypes_path)
    
    # Generate signals
    signals = generator.generate_batch(
        target_count=target_count,
        thread_probability=0.2,
        max_workers=5
    )
    
    # Sort by timestamp
    signals.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Save to file
    datasets_dir.mkdir(exist_ok=True)
    output_path = datasets_dir / "social_signals_stream.csv"
    save_signals_csv(signals, output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Generation Summary:")
    print("=" * 60)
    
    from collections import Counter
    
    category_counts = Counter(s["gt_category"] for s in signals)
    print("\nBy Category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count} ({count*100//len(signals)}%)")
    
    lang_counts = Counter(s["language"] for s in signals)
    print("\nBy Language:")
    for lang, count in sorted(lang_counts.items()):
        print(f"  {lang}: {count} ({count*100//len(signals)}%)")
    
    print(f"\nTotal: {len(signals)} social signals generated")
    return signals


if __name__ == "__main__":
    main(target_count=100)  # Small test batch
