# app/models/ollama_model.py
import requests
import logging
from typing import Dict, Any, Optional
from .base_model import BaseLLMModel

logger = logging.getLogger(__name__)

class OllamaModel(BaseLLMModel):
    """Ollama model implementation for local LLM hosting"""
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.base_url = model_config.get('base_url', 'http://localhost:11434')
        self.timeout = model_config.get('timeout', 120)
        self.temperature = model_config.get('temperature', 0.7)
        self.max_tokens = model_config.get('max_tokens', 512)
        
        # Ensure base_url doesn't end with slash
        self.base_url = self.base_url.rstrip('/')
        
        logger.info(f"Initialized Ollama model: {self.model_name} at {self.base_url}")
    
    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Ollama API"""
        if not self.validate_input(prompt, system_prompt):
            raise ValueError("Invalid input provided")
        
        if not self.is_available():
            raise RuntimeError(f"Ollama model {self.model_name} is not available")
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            logger.debug(f"Sending request to Ollama: {self.base_url}/api/generate")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "response" not in result:
                raise ValueError("Invalid response format from Ollama")
            
            generated_text = result["response"].strip()
            logger.debug(f"Generated response length: {len(generated_text)} characters")
            
            return generated_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            raise RuntimeError(f"Failed to communicate with Ollama: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama generation: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Ollama service and model are available"""
        try:
            # Check if Ollama service is running
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if specific model is available
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model["name"] for model in models_data.get("models", [])]
                return self.model_name in available_models
            
            return False
            
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False
    
    def load_model(self) -> bool:
        """Load model in Ollama (pull if necessary)"""
        try:
            # Check if model is already available
            if self.is_available():
                self._is_loaded = True
                logger.info(f"Model {self.model_name} already available")
                return True
            
            # Try to pull the model
            logger.info(f"Pulling model {self.model_name} from Ollama...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name},
                timeout=600  # Longer timeout for model downloads
            )
            
            if response.status_code == 200:
                self._is_loaded = True
                logger.info(f"Successfully loaded model: {self.model_name}")
                return True
            else:
                logger.error(f"Failed to pull model {self.model_name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load Ollama model {self.model_name}: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information from Ollama"""
        info = super().get_model_info()
        
        try:
            # Get additional info from Ollama
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model_name},
                timeout=10
            )
            
            if response.status_code == 200:
                ollama_info = response.json()
                info.update({
                    "ollama_info": {
                        "parameters": ollama_info.get("parameters", {}),
                        "template": ollama_info.get("template", ""),
                        "details": ollama_info.get("details", {})
                    }
                })
        except Exception as e:
            logger.debug(f"Could not fetch additional Ollama info: {e}")
        
        return info