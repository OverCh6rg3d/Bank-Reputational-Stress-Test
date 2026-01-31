"""
Data loading utilities for the Reputational Stress-Test Simulator.

Loads and indexes all synthetic datasets:
- Social signals stream (CSV)
- Agent archetypes (CSV)
- Bank knowledge base (CSV → ChromaDB)
- Scenario definitions (JSON)
"""

import ast
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import chromadb
import pandas as pd

from backend.core.embedder import GitHubEmbedder, get_embedder

from ..models.schemas import (
    AgentArchetype,
    KnowledgeFact,
    PlatformSource,
    Scenario,
    SocialSignal,
)

logger = logging.getLogger(__name__)

# Default data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


class DataLoader:
    """
    Singleton-style data loader that caches loaded datasets.
    Provides efficient access to all synthetic data.
    """

    _instance: Optional["DataLoader"] = None
    _initialized: bool = False

    def __new__(cls) -> "DataLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data_dir: Optional[Path] = None):
        if self._initialized:
            return

        self.data_dir = data_dir or DATA_DIR
        self._signals: Optional[list[SocialSignal]] = None
        self._agents: Optional[list[AgentArchetype]] = None
        self._knowledge_base: Optional[list[KnowledgeFact]] = None
        self._scenarios: Optional[list[Scenario]] = None

        # Embedding model (lazy loaded) - uses GitHub Models API
        self._embedder: Optional[GitHubEmbedder] = None

        # ChromaDB for knowledge base RAG
        self._chroma_client: Optional[chromadb.Client] = None
        self._kb_collection: Optional[chromadb.Collection] = None

        self._initialized = True
        logger.info(f"DataLoader initialized with data_dir: {self.data_dir}")

    @property
    def embedder(self) -> Optional[GitHubEmbedder]:
        """Lazy-load the GitHub Models embedder with graceful fallback."""
        if self._embedder is None:
            try:
                logger.info("Initializing GitHub Models embedder...")
                self._embedder = get_embedder()
                if self._embedder is None:
                    logger.warning("GITHUB_TOKEN not set. RAG features will be disabled.")
            except Exception as e:
                logger.warning(f"Failed to initialize embedder: {e}")
                logger.warning("RAG features will be disabled.")
                return None
        return self._embedder

    def _parse_list_field(self, value: str) -> list[str]:
        """Parse a string representation of a list."""
        if pd.isna(value) or value == "" or value == "[]":
            return []
        try:
            # Try literal eval first (handles Python list syntax)
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except (ValueError, SyntaxError):
            # Fall back to comma-separated
            return [v.strip() for v in value.split(",") if v.strip()]

    def load_signals(self, limit: Optional[int] = None) -> list[SocialSignal]:
        """Load social signals from CSV."""
        if self._signals is not None and limit is None:
            return self._signals

        signals_path = self.data_dir / "social_signals_stream.csv"
        logger.info(f"Loading signals from {signals_path}")

        df = pd.read_csv(signals_path, nrows=limit)
        signals = []

        for _, row in df.iterrows():
            try:
                # Handle media_type NaN values
                media_type_val = row.get("media_type")
                if pd.isna(media_type_val):
                    media_type_val = "None"
                
                signal = SocialSignal(
                    signal_id=UUID(row["signal_id"]),
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    platform_source=PlatformSource(row["platform_source"]),
                    author_id=UUID(row["author_id"]) if pd.notna(row.get("author_id")) else None,
                    content_text=row["content_text"],
                    parent_id=UUID(row["parent_id"]) if pd.notna(row.get("parent_id")) else None,
                    thread_id=UUID(row["thread_id"]),
                    media_type=media_type_val,
                    language=row.get("language", "en") if pd.notna(row.get("language")) else "en",
                    hashtags=self._parse_list_field(row.get("hashtags", "[]")),
                    mentions=self._parse_list_field(row.get("mentions", "[]")),
                    gt_category=row["gt_category"],
                    gt_sentiment=float(row["gt_sentiment"]),
                    gt_is_misinformation=bool(row.get("gt_is_misinformation", False)),
                    gt_virality_potential=int(row["gt_virality_potential"]),
                )
                signals.append(signal)
            except Exception as e:
                logger.warning(f"Failed to parse signal row: {e}")
                continue

        if limit is None:
            self._signals = signals

        logger.info(f"Loaded {len(signals)} signals")
        return signals

    def load_agents(self) -> list[AgentArchetype]:
        """Load agent archetypes from CSV."""
        if self._agents is not None:
            return self._agents

        agents_path = self.data_dir / "agent_archetypes.csv"
        logger.info(f"Loading agents from {agents_path}")

        df = pd.read_csv(agents_path)
        agents = []

        for _, row in df.iterrows():
            try:
                agent = AgentArchetype(
                    agent_id=UUID(row["agent_id"]),
                    archetype_name=row["archetype_name"],
                    demographic_segment=row["demographic_segment"],
                    financial_literacy=int(row["financial_literacy"]),
                    brand_loyalty=int(row["brand_loyalty"]),
                    skepticism_score=int(row["skepticism_score"]),
                    network_influence=int(row["network_influence"]),
                    activity_frequency=float(row["activity_frequency"]),
                    preferred_platform=PlatformSource(row["preferred_platform"]),
                    core_values=self._parse_list_field(row.get("core_values", "[]")),
                    persona_description=row.get("persona_description", ""),
                    behavioral_pattern=row.get("behavioral_pattern", ""),
                )
                agents.append(agent)
            except Exception as e:
                logger.warning(f"Failed to parse agent row: {e}")
                continue

        self._agents = agents
        logger.info(f"Loaded {len(agents)} agent archetypes")
        return agents

    def load_knowledge_base(self) -> list[KnowledgeFact]:
        """Load knowledge base from CSV."""
        if self._knowledge_base is not None:
            return self._knowledge_base

        kb_path = self.data_dir / "bank_knowledge_base.csv"
        logger.info(f"Loading knowledge base from {kb_path}")

        df = pd.read_csv(kb_path)
        facts = []

        for _, row in df.iterrows():
            try:
                fact = KnowledgeFact(
                    kb_id=UUID(row["kb_id"]),
                    topic_area=row["topic_area"],
                    fact_statement=row["fact_statement"],
                    public_url=row["public_url"],
                    last_updated=datetime.fromisoformat(row["last_updated"]),
                    keywords=self._parse_list_field(row.get("keywords", "[]")),
                )
                facts.append(fact)
            except Exception as e:
                logger.warning(f"Failed to parse knowledge row: {e}")
                continue

        self._knowledge_base = facts
        logger.info(f"Loaded {len(facts)} knowledge facts")
        return facts

    def load_scenarios(self) -> list[Scenario]:
        """Load scenario definitions from JSON."""
        if self._scenarios is not None:
            return self._scenarios

        scenarios_path = self.data_dir / "scenario_definitions.json"
        logger.info(f"Loading scenarios from {scenarios_path}")

        with open(scenarios_path, "r") as f:
            data = json.load(f)

        scenarios = []
        for item in data:
            try:
                scenario = Scenario(
                    scenario_id=UUID(item["scenario_id"]),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    scenario_name=item["scenario_name"],
                    description=item["description"],
                    trigger_category=item["trigger_category"],
                    target_segment=item["target_segment"],
                    simulation_duration_hours=item["simulation_duration_hours"],
                    severity_level=item["severity_level"],
                    expected_velocity_peak=item["expected_velocity_peak"],
                    recommended_response_time_hours=item["recommended_response_time_hours"],
                    key_narratives=item.get("key_narratives", []),
                    monitoring_keywords=item.get("monitoring_keywords", []),
                    potential_impact=item.get("potential_impact", {}),
                )
                scenarios.append(scenario)
            except Exception as e:
                logger.warning(f"Failed to parse scenario: {e}")
                continue

        self._scenarios = scenarios
        logger.info(f"Loaded {len(scenarios)} scenarios")
        return scenarios

    def get_scenario_by_id(self, scenario_id: UUID) -> Optional[Scenario]:
        """Get a specific scenario by ID."""
        scenarios = self.load_scenarios()
        for scenario in scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        return None

    def get_scenario_by_name(self, name: str) -> Optional[Scenario]:
        """Get a scenario by name (case-insensitive partial match)."""
        scenarios = self.load_scenarios()
        name_lower = name.lower()
        for scenario in scenarios:
            if name_lower in scenario.scenario_name.lower():
                return scenario
        return None

    def get_signals_for_scenario(
        self, scenario: Scenario, limit: int = 100
    ) -> list[SocialSignal]:
        """
        Get signals relevant to a scenario based on trigger category
        and monitoring keywords.
        """
        all_signals = self.load_signals()
        
        # Filter by category
        category_signals = [
            s for s in all_signals
            if s.gt_category == scenario.trigger_category
        ]

        # Sort by virality potential (most viral first)
        category_signals.sort(key=lambda s: s.gt_virality_potential, reverse=True)

        return category_signals[:limit]

    def init_knowledge_base_rag(self) -> chromadb.Collection:
        """
        Initialize ChromaDB collection with embedded knowledge facts.
        This enables RAG-based fact-checking.
        """
        if self._kb_collection is not None:
            return self._kb_collection

        logger.info("Initializing ChromaDB for knowledge base RAG...")
        
        # Create in-memory client
        self._chroma_client = chromadb.Client()
        
        # Create or get collection
        self._kb_collection = self._chroma_client.get_or_create_collection(
            name="bank_knowledge_base",
            metadata={"description": "Official bank facts for fact-checking"}
        )

        # Load and embed knowledge facts
        facts = self.load_knowledge_base()
        
        if self._kb_collection.count() == 0:
            logger.info(f"Embedding {len(facts)} knowledge facts...")
            
            documents = [fact.fact_statement for fact in facts]
            ids = [str(fact.kb_id) for fact in facts]
            metadatas = [
                {"topic_area": fact.topic_area, "url": fact.public_url}
                for fact in facts
            ]
            
            # Generate embeddings
            embeddings = self.embedder.encode(documents)
            
            self._kb_collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas,
            )
            
            logger.info("Knowledge base indexed in ChromaDB")

        return self._kb_collection

    def query_knowledge_base(
        self, query: str, n_results: int = 5
    ) -> list[dict]:
        """
        Query the knowledge base for facts relevant to a claim.
        Returns matched facts with relevance scores.
        """
        if self.embedder is None:
            # Fallback: return all facts without similarity scoring
            facts = self.load_knowledge_base()
            return [
                {"fact": f.fact_statement, "topic": f.topic_area, "url": f.public_url, "relevance": 0.5}
                for f in facts[:n_results]
            ]
        
        collection = self.init_knowledge_base_rag()
        if collection is None:
            return []
        
        # Embed query
        query_embedding = self.embedder.encode([query])
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        facts = []
        for i, doc in enumerate(results["documents"][0]):
            facts.append({
                "fact": doc,
                "topic": results["metadatas"][0][i]["topic_area"],
                "url": results["metadatas"][0][i]["url"],
                "distance": results["distances"][0][i],
                "relevance": 1 - results["distances"][0][i],
            })

        return facts

    def embed_signals(self, signals: list[SocialSignal]) -> list[list[float]]:
        """Generate embeddings for a list of signals."""
        texts = [s.content_text for s in signals]
        embeddings = self.embedder.encode(texts)
        return embeddings


# Convenience function
def get_data_loader(data_dir: Optional[Path] = None) -> DataLoader:
    """Get the singleton DataLoader instance."""
    loader = DataLoader.__new__(DataLoader)
    loader.__init__(data_dir)
    return loader
