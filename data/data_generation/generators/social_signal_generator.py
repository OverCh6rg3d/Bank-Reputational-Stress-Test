"""
Social Signal Generator
Generates synthetic social media posts for the Reputational Stress-Test Simulator
"""

import json
import uuid
import random
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# Load templates
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def load_templates() -> Tuple[Dict, Dict, Dict]:
    """Load all template files."""
    with open(TEMPLATE_DIR / "platform_styles.json", "r") as f:
        platform_styles = json.load(f)
    with open(TEMPLATE_DIR / "value_distributions.json", "r") as f:
        distributions = json.load(f)
    with open(TEMPLATE_DIR / "arabic_phrases.json", "r") as f:
        arabic_phrases = json.load(f)
    return platform_styles, distributions, arabic_phrases


# Content templates by category
CONTENT_TEMPLATES = {
    "Fraud_Rumor": {
        "en": [
            "Just got a call from someone claiming to be from {bank}. They asked for my OTP! Is this a scam?",
            "WARNING: Someone is targeting {bank} customers with phishing emails. Do NOT click any links!",
            "My friend's account at {bank} was hacked last night. They lost AED {amount}. The app is NOT secure!",
            "Anyone else getting weird SMS from '{bank} Support'? Asking for card details. Seems fishy...",
            "BREAKING: Major security breach at {bank}?! My colleague said all their data was leaked!",
            "Can't trust {bank} anymore. Third person I know who got scammed through their app.",
            "PSA: If anyone calls asking for your {bank} OTP, HANG UP immediately. Almost fell for it today.",
            "Rumor going around that {bank}'s database was compromised. Anyone know if this is true?",
            "My mom almost transferred AED {amount} to scammers pretending to be {bank} support!",
            "Is the {bank} OTP bypass hack real? Seeing lots of posts about it on Twitter...",
            "Got an email about 'account verification' from {bank}. Clicked link. Think I'm compromised??",
            "BEWARE: New scam targeting {bank} credit card holders. They somehow have your phone number!",
            "{bank} customers BEWARE - there's a voice phishing attack going around. Very convincing!",
            "Why isn't {bank} warning customers about the OTP scam?! This is negligent!",
            "Lost AED {amount} because of {bank}'s weak security. Their 2FA is a joke.",
        ],
        "ar": [
            "انتبهوا! في نصابين يتصلون باسم {bank} ويطلبون الرمز السري!",
            "صديقي خسر {amount} درهم من حسابه في {bank}. كيف صار هذا؟!",
            "حذروا أهلكم! رسايل مشبوهة تجي باسم {bank}. لا تضغطون أي رابط!",
            "والله ما أصدق! {bank} ما يحمون عملاءهم من الاحتيال!",
            "للي ما يعرف - في هجوم الكتروني على بنك {bank}. انتبهوا على حساباتكم!",
            "رسالة من '{bank}' تطلب تحديث البيانات. هذا نصب صح؟",
            "البنك ما يطلب الرقم السري بالتلفون! انتبهوا يا جماعة!",
            "اتصلوا علي اليوم يقولون من {bank}. طلبوا OTP. خايف على حسابي!",
        ],
        "mix": [
            "Got a call from '{bank}' طلبوا مني OTP والله خايف now!",
            "WARNING للي عندهم حساب في {bank} - there's a phishing attack happening!",
            "My account got compromised والله تعبت معاهم in customer service!",
            "هل صحيح {bank} got hacked? كل الناس يقولون بالسوشيال ميديا!",
            "{bank} security ضعيف جداً... they keep getting hacked!",
        ]
    },
    "Service_Outage": {
        "en": [
            "Is {bank} app down for everyone or just me? Can't login since this morning!",
            "The {bank} app is DEAD. Can't make any transfers. This is ridiculous!",
            "@{bank} your app has been down for 3 hours. No acknowledgment. No ETA. Terrible!",
            "Can't access my {bank} account online. Website and app both down. Need to pay bills TODAY!",
            "Third time this month the {bank} app crashes. Time to switch banks honestly.",
            "Anyone else having issues with {bank} transfers? My money is stuck!",
            "{bank} online banking is slow as hell today. Takes 5 minutes to load a page.",
            "My salary didn't reflect in my {bank} account. It's been 2 hours. App shows nothing!",
            "@{bank} fix your servers! I have urgent payments to make!",
            "The {bank} ATMs near me are all out of order. Convenience? What convenience?",
            "Can't even check my balance on the {bank} app. Error 500. Very professional.",
            "Scheduled maintenance again? {bank} is always 'upgrading' but service gets worse!",
            "Payment failed 3 times on {bank} app. Had to use cash like it's 1990.",
            "My {bank} card got declined even though I have funds. Embarrassing at the restaurant!",
            "{bank} face ID stopped working after update. Now I'm locked out completely!",
        ],
        "ar": [
            "تطبيق {bank} ما يشتغل من الصباح! هل أنا الوحيد؟",
            "محد يرد في خدمة عملاء {bank}! التطبيق واقف ولا أحد يجاوب!",
            "التحويل من {bank} معلق من أمس. فلوسي وين راحت؟!",
            "ما أقدر أدخل حسابي في {bank}. الموقع والتطبيق كلهم واقفين!",
            "الله يستر على فلوسنا! {bank} واقف تماماً اليوم!",
            "{bank} لازم يحسنون سيرفراتهم! كل أسبوع نفس المشكلة!",
            "حاولت أسحب من صراف {bank}. 'خارج الخدمة'. كل الصرافات!",
            "راتبي ما نزل في حساب {bank}. الـ HR يقولون حولوه! وين راح؟",
        ],
        "mix": [
            "{bank} app واقف من ساعتين! I need to transfer money urgently!",
            "Is anyone else facing issues with {bank}? التطبيق مو راضي يفتح!",
            "Worst timing ever! {bank} down وعندي payment deadline!",
            "كل مرة maintenance في أسوأ وقت! {bank} please get it together!",
            "My {bank} card got declined حتى المبلغ موجود in my account!",
        ]
    },
    "Competitor_News": {
        "en": [
            "Just switched from {bank} to {competitor}. Best decision ever! Their app actually works.",
            "Heard {competitor} is offering 0% balance transfer from {bank}. Might be time to move!",
            "Why is {competitor} offering 3% savings rate while {bank} only gives 1.5%? Time to switch?",
            "{competitor} has a much better rewards program than {bank}. Just saying.",
            "My friend at {competitor} got instant loan approval. {bank} made me wait 2 weeks!",
            "Anyone compared {bank} vs {competitor} fees? Thinking of moving my business account.",
            "{competitor} app is so smooth compared to {bank}. Night and day difference!",
            "The new {competitor} card has no foreign transaction fees. {bank} charges 3%!",
            "{competitor} just launched instant transfers. Meanwhile {bank} still takes 24 hours.",
            "Saw {competitor} ad - they're offering AED {amount} cashback for new accounts from {bank}.",
            "Customer service at {competitor} > {bank}. Actually got a human after 2 minutes!",
            "{competitor}'s new digital account has no minimum balance. {bank} requires 3000!",
            "Read that {competitor} is merging with another bank. Will they be bigger than {bank}?",
            "Just got a better credit limit offer from {competitor}. Sorry {bank}, we're done.",
            "{competitor} approved my home loan in 3 days. {bank} rejected me after 3 weeks!",
        ],
        "ar": [
            "نقلت حسابي من {bank} لـ {competitor}. أفضل قرار! خدمتهم ممتازة!",
            "{competitor} يعطون نسبة أحسن على الادخار من {bank}. ليش أبقى معاهم؟",
            "تطبيق {competitor} أحسن بمراحل من تطبيق {bank}!",
            "سمعت {competitor} عندهم عرض للي يحولون من {bank}. حد جرب؟",
            "{bank} رسومهم عالية مقارنة بـ {competitor}. وقت التغيير!",
        ],
        "mix": [
            "Comparing banks and honestly {competitor} يفوز على {bank} in everything!",
            "Just opened account with {competitor} والفرق واضح from {bank}!",
            "{competitor} customer service رد علي بخمس دقائق. {bank} took 3 hours!",
            "The {competitor} rewards are actually useful مو زي {bank} اللي ما ينفع!",
        ]
    },
    "Positive_Neutral": {
        "en": [
            "Just opened a Neo account with {bank}. Super easy process, done in 5 minutes!",
            "Shoutout to {bank} customer service - resolved my issue in one call. Thanks!",
            "{bank} app update is actually nice. Dark mode finally! Looking sleek.",
            "My salary loan from {bank} got approved same day. Impressed with the speed!",
            "Been with {bank} for 10 years. Solid service, no major complaints.",
            "The {bank} Platinum card lounge access is underrated. Saved my Dubai layover!",
            "Finally set up Apple Pay with {bank}. Took forever but works great now!",
            "Quick question - does {bank} allow USD accounts for freelancers? Anyone know?",
            "{bank} ATM near my office is always stocked. Small wins matter!",
            "Got a call from {bank} about upgrading my account. No pressure, just info. Nice!",
            "Transferred money at 2am through {bank} app. Reached instantly. Love AANI!",
            "The new {bank} credit card designs look premium. Might get the black one.",
            "Deposited a check through {bank} app. Cleared next day. Technology!",
            "{bank} face ID login is so smooth. No more remembering passwords!",
            "Just used {bank} virtual card for online purchase. Extra secure, love it!",
        ],
        "ar": [
            "الحمد لله {bank} خدمتهم ممتازة. ما عندي شكوى!",
            "فتحت حساب Neo مع {bank} بخمس دقائق. سهل جداً!",
            "شكراً لفريق {bank} - حلوا مشكلتي بسرعة!",
            "تطبيق {bank} صار أحسن بعد التحديث. الديزاين حلو!",
            "{bank} أفضل بنك تعاملت معاه. مرتاح معاهم من سنين!",
            "حولت فلوس من {bank} بالليل ووصلت بثانية. ممتاز!",
        ],
        "mix": [
            "Loving the new {bank} app update! الديزاين صار جميل!",
            "{bank} customer service today was amazing والله impressed!",
            "Finally got my {bank} card مع الكاش باك. Feels good!",
            "Been a {bank} customer for years ولسى مرتاح معاهم. Good bank!",
        ]
    },
    "Irrelevant": {
        "en": [
            "What a beautiful sunset in Dubai today! 🌅",
            "Anyone know a good shawarma place near Marina?",
            "Traffic on Sheikh Zayed is INSANE right now. Stay home if you can!",
            "Just finished Squid Game season 2. No spoilers but WOW!",
            "Looking for recommendations for a birthday dinner in Downtown.",
            "The weather in UAE is finally cooling down. Time for outdoor activities!",
            "Who else is excited for the Dubai Shopping Festival?",
            "My phone battery dies so fast. Need to get it checked.",
            "Best gyms in JLT? Looking to start working out again.",
            "Can't believe it's almost February already. Time flies!",
            "Football match tonight! Who are you supporting?",
            "Tried the new coffee shop in DIFC. Overrated honestly.",
            "Need a good plumber. Any recommendations in Dubai Marina?",
            "Happy Friday everyone! What are your weekend plans?",
            "The new Metro extension is so convenient. Love it!",
        ],
        "ar": [
            "الجو في دبي اليوم جميل! ☀️",
            "أحد يعرف مطعم حلو في مارينا؟",
            "الزحمة في الشيخ زايد ما تنتهي!",
            "الويكند موعد الراحة! شنو خططكم؟",
            "سهرتنا اليوم مع الأهل. الحمد لله!",
            "الجو صار حلو أخيراً! وقت التخييم!",
        ],
        "mix": [
            "Beautiful day in Dubai! الجو amazing today! ☀️",
            "Looking for good restaurants في داون تاون. Any suggestions?",
            "Weekend vibes! مين عنده plans للسهرة؟",
            "The traffic اليوم is crazy! Stay home if you can!",
        ]
    }
}

# Bank and competitor names
BANKS = {
    "main": ["Mashreq", "MashreqBank", "Mashreq Bank"],
    "competitors": ["FAB", "ADCB", "Emirates NBD", "DIB", "RAKBank", "ENBD", "CBD"]
}

# Hashtags by category
HASHTAGS = {
    "Fraud_Rumor": ["#Scam", "#BankFraud", "#PhishingAlert", "#OTPScam", "#UAE", "#Dubai", "#BankingFraud", "#CyberSecurity", "#ScamAlert", "#BewareOfScams"],
    "Service_Outage": ["#AppDown", "#BankingFail", "#CustomerService", "#UAE", "#Dubai", "#DigitalBanking", "#TechFail", "#ServiceDown"],
    "Competitor_News": ["#Banking", "#UAE", "#Dubai", "#FinTech", "#SwitchBank", "#BetterRates", "#DigitalBanking"],
    "Positive_Neutral": ["#Banking", "#UAE", "#Dubai", "#DigitalBanking", "#CustomerExperience", "#FinTech", "#HappyCustomer"],
    "Irrelevant": ["#Dubai", "#UAE", "#DubaiLife", "#UAELife", "#Weekend", "#LifeInDubai", "#MyDubai"]
}


class SocialSignalGenerator:
    def __init__(self):
        self.platform_styles, self.distributions, self.arabic_phrases = load_templates()
        self.generated_hashes = set()  # For deduplication
        self.archetypes = []
        
    def load_archetypes(self, archetypes_path: Path):
        """Load archetypes from CSV file."""
        if archetypes_path.exists():
            with open(archetypes_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.archetypes = list(reader)
            print(f"Loaded {len(self.archetypes)} archetypes")
        else:
            print("Warning: Archetypes file not found. Posts will have NULL author_id.")
    
    def select_bank(self, is_main: bool = True) -> str:
        """Select a bank name."""
        if is_main:
            return random.choice(BANKS["main"])
        return random.choice(BANKS["competitors"])
    
    def select_author(self, platform: str) -> Optional[str]:
        """Select an author archetype that prefers this platform."""
        if not self.archetypes:
            return None
        
        # Filter archetypes by preferred platform
        matching = [a for a in self.archetypes if a["preferred_platform"] == platform]
        if matching:
            # 70% chance to use matching platform preference
            if random.random() < 0.7:
                return random.choice(matching)["agent_id"]
        
        # Otherwise random archetype
        return random.choice(self.archetypes)["agent_id"]
    
    def generate_content(self, category: str, language: str, platform: str) -> Tuple[str, List[str], List[str]]:
        """Generate post content based on category, language, and platform."""
        templates = CONTENT_TEMPLATES[category][language]
        template = random.choice(templates)
        
        # Fill in template variables
        content = template.format(
            bank=self.select_bank(is_main=True),
            competitor=self.select_bank(is_main=False),
            amount=random.choice([1000, 2500, 5000, 10000, 15000, 25000, 50000])
        )
        
        # Platform-specific styling
        style = self.platform_styles[platform]
        
        # Truncate if needed
        if len(content) > style["max_length"]:
            content = content[:style["max_length"]-3] + "..."
        
        # Add typos based on probability
        if random.random() < style["typo_probability"]:
            content = self._add_typo(content)
        
        # Generate hashtags
        hashtags = []
        num_hashtags = random.randint(style["hashtag_count"]["min"], style["hashtag_count"]["max"])
        if num_hashtags > 0:
            category_hashtags = HASHTAGS.get(category, [])
            hashtags = random.sample(category_hashtags, min(num_hashtags, len(category_hashtags)))
        
        # Generate mentions
        mentions = []
        if "{bank}" in template or "@" in template:
            if random.random() < 0.5:
                mentions.append("@MashreqBank")
        if category == "Service_Outage" and random.random() < 0.3:
            mentions.append("@CBUAEGov")  # Central Bank
        
        return content, hashtags, mentions
    
    def _add_typo(self, text: str) -> str:
        """Add a random typo to text."""
        if len(text) < 10:
            return text
        
        typo_types = ["double_letter", "missing_letter", "swap_letters"]
        typo_type = random.choice(typo_types)
        
        words = text.split()
        if not words:
            return text
        
        word_idx = random.randint(0, len(words) - 1)
        word = words[word_idx]
        
        if len(word) < 3:
            return text
        
        char_idx = random.randint(1, len(word) - 2)
        
        if typo_type == "double_letter":
            word = word[:char_idx] + word[char_idx] + word[char_idx:]
        elif typo_type == "missing_letter":
            word = word[:char_idx] + word[char_idx+1:]
        else:  # swap_letters
            word = word[:char_idx] + word[char_idx+1] + word[char_idx] + word[char_idx+2:]
        
        words[word_idx] = word
        return " ".join(words)
    
    def generate_ground_truth(self, category: str, content: str) -> Dict[str, Any]:
        """Generate ground truth metadata for a post."""
        # Sentiment based on category
        sentiment_ranges = {
            "Fraud_Rumor": (-1.0, -0.3),
            "Service_Outage": (-0.9, -0.2),
            "Competitor_News": (-0.5, 0.3),
            "Positive_Neutral": (0.2, 1.0),
            "Irrelevant": (-0.2, 0.3)
        }
        
        min_sent, max_sent = sentiment_ranges[category]
        sentiment = round(random.uniform(min_sent, max_sent), 2)
        
        # Virality potential
        virality_ranges = {
            "Fraud_Rumor": (40, 95),
            "Service_Outage": (30, 80),
            "Competitor_News": (20, 60),
            "Positive_Neutral": (10, 50),
            "Irrelevant": (5, 30)
        }
        min_vir, max_vir = virality_ranges[category]
        virality = random.randint(min_vir, max_vir)
        
        # Boost virality for certain keywords
        viral_keywords = ["BREAKING", "WARNING", "hacked", "scam", "leaked", "urgent", "انتبهوا", "خطير"]
        for keyword in viral_keywords:
            if keyword.lower() in content.lower():
                virality = min(100, virality + 15)
        
        # Is misinformation
        is_misinformation = False
        if category == "Fraud_Rumor":
            # Most fraud rumors are TRUE warnings, some are false claims
            is_misinformation = random.random() < 0.4
        
        return {
            "gt_category": category,
            "gt_sentiment": sentiment,
            "gt_is_misinformation": is_misinformation,
            "gt_virality_potential": virality
        }
    
    def generate_signal(
        self,
        category: str = None,
        language: str = None,
        platform: str = None,
        base_time: datetime = None,
        parent_id: str = None,
        thread_id: str = None
    ) -> Dict[str, Any]:
        """Generate a single social signal."""
        
        # Select random values if not provided
        if category is None:
            dist = self.distributions["post_category_distribution"]
            categories = list(dist.keys())
            weights = list(dist.values())
            category = random.choices(categories, weights=weights, k=1)[0]
        
        if language is None:
            dist = self.distributions["language_distribution"]
            languages = list(dist.keys())
            weights = list(dist.values())
            language = random.choices(languages, weights=weights, k=1)[0]
        
        if platform is None:
            platforms = list(self.platform_styles.keys())
            platform = random.choice(platforms)
        
        if base_time is None:
            base_time = datetime.now()
        
        # Generate content
        content, hashtags, mentions = self.generate_content(category, language, platform)
        
        # Check for duplicates
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if content_hash in self.generated_hashes:
            # Regenerate with slight variation
            content = content + " " + random.choice(["!!", "...", "?", "🤔", "😤", "⚠️"])
        self.generated_hashes.add(content_hash)
        
        # Generate timestamp (within last 7 days from base_time)
        hours_ago = random.uniform(0, 168)
        timestamp = base_time - timedelta(hours=hours_ago)
        
        # Generate IDs
        signal_id = str(uuid.uuid4())
        author_id = self.select_author(platform)
        
        # Thread handling
        if parent_id is None:
            thread_id = signal_id  # Original post is the thread root
        
        # Media type
        media_types = ["None", "Image", "Video_Link"]
        media_weights = [0.7, 0.2, 0.1]
        media_type = random.choices(media_types, weights=media_weights, k=1)[0]
        
        # Generate ground truth
        ground_truth = self.generate_ground_truth(category, content)
        
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
            "hashtags": json.dumps(hashtags),
            "mentions": json.dumps(mentions),
            **ground_truth
        }
    
    def generate_thread(
        self,
        root_category: str,
        min_replies: int = 2,
        max_replies: int = 8,
        base_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Generate a thread with original post and replies."""
        if base_time is None:
            base_time = datetime.now()
        
        signals = []
        
        # Generate root post
        root = self.generate_signal(category=root_category, base_time=base_time)
        signals.append(root)
        
        thread_id = root["signal_id"]
        root_time = datetime.fromisoformat(root["timestamp"])
        
        # Generate replies
        num_replies = random.randint(min_replies, max_replies)
        reply_parents = [root["signal_id"]]  # Can reply to root or other replies
        
        for i in range(num_replies):
            # Time progression for replies
            reply_time = root_time + timedelta(minutes=random.randint(1, 60 * (i + 1)))
            
            # Reply category logic
            if root_category == "Fraud_Rumor":
                reply_category = random.choice(["Fraud_Rumor", "Fraud_Rumor", "Positive_Neutral"])
            elif root_category == "Service_Outage":
                reply_category = random.choice(["Service_Outage", "Service_Outage", "Positive_Neutral"])
            else:
                reply_category = root_category
            
            # Select parent (root or previous reply)
            parent_id = random.choice(reply_parents)
            
            # Use same language as root 70% of time
            language = None
            if random.random() < 0.7:
                language = root["language"]
            
            reply = self.generate_signal(
                category=reply_category,
                language=language,
                platform=root["platform_source"],
                base_time=reply_time,
                parent_id=parent_id,
                thread_id=thread_id
            )
            
            signals.append(reply)
            reply_parents.append(reply["signal_id"])
        
        return signals
    
    def generate_batch(
        self,
        target_count: int = 5000,
        thread_probability: float = 0.3,
        avg_thread_size: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate a batch of social signals with some threads."""
        signals = []
        base_time = datetime.now()
        
        # Calculate how many standalone vs threads
        estimated_thread_signals = int(target_count * thread_probability)
        standalone_count = target_count - estimated_thread_signals
        num_threads = estimated_thread_signals // avg_thread_size
        
        print(f"Generating ~{standalone_count} standalone posts and ~{num_threads} threads...")
        
        # Generate category distribution
        dist = self.distributions["post_category_distribution"]
        categories = list(dist.keys())
        
        # Generate standalone signals
        for i in range(standalone_count):
            if i % 500 == 0:
                print(f"  Generated {i}/{standalone_count} standalone signals...")
            signal = self.generate_signal(base_time=base_time)
            signals.append(signal)
        
        # Generate threads
        for i in range(num_threads):
            if i % 100 == 0:
                print(f"  Generated {i}/{num_threads} threads...")
            
            # Thread root category - bias toward problem categories
            root_category = random.choices(
                categories,
                weights=[0.35, 0.35, 0.15, 0.1, 0.05],
                k=1
            )[0]
            
            thread = self.generate_thread(root_category, base_time=base_time)
            signals.extend(thread)
        
        return signals


def save_signals_csv(signals: List[Dict[str, Any]], output_path: Path):
    """Save signals to CSV file."""
    if not signals:
        print("No signals to save!")
        return
    
    fieldnames = list(signals[0].keys())
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(signals)
    
    print(f"✓ Saved {len(signals)} social signals to {output_path}")


def main():
    """Main entry point for social signal generation."""
    print("=" * 60)
    print("Social Signal Generator")
    print("=" * 60)
    
    generator = SocialSignalGenerator()
    
    # Load archetypes if available
    datasets_dir = Path(__file__).parent.parent.parent / "datasets"
    archetypes_path = datasets_dir / "agent_archetypes.csv"
    generator.load_archetypes(archetypes_path)
    
    # Generate signals
    signals = generator.generate_batch(
        target_count=5000,
        thread_probability=0.25,
        avg_thread_size=4
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
    
    platform_counts = Counter(s["platform_source"] for s in signals)
    print("\nBy Platform:")
    for plat, count in sorted(platform_counts.items()):
        print(f"  {plat}: {count}")
    
    lang_counts = Counter(s["language"] for s in signals)
    print("\nBy Language:")
    for lang, count in sorted(lang_counts.items()):
        print(f"  {lang}: {count} ({count*100//len(signals)}%)")
    
    # Thread stats
    thread_ids = set(s["thread_id"] for s in signals)
    threads_with_replies = sum(1 for t in thread_ids if sum(1 for s in signals if s["thread_id"] == t) > 1)
    print(f"\nThreads with replies: {threads_with_replies}")
    
    print(f"\nTotal: {len(signals)} social signals generated")
    return signals


if __name__ == "__main__":
    main()
