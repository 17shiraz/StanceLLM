# app/models/base_model.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseLLMModel(ABC):
    """Abstract base class for all LLM implementations"""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
        self.model_name = model_config.get('model_name', 'unknown')
        self.model_type = model_config.get('type', 'unknown')
        self.description = model_config.get('description', 'No description available')
        self.memory_requirement = model_config.get('memory_requirement', 0)
        self.context_length = model_config.get('context_length', 2048)
        self._is_loaded = False
        
        logger.info(f"Initializing {self.model_type} model: {self.model_name}")
    
    @abstractmethod
    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """
        Generate response from the model given user prompt and system prompt.
        
        Args:
            prompt: User input prompt
            system_prompt: System instruction prompt
            
        Returns:
            Generated response string
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if model is loaded and available for inference."""
        pass
    
    @abstractmethod
    def load_model(self) -> bool:
        """
        Load the model. Returns True if successful.
        
        Returns:
            Boolean indicating success/failure
        """
        pass
    
    def unload_model(self) -> bool:
        """
        Unload the model to free memory.
        
        Returns:
            Boolean indicating success/failure
        """
        try:
            self._is_loaded = False
            logger.info(f"Unloaded model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload model {self.model_name}: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": self.model_name,
            "type": self.model_type,
            "description": self.description,
            "memory_requirement": self.memory_requirement,
            "context_length": self.context_length,
            "is_loaded": self._is_loaded,
            "config": self.model_config
        }
    
    def validate_input(self, prompt: str, system_prompt: str) -> bool:
        """
        Validate input prompts.
        
        Args:
            prompt: User prompt to validate
            system_prompt: System prompt to validate
            
        Returns:
            Boolean indicating if inputs are valid
        """
        if not prompt or not isinstance(prompt, str):
            logger.warning("Invalid user prompt provided")
            return False
        
        if not system_prompt or not isinstance(system_prompt, str):
            logger.warning("Invalid system prompt provided")
            return False
        
        # Check combined length against context window
        total_length = len(prompt) + len(system_prompt)
        if total_length > self.context_length * 4:  # Rough token estimation
            logger.warning(f"Combined prompt length ({total_length}) may exceed context window")
            return False
        
        return True
