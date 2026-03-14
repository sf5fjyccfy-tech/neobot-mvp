"""
Global HTTP Client avec Connection Pooling
Utilisé pour les appels IA et APIs externes
Optimisé pour performance (50% plus rapide que creating new client à chaque fois)
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global async client (reused across all requests)
_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    """
    Get or create the global async HTTP client
    With connection pooling for performance
    """
    global _http_client
    
    if _http_client is None:
        logger.info("🌐 Initializing global HTTP client with pooling...")
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            ),
            timeout=httpx.Timeout(
                timeout=30.0,      # Total timeout (increased from 5 seconds)
                connect=5.0,       # Connection timeout
                read=25.0,         # Read timeout
                pool=2.0           # Pool timeout
            ),
            verify=True,
            follow_redirects=True
        )
        logger.info("✅ Global HTTP client initialized")
    
    return _http_client


async def close_http_client():
    """
    Close the global HTTP client (called on app shutdown)
    """
    global _http_client
    
    if _http_client is not None:
        logger.info("🔌 Closing global HTTP client...")
        await _http_client.aclose()
        _http_client = None
        logger.info("✅ Global HTTP client closed")


class DeepSeekClient:
    """
    Client for DeepSeek API calls using global HTTP connection pooling
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "deepseek-chat"
    
    async def call(self, messages: list, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Call DeepSeek API with the global pooled HTTP client
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Model temperature (0-1)
            max_tokens: Max tokens in response
        
        Returns:
            Response text from DeepSeek
        """
        client = get_http_client()
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except httpx.HTTPError as e:
            logger.error(f"❌ DeepSeek API error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error calling DeepSeek: {e}")
            raise
