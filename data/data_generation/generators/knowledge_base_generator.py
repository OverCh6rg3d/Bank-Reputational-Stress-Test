"""
Bank Knowledge Base Generator
Generates the official truth database for the Reputational Stress-Test Simulator
"""

import json
import uuid
from datetime import datetime, timedelta
import random
from pathlib import Path
from typing import Dict, List, Any
import csv


# Knowledge base facts organized by topic area
KNOWLEDGE_BASE_FACTS = {
    "Security": [
        {
            "fact_statement": "Mashreq Bank will NEVER ask for your OTP, PIN, or password through phone calls, SMS, or email. All such requests are fraudulent.",
            "keywords": ["OTP", "PIN", "password", "phone", "scam", "fraud", "phishing", "never ask"]
        },
        {
            "fact_statement": "All official Mashreq communications come from verified email domains ending in @mashreq.com or @mashreqbank.com only.",
            "keywords": ["email", "official", "verified", "domain", "mashreq.com"]
        },
        {
            "fact_statement": "The Mashreq mobile app uses biometric authentication (fingerprint/face ID) and 256-bit encryption for all transactions.",
            "keywords": ["app", "biometric", "encryption", "fingerprint", "face ID", "security"]
        },
        {
            "fact_statement": "Customers can instantly freeze their cards through the Mashreq app if they suspect unauthorized activity.",
            "keywords": ["freeze", "card", "app", "unauthorized", "instant", "block"]
        },
        {
            "fact_statement": "Two-factor authentication (2FA) is mandatory for all online banking transactions above AED 1,000.",
            "keywords": ["2FA", "two-factor", "authentication", "mandatory", "transactions"]
        },
        {
            "fact_statement": "Mashreq employs 24/7 fraud monitoring systems that automatically flag suspicious transactions.",
            "keywords": ["fraud", "monitoring", "24/7", "suspicious", "automatic", "detection"]
        },
        {
            "fact_statement": "Account login attempts are limited to 3 tries. After 3 failed attempts, the account is temporarily locked for security.",
            "keywords": ["login", "attempts", "locked", "failed", "security", "temporary"]
        },
        {
            "fact_statement": "Mashreq uses tokenization for all card-not-present transactions, meaning actual card numbers are never shared with merchants.",
            "keywords": ["tokenization", "card", "merchants", "secure", "numbers", "protected"]
        },
        {
            "fact_statement": "All Mashreq ATMs are equipped with anti-skimming technology and encrypted PIN pads.",
            "keywords": ["ATM", "skimming", "anti-skimming", "PIN", "encrypted", "secure"]
        },
        {
            "fact_statement": "Customers receive real-time SMS and push notifications for all account transactions above AED 100.",
            "keywords": ["SMS", "notifications", "real-time", "transactions", "alerts", "push"]
        },
        {
            "fact_statement": "Mashreq's Secure Key generates unique transaction codes that expire within 60 seconds.",
            "keywords": ["Secure Key", "transaction", "code", "expire", "unique", "60 seconds"]
        },
        {
            "fact_statement": "The bank maintains SOC 2 Type II and ISO 27001 certifications for information security management.",
            "keywords": ["SOC 2", "ISO 27001", "certified", "security", "compliance", "audit"]
        },
        {
            "fact_statement": "Mashreq never stores CVV numbers in its systems - these must be entered fresh for each transaction.",
            "keywords": ["CVV", "stored", "never", "security", "transaction", "fresh"]
        },
        {
            "fact_statement": "Password changes require verification through registered mobile number or email, plus security questions.",
            "keywords": ["password", "change", "verification", "mobile", "email", "security questions"]
        },
        {
            "fact_statement": "International transactions are blocked by default and must be enabled by the customer through the app or customer service.",
            "keywords": ["international", "transactions", "blocked", "enabled", "app", "default"]
        },
        {
            "fact_statement": "Mashreq partners with UAE Central Bank's AANI instant payment system for secure domestic transfers.",
            "keywords": ["AANI", "Central Bank", "instant", "payment", "domestic", "transfer", "secure"]
        },
        {
            "fact_statement": "All bank staff undergo regular security training and background checks as per UAE Central Bank regulations.",
            "keywords": ["staff", "training", "background", "checks", "regulations", "Central Bank"]
        },
        {
            "fact_statement": "Session timeout for online banking is set to 5 minutes of inactivity for security purposes.",
            "keywords": ["session", "timeout", "inactivity", "5 minutes", "security", "online banking"]
        },
        {
            "fact_statement": "Device registration is required for new logins - unrecognized devices trigger additional verification steps.",
            "keywords": ["device", "registration", "new", "login", "verification", "unrecognized"]
        },
        {
            "fact_statement": "Mashreq's fraud investigation team responds to reported incidents within 24 hours.",
            "keywords": ["fraud", "investigation", "24 hours", "reported", "response", "team"]
        }
    ],
    "Fees": [
        {
            "fact_statement": "Neo (digital) accounts have zero monthly maintenance fees for the first year.",
            "keywords": ["Neo", "digital", "zero", "free", "maintenance", "fees", "first year"]
        },
        {
            "fact_statement": "Standard savings accounts have a monthly fee of AED 25, waived if minimum balance of AED 3,000 is maintained.",
            "keywords": ["savings", "monthly", "fee", "AED 25", "minimum", "balance", "waived"]
        },
        {
            "fact_statement": "Domestic transfers via AANI are free for all Mashreq customers.",
            "keywords": ["domestic", "transfer", "AANI", "free", "customers"]
        },
        {
            "fact_statement": "International wire transfers cost AED 50 plus exchange rate margin of up to 2%.",
            "keywords": ["international", "wire", "transfer", "AED 50", "exchange", "rate", "margin"]
        },
        {
            "fact_statement": "ATM withdrawals at Mashreq ATMs are unlimited and free. Non-Mashreq ATMs incur AED 2 per transaction.",
            "keywords": ["ATM", "withdrawal", "free", "unlimited", "non-Mashreq", "AED 2"]
        },
        {
            "fact_statement": "Credit card annual fees range from AED 0 (Solitaire) to AED 750 (Platinum) depending on the card type.",
            "keywords": ["credit card", "annual", "fees", "Solitaire", "Platinum", "range"]
        },
        {
            "fact_statement": "Late payment fees on credit cards are AED 200 or 5% of the minimum due, whichever is higher.",
            "keywords": ["late", "payment", "fees", "credit card", "AED 200", "5%", "minimum"]
        },
        {
            "fact_statement": "Cheque book issuance is free for the first 25 leaves per year; additional leaves cost AED 1 each.",
            "keywords": ["cheque", "book", "free", "25", "leaves", "AED 1", "additional"]
        },
        {
            "fact_statement": "Account closure within 6 months of opening incurs an early closure fee of AED 100.",
            "keywords": ["account", "closure", "early", "fee", "AED 100", "6 months"]
        },
        {
            "fact_statement": "Currency conversion fees on debit card purchases abroad are 2.75% of the transaction amount.",
            "keywords": ["currency", "conversion", "fees", "debit", "abroad", "2.75%"]
        },
        {
            "fact_statement": "SMS banking alerts are free for the first 20 per month; additional alerts cost AED 0.30 each.",
            "keywords": ["SMS", "alerts", "free", "20", "AED 0.30", "additional"]
        },
        {
            "fact_statement": "Balance certificate issuance costs AED 50, liability letters cost AED 100.",
            "keywords": ["balance", "certificate", "liability", "letter", "AED 50", "AED 100"]
        },
        {
            "fact_statement": "Stop payment on cheques costs AED 50 per instruction.",
            "keywords": ["stop", "payment", "cheque", "AED 50", "instruction"]
        },
        {
            "fact_statement": "Salary transfer account holders receive fee waivers on most standard services.",
            "keywords": ["salary", "transfer", "account", "fee", "waiver", "services"]
        },
        {
            "fact_statement": "Dormant account reactivation fee is AED 50, charged after 12 months of inactivity.",
            "keywords": ["dormant", "reactivation", "fee", "AED 50", "12 months", "inactive"]
        }
    ],
    "App_Status": [
        {
            "fact_statement": "Scheduled maintenance windows are every Sunday from 2:00 AM to 4:00 AM UAE time.",
            "keywords": ["maintenance", "Sunday", "2 AM", "4 AM", "scheduled", "window"]
        },
        {
            "fact_statement": "The Mashreq app requires iOS 14.0+ or Android 8.0+ to function properly.",
            "keywords": ["app", "iOS", "Android", "version", "requirement", "14.0", "8.0"]
        },
        {
            "fact_statement": "Push notifications require app version 5.0 or higher to work correctly.",
            "keywords": ["push", "notifications", "version", "5.0", "app", "update"]
        },
        {
            "fact_statement": "Face ID login is only available on iPhone X and newer models.",
            "keywords": ["Face ID", "iPhone X", "login", "biometric", "newer"]
        },
        {
            "fact_statement": "The app automatically logs out after 5 minutes of inactivity for security.",
            "keywords": ["logout", "automatic", "5 minutes", "inactivity", "security"]
        },
        {
            "fact_statement": "Real-time notifications may experience delays of up to 30 seconds during peak hours.",
            "keywords": ["notifications", "delay", "30 seconds", "peak", "real-time"]
        },
        {
            "fact_statement": "UAE Pass integration for instant account opening is available in app version 6.0+.",
            "keywords": ["UAE Pass", "integration", "account", "opening", "version", "6.0"]
        },
        {
            "fact_statement": "International roaming may cause temporary connectivity issues with the app - use WiFi when abroad.",
            "keywords": ["international", "roaming", "connectivity", "WiFi", "abroad", "issues"]
        },
        {
            "fact_statement": "The web banking portal is accessible 24/7 as an alternative when the app is under maintenance.",
            "keywords": ["web", "banking", "portal", "24/7", "alternative", "maintenance"]
        },
        {
            "fact_statement": "Biometric login can be reset through the 'Forgot Password' flow if fingerprint/face is not recognized.",
            "keywords": ["biometric", "reset", "forgot", "password", "fingerprint", "face"]
        },
        {
            "fact_statement": "App cache should be cleared if experiencing persistent login issues - Settings > Storage > Clear Cache.",
            "keywords": ["cache", "clear", "login", "issues", "settings", "storage"]
        },
        {
            "fact_statement": "Dark mode is available in app version 5.5+ under Settings > Display.",
            "keywords": ["dark mode", "version", "5.5", "settings", "display"]
        }
    ],
    "Products": [
        {
            "fact_statement": "Neo is Mashreq's digital-only banking product with instant account opening via UAE Pass.",
            "keywords": ["Neo", "digital", "instant", "UAE Pass", "account", "opening"]
        },
        {
            "fact_statement": "Personal loans are available from AED 5,000 to AED 3 million with terms from 12 to 48 months.",
            "keywords": ["personal", "loan", "AED 5,000", "AED 3 million", "12 months", "48 months"]
        },
        {
            "fact_statement": "Home loans (mortgages) offer up to 80% financing for UAE nationals and 75% for expatriates.",
            "keywords": ["home", "loan", "mortgage", "80%", "75%", "UAE nationals", "expatriates"]
        },
        {
            "fact_statement": "Credit card limit increases can be requested every 6 months based on credit history.",
            "keywords": ["credit card", "limit", "increase", "6 months", "credit history"]
        },
        {
            "fact_statement": "Business accounts require trade license, Emirates ID, and minimum initial deposit of AED 10,000.",
            "keywords": ["business", "account", "trade license", "Emirates ID", "AED 10,000", "deposit"]
        },
        {
            "fact_statement": "Mashreq Gold savings account offers tiered interest rates up to 2.5% APY on balances above AED 100,000.",
            "keywords": ["Gold", "savings", "interest", "2.5%", "APY", "AED 100,000"]
        },
        {
            "fact_statement": "Fixed deposit terms range from 1 month to 5 years with interest rates from 2% to 4.5% APY.",
            "keywords": ["fixed", "deposit", "1 month", "5 years", "interest", "2%", "4.5%"]
        },
        {
            "fact_statement": "The Mashreq Platinum card includes complimentary airport lounge access (2 visits per quarter).",
            "keywords": ["Platinum", "card", "airport", "lounge", "complimentary", "2 visits"]
        },
        {
            "fact_statement": "Car loans are available for new and used vehicles up to 5 years old with financing up to 80%.",
            "keywords": ["car", "loan", "new", "used", "5 years", "80%", "financing"]
        },
        {
            "fact_statement": "Mashreq Investment services require minimum investment of AED 50,000 for managed portfolios.",
            "keywords": ["investment", "managed", "portfolio", "AED 50,000", "minimum"]
        },
        {
            "fact_statement": "Overdraft facilities are available for salary account holders with limits up to 2x monthly salary.",
            "keywords": ["overdraft", "salary", "account", "2x", "limit", "monthly"]
        },
        {
            "fact_statement": "Joint accounts are available for married couples with either 'Either or Survivor' or 'Both to Sign' operation modes.",
            "keywords": ["joint", "account", "married", "either", "survivor", "both", "sign"]
        },
        {
            "fact_statement": "Minor savings accounts can be opened for children aged 0-18 with guardian oversight.",
            "keywords": ["minor", "children", "savings", "0-18", "guardian", "oversight"]
        },
        {
            "fact_statement": "Mashreq Millionaire savings account enters customers into monthly prize draws for every AED 5,000 saved.",
            "keywords": ["Millionaire", "savings", "prize", "draw", "monthly", "AED 5,000"]
        },
        {
            "fact_statement": "Trade finance solutions include Letters of Credit, Bank Guarantees, and Documentary Collections.",
            "keywords": ["trade", "finance", "letter of credit", "bank guarantee", "documentary", "collection"]
        }
    ],
    "Compliance": [
        {
            "fact_statement": "Mashreq complies with UAE Personal Data Protection Law (PDPL) Federal Decree-Law No. 45 of 2021.",
            "keywords": ["PDPL", "data protection", "UAE", "law", "Federal", "45", "2021", "complies"]
        },
        {
            "fact_statement": "KYC (Know Your Customer) documents must be updated every 2 years as per UAE Central Bank requirements.",
            "keywords": ["KYC", "documents", "update", "2 years", "Central Bank", "requirements"]
        },
        {
            "fact_statement": "Large cash transactions above AED 55,000 are reported to the UAE Financial Intelligence Unit.",
            "keywords": ["cash", "transactions", "AED 55,000", "reported", "Financial Intelligence", "large"]
        },
        {
            "fact_statement": "Account holders must notify the bank of address changes within 30 days per banking regulations.",
            "keywords": ["address", "change", "notify", "30 days", "regulations", "banking"]
        },
        {
            "fact_statement": "Mashreq is regulated by the UAE Central Bank and holds a full banking license since 1967.",
            "keywords": ["Central Bank", "regulated", "license", "1967", "full", "banking"]
        },
        {
            "fact_statement": "Customer data is stored in UAE-based data centers and never transferred outside the country without consent.",
            "keywords": ["data", "stored", "UAE", "data centers", "never", "transferred", "consent"]
        },
        {
            "fact_statement": "Anti-money laundering (AML) screening is performed on all international transfers.",
            "keywords": ["AML", "anti-money laundering", "screening", "international", "transfers"]
        },
        {
            "fact_statement": "Mashreq's privacy policy allows customers to opt out of marketing communications at any time.",
            "keywords": ["privacy", "policy", "opt out", "marketing", "communications", "any time"]
        },
        {
            "fact_statement": "The bank is required to report suspected fraud to authorities within 24 hours of detection.",
            "keywords": ["fraud", "report", "authorities", "24 hours", "detection", "required"]
        },
        {
            "fact_statement": "Emirates ID verification is mandatory for all account-related transactions at branches.",
            "keywords": ["Emirates ID", "verification", "mandatory", "account", "transactions", "branches"]
        },
        {
            "fact_statement": "Mashreq undergoes annual external audits by one of the Big 4 accounting firms.",
            "keywords": ["audit", "annual", "external", "Big 4", "accounting", "firms"]
        },
        {
            "fact_statement": "Customer complaint resolution SLA is 5 business days for standard issues, 15 days for complex cases.",
            "keywords": ["complaint", "resolution", "SLA", "5 days", "15 days", "business", "standard"]
        },
        {
            "fact_statement": "Tax residency self-certification (CRS/FATCA) is required for all new account holders.",
            "keywords": ["tax", "residency", "CRS", "FATCA", "certification", "required", "new account"]
        },
        {
            "fact_statement": "Beneficial ownership declaration is required for all corporate accounts per AML regulations.",
            "keywords": ["beneficial", "ownership", "declaration", "corporate", "AML", "regulations"]
        },
        {
            "fact_statement": "The bank's capital adequacy ratio exceeds the minimum 13% required by UAE Central Bank.",
            "keywords": ["capital", "adequacy", "ratio", "13%", "Central Bank", "exceeds", "minimum"]
        }
    ]
}


def generate_knowledge_base() -> List[Dict[str, Any]]:
    """Generate the complete knowledge base."""
    knowledge_entries = []
    base_date = datetime.now() - timedelta(days=30)
    
    for topic_area, facts in KNOWLEDGE_BASE_FACTS.items():
        print(f"Processing {len(facts)} facts for topic: {topic_area}")
        
        for i, fact_data in enumerate(facts):
            # Generate realistic last_updated date (within last 6 months)
            days_ago = random.randint(0, 180)
            last_updated = base_date - timedelta(days=days_ago)
            
            # Generate realistic public URL
            topic_slug = topic_area.lower().replace("_", "-")
            url_path = fact_data["keywords"][0].lower().replace(" ", "-")
            public_url = f"https://www.mashreqbank.com/uae/en/faq/{topic_slug}/{url_path}"
            
            entry = {
                "kb_id": str(uuid.uuid4()),
                "topic_area": topic_area,
                "fact_statement": fact_data["fact_statement"],
                "public_url": public_url,
                "last_updated": last_updated.isoformat(),
                "keywords": json.dumps(fact_data["keywords"])
            }
            
            knowledge_entries.append(entry)
    
    return knowledge_entries


def save_knowledge_base_csv(entries: List[Dict[str, Any]], output_path: Path):
    """Save knowledge base to CSV file."""
    if not entries:
        print("No entries to save!")
        return
    
    fieldnames = list(entries[0].keys())
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)
    
    print(f"✓ Saved {len(entries)} knowledge base entries to {output_path}")


def main():
    """Main entry point for knowledge base generation."""
    print("=" * 60)
    print("Bank Knowledge Base Generator")
    print("=" * 60)
    
    # Generate knowledge base
    entries = generate_knowledge_base()
    
    # Save to datasets folder
    output_dir = Path(__file__).parent.parent.parent / "datasets"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "bank_knowledge_base.csv"
    save_knowledge_base_csv(entries, output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Generation Summary:")
    print("=" * 60)
    
    from collections import Counter
    topic_counts = Counter(e["topic_area"] for e in entries)
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic}: {count} facts")
    
    print(f"\nTotal: {len(entries)} knowledge base entries generated")
    return entries


if __name__ == "__main__":
    main()
