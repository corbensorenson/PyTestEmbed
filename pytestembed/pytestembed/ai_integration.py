"""
AI Integration module for PyTestEmbed.

Provides integration with local AI models via Ollama and LMStudio
for test generation and documentation enhancement.
"""

import json
import requests
import os
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
# from .ai_context import create_contextualized_prompt  # Temporarily disabled due to import hook issues
from .config_manager import get_config_manager
from .error_handler import get_error_handler, with_error_recovery, NetworkError, AIError


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate a completion for the given prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI provider is available."""
        pass


class OllamaProvider(AIProvider):
    """Ollama AI provider for local model inference."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = requests.Session()
    
    @with_error_recovery(context="ollama_generation", recovery_strategy="network_timeout", default_return="")
    def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate completion using Ollama API with error recovery."""
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "max_tokens": kwargs.get("max_tokens", 1000)
                }
            }

            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Ollama request timed out: {e}")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Ollama connection failed: {e}")
        except requests.exceptions.RequestException as e:
            raise AIError(f"Ollama generation failed: {e}")
        except Exception as e:
            raise AIError(f"Ollama generation failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models in Ollama."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except:
            return []


class LMStudioProvider(AIProvider):
    """LMStudio AI provider for local model inference."""
    
    def __init__(self, base_url: str = "http://localhost:1234", model: str = "local-model"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = requests.Session()
    
    def generate_completion(self, prompt: str, **kwargs) -> str:
        """Generate completion using LMStudio OpenAI-compatible API."""
        try:
            url = f"{self.base_url}/v1/chat/completions"

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 500),  # Reduced for structured output
                "temperature": kwargs.get("temperature", 0.3),  # Lower for more consistent output
                "top_p": kwargs.get("top_p", 0.9),
                "stop": kwargs.get("stop", None)
            }

            # Add structured output if specified
            response_format = kwargs.get("response_format")
            if response_format:
                payload["response_format"] = response_format

            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return ""

        except Exception as e:
            raise AIProviderError(f"LMStudio generation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if LMStudio is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models in LMStudio."""
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except:
            return []


class AIProviderError(Exception):
    """Exception raised when AI provider operations fail."""
    pass


class AIManager:
    """Manager for AI providers and operations."""
    
    def __init__(self):
        self.providers = {}
        self.active_provider = None
        self.config_manager = get_config_manager()
        self._load_configuration()
    
    def _load_configuration(self):
        """Load AI configuration from config manager."""
        ai_config = self.config_manager.get_ai_provider_config()

        # Try to initialize Ollama
        ollama = OllamaProvider(ai_config.ollama_url, ai_config.ollama_model)
        if ollama.is_available():
            self.providers["ollama"] = ollama
            if not self.active_provider:
                self.active_provider = "ollama"

        # Try to initialize LMStudio
        lmstudio = LMStudioProvider(ai_config.lmstudio_url, ai_config.lmstudio_model)
        if lmstudio.is_available():
            self.providers["lmstudio"] = lmstudio
            if not self.active_provider:
                self.active_provider = "lmstudio"

        # Set the configured active provider
        if ai_config.provider in self.providers:
            self.active_provider = ai_config.provider
    
    def get_provider(self, provider_name: Optional[str] = None) -> Optional[AIProvider]:
        """Get AI provider by name or return active provider."""
        if provider_name:
            return self.providers.get(provider_name)
        
        if self.active_provider:
            return self.providers.get(self.active_provider)
        
        return None
    
    def set_active_provider(self, provider_name: str):
        """Set the active AI provider."""
        if provider_name in self.providers:
            self.active_provider = provider_name
        else:
            raise ValueError(f"Provider '{provider_name}' not available")
    
    def list_available_providers(self) -> List[str]:
        """List all available AI providers."""
        return list(self.providers.keys())
    
    def is_ai_available(self) -> bool:
        """Check if any AI provider is available."""
        return len(self.providers) > 0
    
    def generate_completion(self, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """Generate completion using specified or active provider."""
        ai_provider = self.get_provider(provider)
        if not ai_provider:
            raise AIProviderError("No AI provider available")

        return ai_provider.generate_completion(prompt, **kwargs)

    def generate_contextualized_completion(self, prompt: str, task_type: str = "general", provider: Optional[str] = None, **kwargs) -> str:
        """Generate completion with PyTestEmbed context prepended."""
        ai_provider = self.get_provider(provider)
        if not ai_provider:
            raise AIProviderError("No AI provider available")

        contextualized_prompt = create_contextualized_prompt(prompt, task_type)
        return ai_provider.generate_completion(contextualized_prompt, **kwargs)


# Global AI manager instance
ai_manager = AIManager()


def get_ai_manager() -> AIManager:
    """Get the global AI manager instance."""
    return ai_manager
