# app/models/model_factory.py
import logging
from typing import Dict, Any
from .base_model import BaseLLMModel
from .ollama_model import OllamaModel
from .huggingface_model import HuggingFaceModel

logger = logging.getLogger(__name__)

class ModelFactory:
    """Factory class for creating different types of LLM models"""
    
    # Registry of available model types
    _model_registry = {
        'ollama': OllamaModel,
        'huggingface': HuggingFaceModel,
    }
    
    @classmethod
    def create_model(cls, model_type: str, model_config: Dict[str, Any]) -> BaseLLMModel:
        """
        Create a model instance based on the specified type.
        
        Args:
            model_type: Type of model to create ('ollama', 'huggingface')
            model_config: Configuration dictionary for the model
            
        Returns:
            Instance of the requested model type
            
        Raises:
            ValueError: If model type is not supported
        """
        model_type = model_type.lower().strip()
        
        if model_type not in cls._model_registry:
            available_types = list(cls._model_registry.keys())
            raise ValueError(
                f"Unsupported model type: {model_type}. "
                f"Available types: {available_types}"
            )
        
        model_class = cls._model_registry[model_type]
        
        try:
            logger.info(f"Creating {model_type} model with config: {model_config.get('model_name', 'unknown')}")
            model_instance = model_class(model_config)
            logger.info(f"Successfully created {model_type} model: {model_instance.model_name}")
            return model_instance
            
        except Exception as e:
            logger.error(f"Failed to create {model_type} model: {e}")
            raise RuntimeError(f"Model creation failed: {e}")
    
    @classmethod
    def register_model_type(cls, model_type: str, model_class: type) -> None:
        """
        Register a new model type.
        
        Args:
            model_type: Name of the model type
            model_class: Class implementing the model
        """
        if not issubclass(model_class, BaseLLMModel):
            raise ValueError(f"Model class must inherit from BaseLLMModel")
        
        cls._model_registry[model_type.lower()] = model_class
        logger.info(f"Registered new model type: {model_type}")
    
    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available model types."""
        return list(cls._model_registry.keys())
    
    @classmethod
    def validate_config(cls, model_type: str, model_config: Dict[str, Any]) -> bool:
        """
        Validate model configuration for a specific type.
        
        Args:
            model_type: Type of model
            model_config: Configuration to validate
            
        Returns:
            Boolean indicating if configuration is valid
        """
        model_type = model_type.lower().strip()
        
        if model_type not in cls._model_registry:
            logger.error(f"Unknown model type for validation: {model_type}")
            return False
        
        # Basic validation
        if not isinstance(model_config, dict):
            logger.error("Model config must be a dictionary")
            return False
        
        if 'model_name' not in model_config:
            logger.error("Model config must contain 'model_name'")
            return False
        
        # Type-specific validation
        if model_type == 'ollama':
            return cls._validate_ollama_config(model_config)
        elif model_type == 'huggingface':
            return cls._validate_huggingface_config(model_config)
        
        return True
    
    @classmethod
    def _validate_ollama_config(cls, config: Dict[str, Any]) -> bool:
        """Validate Ollama-specific configuration"""
        required_fields = ['model_name']
        optional_fields = ['base_url', 'timeout', 'temperature', 'max_tokens']
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required Ollama config field: {field}")
                return False
        
        # Validate base_url format if provided
        if 'base_url' in config:
            base_url = config['base_url']
            if not isinstance(base_url, str) or not base_url.startswith(('http://', 'https://')):
                logger.error("Invalid base_url format for Ollama config")
                return False
        
        return True
    
    @classmethod
    def _validate_huggingface_config(cls, config: Dict[str, Any]) -> bool:
        """Validate HuggingFace-specific configuration"""
        required_fields = ['model_name']
        optional_fields = ['device', 'max_length', 'temperature', 'do_sample', 'top_p']
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required HuggingFace config field: {field}")
                return False
        
        # Validate device format if provided
        if 'device' in config:
            device = config['device']
            valid_devices = ['cpu', 'cuda', 'auto']
            if device not in valid_devices and not device.startswith('cuda:'):
                logger.warning(f"Unusual device specified: {device}")
        
        return True