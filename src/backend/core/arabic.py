"""
Arabic Language Support Module.

Provides utilities for handling Arabic text, including:
- RTL layout direction detection
- Text normalization
- Bi-directional sentiment analysis helpers
"""

import re
import unicodedata
from typing import Optional

class ArabicHandler:
    """Handles Arabic-specific text processing."""
    
    ARABIC_RANGE = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
    
    @staticmethod
    def is_arabic(text: str) -> bool:
        """Check if text contains Arabic characters."""
        return bool(re.search(ArabicHandler.ARABIC_RANGE, text))
    
    @staticmethod
    def get_text_direction(text: str) -> str:
        """Return 'rtl' if text is primarily Arabic, else 'ltr'."""
        if not text:
            return "ltr"
        
        # Simple heuristic: look at first strong directional character
        for char in text:
            direction = unicodedata.bidirectional(char)
            if direction in ('R', 'AL'):
                return "rtl"
            elif direction == 'L':
                return "ltr"
                
        return "ltr"
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Arabic text (remove tatweel, normalize alef/yeh/teh)."""
        if not text:
            return ""
            
        # Remove Tatweel (Kashida)
        text = re.sub(r'\u0640', '', text)
        
        # Normalize Alef forms
        text = re.sub(r'[أإآ]', 'ا', text)
        
        # Normalize Teh Marbuta
        text = re.sub(r'ة', 'h', text) # Often mapped to h or t depending on context, keeping simple
        
        # NormalizeYeh
        text = re.sub(r'ى', 'ي', text)
        
        return text

    @staticmethod
    def format_for_display(text: str) -> str:
        """Format text for display with appropriate direction markers."""
        if ArabicHandler.is_arabic(text):
            return f"\u202B{text}\u202C"  # Wrap in RLE and PDF
        return text

    @property
    def system_prompt_addition(self) -> str:
        """Prompt instruction for LLMs to handle Arabic."""
        return (
            "You are capable of processing mixed English and Arabic text. "
            "When analyzing Arabic content, consider cultural context and nuances. "
            "Respond in English unless keeping the original quote."
        )

# Sentiment nuances for Arabic financial context
ARABIC_SENTIMENT_KEYWORDS = {
    "positive": [
        "ممتاز", "رائع", "ثقة", "أمان", "نمو", "أرباح", "تحسن"
    ],
    "negative": [
        "نصب", "احتيال", "سرقة", "تأخير", "سيء", "فشل", "انهيار", "خسارة"
    ]
}

def analyze_arabic_sentiment_heuristic(text: str) -> Optional[float]:
    """
    Simple heuristic sentiment analysis for Arabic text.
    Returns score between -1.0 and 1.0, or None if no keywords found.
    """
    if not ArabicHandler.is_arabic(text):
        return None
        
    score = 0.0
    found = False
    
    for word in ARABIC_SENTIMENT_KEYWORDS["positive"]:
        if word in text:
            score += 0.5
            found = True
            
    for word in ARABIC_SENTIMENT_KEYWORDS["negative"]:
        if word in text:
            score -= 0.8  # Negative words carry more weight in banking
            found = True
            
    return max(-1.0, min(1.0, score)) if found else 0.0
