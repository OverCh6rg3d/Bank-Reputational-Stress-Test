"""
GitHub Models Embedder - Uses OpenAI-compatible API for embeddings.

This module provides embeddings using GitHub's model inference API,
which offers access to OpenAI's text-embedding-3-large model.
"""

import os
import time
import threading
import logging
from collections import deque
from typing import Optional, Union

from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)

# GitHub Models API configuration
GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference"
DEFAULT_MODEL = "openai/text-embedding-3-large"


class RateLimiter:
    """
    Rate limiter for API requests with:
    - Requests per minute limit
    - Maximum concurrent requests
    - Token per request limit
    """
    
    def __init__(
        self,
        requests_per_minute: int = 15,
        max_concurrent: int = 5,
        max_tokens_per_request: int = 64000
    ):
        self.requests_per_minute = requests_per_minute
        self.max_concurrent = max_concurrent
        self.max_tokens_per_request = max_tokens_per_request
        
        self.request_times = deque()
        self.active_requests = 0
        self.lock = threading.Lock()
        
        # Try to use tiktoken for accurate token counting
        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            logger.warning("tiktoken not installed, using approximate token counting")
            self.encoder = None
    
    def estimate_tokens(self, text: str) -> int:
        """Count tokens using tiktoken with fallback."""
        if self.encoder:
            try:
                return len(self.encoder.encode(text))
            except Exception:
                pass
        # Fallback to approximate count (1 token ≈ 4 chars)
        return len(text) // 4
    
    def wait_if_needed(self, texts: list[str]) -> None:
        """Block until rate limits allow the request."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Check token limit
        total_tokens = sum(self.estimate_tokens(t) for t in texts)
        if total_tokens > self.max_tokens_per_request:
            raise ValueError(
                f"Request exceeds token limit: {total_tokens} > {self.max_tokens_per_request}"
            )
        
        while True:
            with self.lock:
                now = time.time()
                
                # Remove requests older than 1 minute
                while self.request_times and now - self.request_times[0] > 60:
                    self.request_times.popleft()
                
                # Check if we can proceed
                if (len(self.request_times) < self.requests_per_minute and 
                    self.active_requests < self.max_concurrent):
                    self.request_times.append(now)
                    self.active_requests += 1
                    return
            
            # Wait a bit before retrying
            time.sleep(0.1)
    
    def release(self) -> None:
        """Release a concurrent request slot."""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)


class GitHubEmbedder:
    """
    Embedding helper using GitHub Models API (OpenAI-compatible).
    
    Uses the text-embedding-3-large model which produces 3072-dimensional embeddings.
    Includes rate limiting and token management.
    
    Usage:
        embedder = GitHubEmbedder()
        embeddings = embedder.embed("single string")    # returns [[float,...]]
        embeddings = embedder.embed(["one", "two"])     # returns [[...], [...]]
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_per_minute: int = 15,
        max_concurrent: int = 5,
        max_tokens_per_request: int = 64000
    ):
        self.api_key = api_key or os.getenv("GITHUB_TOKEN")
        if not self.api_key:
            raise ValueError(
                "GITHUB_TOKEN required. Set it in .env or pass api_key parameter."
            )
        
        self.base_url = GITHUB_MODELS_ENDPOINT
        self.model_name = DEFAULT_MODEL
        
        # Sync client
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        
        # Async client for batch operations
        self._async_client: Optional[AsyncOpenAI] = None
        
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            max_concurrent=max_concurrent,
            max_tokens_per_request=max_tokens_per_request
        )
        
        logger.info(f"GitHubEmbedder initialized with model: {self.model_name}")

    @property
    def async_client(self) -> AsyncOpenAI:
        """Lazy initialization of async client."""
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        return self._async_client

    def embed(self, texts: Union[str, list[str]]) -> list[list[float]]:
        """
        Embed a single string or a list of strings.
        
        Args:
            texts: Single string or list of strings to embed
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        if isinstance(texts, str):
            inputs = [texts]
        elif isinstance(texts, (list, tuple)):
            inputs = list(texts)
        else:
            raise TypeError("texts must be a str or a list/tuple of str")

        # Wait for rate limit clearance
        self.rate_limiter.wait_if_needed(inputs)
        
        try:
            resp = self.client.embeddings.create(
                input=inputs,
                model=self.model_name
            )
            return [item.embedding for item in resp.data]
        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            raise
        finally:
            self.rate_limiter.release()

    async def async_embed(self, texts: Union[str, list[str]]) -> list[list[float]]:
        """
        Async version of embed for use in async contexts.
        """
        if isinstance(texts, str):
            inputs = [texts]
        elif isinstance(texts, (list, tuple)):
            inputs = list(texts)
        else:
            raise TypeError("texts must be a str or a list/tuple of str")

        # Wait for rate limit clearance (blocking, but brief)
        self.rate_limiter.wait_if_needed(inputs)
        
        try:
            resp = await self.async_client.embeddings.create(
                input=inputs,
                model=self.model_name
            )
            return [item.embedding for item in resp.data]
        except Exception as e:
            logger.error(f"Async embedding request failed: {e}")
            raise
        finally:
            self.rate_limiter.release()

    def encode(self, texts: Union[str, list[str]]) -> list[list[float]]:
        """
        Alias for embed() to match sentence-transformers API.
        
        This allows drop-in replacement of SentenceTransformer.
        """
        return self.embed(texts)


# Singleton instance for convenience
_embedder_instance: Optional[GitHubEmbedder] = None


def get_embedder() -> Optional[GitHubEmbedder]:
    """
    Get or create the singleton GitHubEmbedder instance.
    
    Returns None if GITHUB_TOKEN is not set.
    """
    global _embedder_instance
    
    if _embedder_instance is not None:
        return _embedder_instance
    
    try:
        _embedder_instance = GitHubEmbedder()
        return _embedder_instance
    except ValueError as e:
        logger.warning(f"Could not initialize embedder: {e}")
        return None
