# Comprehensive Dataset Schema Strategy
## Project: Reputational Stress-Test Simulator

> [!IMPORTANT]
> Since this project relies on **Synthetic Data**, we effectively need to "God Mode" this dataset. We must generate data that simulates the complexity of the real world to make the AI's job difficult and valuable.

This document defines the **Master Schema** required to build every feature discussed (Signal Detection, Velocity Simulation, Executive Briefing).

---

### 1. Input Data: The Synthetic Social Stream (`social_signals_stream.csv`)
**Purpose:** Represents the chaotic feed of social media posts, news, and comments that the system monitors.
**Volume:** High (Thousands of rows).

| Column Name | Type | Description / Why it's needed |
| :--- | :--- | :--- |
| `signal_id` | `UUID` | Unique identifier for every post/article. |
| `timestamp` | `DateTime` | Critical for calculating "Velocity" (tweets per hour). |
| `platform_source` | `Enum` | `X_Style`, `Reddit_Style`, `News_Portal`, `LinkedIn_Style`. Determines the formality/tone. |
| `author_id` | `UUID` | Links to `agent_archetypes.csv` (if author is a simulated agent) or `NULL` (if generic public). |
| `content_text` | `String` | The raw text body. **(Main input for LLM)**. |
| `parent_id` | `UUID` | If this is a reply, points to the original post. Critical for **Thread Reconstruction**. |
| `thread_id` | `UUID` | Groups all replies in a single conversation context. |
| `media_type` | `Enum` | `None`, `Image`, `Video_Link`. (Signal impact is higher with media). |
| `language` | `String` | `en`, `ar`, `mix`. (To test multilingual capabilities). |
| `hashtags` | `List[Str]` | extracted tags for clustering (e.g., #Mashreq, #Scam). |
| `mentions` | `List[Str]` | Who is tagged? (e.g., @CentralBank). |
| **Ground Truth Metadata** | *(Hidden from AI Agent)* | **Used for Evaluation/Testing** |
| `gt_category` | `Enum` | `Fraud_Rumor`, `Service_Outage`, `Competitor_News`, `Irrelevant`. |
| `gt_sentiment` | `Float` | -1.0 (Negative) to 1.0 (Positive). |
| `gt_is_misinformation` | `Bool` | `True` if the claim is objectively false. |
| `gt_virality_potential` | `Int` | 0-100. A pre-calculated score of how "catchy" this post is. |

---

### 2. The Population: Agent Archetypes (`agent_archetypes.csv`)
**Purpose:** Defines the "characters" in your simulation. Their traits determine *how* they spread or kill a rumor.
**Volume:** Medium (50-200 distinct personas).

| Column Name | Type | Description / Why it's needed |
| :--- | :--- | :--- |
| `agent_id` | `UUID` | Primary Key. |
| `archetype_name` | `String` | e.g., "Anxious Saver", "Crypto Bro", "Retired Professional". |
| `demographic_segment`| `Enum` | `GenZ`, `Millennial`, `SME_Owner`, `HNI` (High Net Worth). |
| `financial_literacy` | `Int` | 1-10. Low lit agents are more likely to share "Free Money" scams. |
| `brand_loyalty` | `Int` | 0-100. High loyalty agents might defend the brand; low might attack. |
| `skepticism_score` | `Int` | 1-10. High score = Needs more proof before sharing. |
| `network_influence` | `Int` | 1-100. How many "followers" they theoretically impact. |
| `activity_frequency` | `Float` | Posts per day. Determines how fast they react in simulation. |
| `preferred_platform` | `Enum` | Where they are most active (e.g., Professionals -> LinkedIn). |
| `core_values` | `List[Str]`| e.g., `["Security", "Speed"]` vs `["Transparency", "Ethics"]`. Guides their LLM reasoning. |

---

### 3. The Truth: Knowledge Base (`bank_knowledge_base.csv`)
**Purpose:** The "Reference Truth" your AI uses to debunk rumors or confirm outages.
**Volume:** Low (50-100 key facts).

| Column Name | Type | Description / Why it's needed |
| :--- | :--- | :--- |
| `kb_id` | `UUID` | Unique ID. |
| `topic_area` | `Enum` | `Fees`, `Security`, `App_Status`, `Products`. |
| `fact_statement` | `String` | The official truth. e.g., "The bank will NEVER ask for OTP via phone." |
| `public_url` | `String` | Link to the public FAQ/Page proving this fact. |
| `last_updated` | `DateTime` | To ensure the info isn't stale. |
| `keywords` | `List[Str]` | For vector retrieval. |

---

### 4. Output: Simulation Event Logs (`simulation_logs.csv`)
**Purpose:** This is the data *generated* by your system during a "Stress Test".
**Volume:** High (Generated dynamically).

| Column Name | Type | Description / Why it's needed |
| :--- | :--- | :--- |
| `simulation_id` | `UUID` | Tie events to a specific "What-If" run. |
| `step_time` | `DateTime` | The virtual time in the simulation. |
| `agent_id` | `UUID` | Which agent is acting. |
| `interacting_with_signal`| `UUID` | The post they are reading. |
| `action_taken` | `Enum` | `IGNORE`, `LIKE`, `SHARE`, `COMMENT`, `REPORT`. |
| `reasoning_trace` | `String` | **(Crucial)** The LLM's explanation: *"I shared this because I'm scared of losing my savings."* |
| `emotional_state_after`| `String` | `Fear`, `Anger`, `Relief`, `Neutral`. |
| `virality_velocity` | `Float` | The calculated rate of spread at this specific timestamp. |

---

### 5. Config: Risk Scenarios (`scenario_definitions.json`)
**Purpose:** Pre-packaged scenarios to launch demos quickly.

*   `scenario_name`: "Data Leak Rumor"
*   `inject_signal_id`: [Link to a specific fake news post]
*   `target_segment`: "All" or "SME_Owners"
*   `simulation_duration_hours`: 24
