"""
PyTestEmbed Configuration Manager

Handles loading, saving, and managing configuration settings for PyTestEmbed.
Stores settings in a local JSON file and provides defaults.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AIProviderConfig:
    """Configuration for AI providers."""
    provider: str = "lmstudio"  # "ollama" or "lmstudio"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "codellama"
    lmstudio_url: str = "http://localhost:1234"
    lmstudio_model: str = "local-model"
    temperature: float = 0.3
    max_tokens: int = 1000
    no_think: bool = True  # Add /no_think to prompts to disable reasoning


@dataclass
class PyTestEmbedConfig:
    """Main PyTestEmbed configuration."""
    # AI Settings
    ai_provider: AIProviderConfig
    
    # General Settings
    cache_enabled: bool = True
    cache_dir: str = ".pytestembed_cache"
    temp_dir: str = ".pytestembed_temp"
    verbose: bool = False
    test_timeout: int = 30
    auto_generate_tests: bool = True
    auto_generate_docs: bool = True
    live_testing: bool = True
    
    # IDE Settings
    vscode_integration: bool = True
    pycharm_integration: bool = True
    live_server_port: int = 8765
    python_interpreter: str = "python"  # Path to Python interpreter for live testing

    # MCP Server Settings
    mcp_server_enabled: bool = False
    mcp_server_port: int = 3001
    auto_start_mcp_server: bool = False
    
    # Custom Prompts
    test_generation_prompt: str = ""
    doc_generation_prompt: str = ""
    conversion_prompt: str = ""
    unified_docs_prompt: str = ""


class ConfigManager:
    """Manages PyTestEmbed configuration settings."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".pytestembed"
        self.config_file = self.config_dir / "config.json"
        self.config: PyTestEmbedConfig = self._load_config()
    
    def _get_default_config(self) -> PyTestEmbedConfig:
        """Get default configuration."""
        return PyTestEmbedConfig(
            ai_provider=AIProviderConfig(),
            test_generation_prompt=self._get_default_test_prompt(),
            doc_generation_prompt=self._get_default_doc_prompt(),
            conversion_prompt=self._get_default_conversion_prompt(),
            unified_docs_prompt=self._get_default_unified_docs_prompt()
        )
    
    def _get_default_test_prompt(self) -> str:
        """Get default test generation prompt."""
        return """Generate comprehensive test cases for this function.

Function: {function_name}
Parameters: {parameters}
Return Type: {return_type}

Source Code:
{source_code}

Generate {test_count} test cases covering:
1. Normal operation with typical inputs
2. Edge cases and boundary conditions  
3. Error conditions when applicable

Use realistic test data and clear descriptions."""
    
    def _get_default_doc_prompt(self) -> str:
        """Get default documentation generation prompt."""
        return """Generate clear documentation for this function.

Function: {function_name}
Parameters: {parameters}
Return Type: {return_type}

Source Code:
{source_code}

Generate comprehensive documentation including:
1. Clear description of what the function does
2. Parameter descriptions with types
3. Return value explanation
4. Exception documentation if applicable
5. Usage examples for complex functions"""
    
    def _get_default_conversion_prompt(self) -> str:
        """Get default conversion prompt."""
        return """Convert this Python code to PyTestEmbed format.

Add appropriate test: and doc: blocks to all functions and methods.
Preserve original functionality while adding comprehensive tests and documentation.

Source Code:
{source_code}

Generate both test and documentation blocks following PyTestEmbed syntax."""
    
    def _get_default_unified_docs_prompt(self) -> str:
        """Get default unified documentation prompt."""
        return """Generate unified documentation for this module.

Module: {module_name}
Functions: {function_list}

Create comprehensive module documentation including:
1. Module overview and purpose
2. Function summaries
3. Usage examples
4. API reference
5. Best practices"""
    
    def _load_config(self) -> PyTestEmbedConfig:
        """Load configuration from file or create default."""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            # Convert dict to config object
            ai_config = AIProviderConfig(**data.get('ai_provider', {}))
            
            config_data = data.copy()
            config_data['ai_provider'] = ai_config
            
            # Handle missing fields with defaults
            default_config = self._get_default_config()
            for field, default_value in asdict(default_config).items():
                if field not in config_data:
                    config_data[field] = default_value
            
            return PyTestEmbedConfig(**config_data)
            
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)
            
            # Convert config to dict
            config_dict = asdict(self.config)
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_ai_provider_config(self) -> AIProviderConfig:
        """Get AI provider configuration."""
        return self.config.ai_provider
    
    def set_ai_provider(self, provider: str, **kwargs):
        """Set AI provider and update configuration."""
        self.config.ai_provider.provider = provider
        
        for key, value in kwargs.items():
            if hasattr(self.config.ai_provider, key):
                setattr(self.config.ai_provider, key, value)
    
    def get_custom_prompt(self, prompt_type: str) -> str:
        """Get custom prompt for a specific type."""
        prompt_map = {
            "test_generation": self.config.test_generation_prompt,
            "doc_generation": self.config.doc_generation_prompt,
            "conversion": self.config.conversion_prompt,
            "unified_docs": self.config.unified_docs_prompt
        }
        return prompt_map.get(prompt_type, "")
    
    def set_custom_prompt(self, prompt_type: str, prompt: str):
        """Set custom prompt for a specific type."""
        if prompt_type == "test_generation":
            self.config.test_generation_prompt = prompt
        elif prompt_type == "doc_generation":
            self.config.doc_generation_prompt = prompt
        elif prompt_type == "conversion":
            self.config.conversion_prompt = prompt
        elif prompt_type == "unified_docs":
            self.config.unified_docs_prompt = prompt
    
    def get_available_models(self, provider: str) -> list:
        """Get available models for a provider."""
        if provider == "ollama":
            return self._get_ollama_models()
        elif provider == "lmstudio":
            return self._get_lmstudio_models()
        return []
    
    def _get_ollama_models(self) -> list:
        """Get available Ollama models."""
        try:
            import requests
            url = f"{self.config.ai_provider.ollama_url}/api/tags"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except Exception:
            pass
        
        # Default models if API call fails
        return ["codellama", "llama2", "mistral", "qwen", "deepseek-coder"]
    
    def _get_lmstudio_models(self) -> list:
        """Get available LMStudio models."""
        try:
            import requests
            url = f"{self.config.ai_provider.lmstudio_url}/v1/models"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['id'] for model in data.get('data', [])]
        except Exception:
            pass
        
        # Default models if API call fails
        return ["local-model", "qwen-14b", "codellama-7b", "mistral-7b"]
    
    def test_ai_connection(self, provider: str = None) -> tuple[bool, str]:
        """Test connection to AI provider."""
        if provider is None:
            provider = self.config.ai_provider.provider
        
        try:
            import requests
            
            if provider == "ollama":
                url = f"{self.config.ai_provider.ollama_url}/api/tags"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True, "Ollama connection successful"
                else:
                    return False, f"Ollama returned status {response.status_code}"
            
            elif provider == "lmstudio":
                url = f"{self.config.ai_provider.lmstudio_url}/v1/models"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True, "LMStudio connection successful"
                else:
                    return False, f"LMStudio returned status {response.status_code}"
            
            return False, f"Unknown provider: {provider}"
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self.config = self._get_default_config()
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a file."""
        try:
            config_dict = asdict(self.config)
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            return True
        except Exception:
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            ai_config = AIProviderConfig(**data.get('ai_provider', {}))
            data['ai_provider'] = ai_config
            
            self.config = PyTestEmbedConfig(**data)
            return True
        except Exception:
            return False


# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
