import os
from typing import Dict, Any
from pathlib import Path

class Config:
    """Configuration management for the LLM Stance Detection API"""
    
    # Environment
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = int(os.getenv("API_WORKERS", "1"))
    
    # Model Configuration
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama2")
    MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/app/models/cache")
    MAX_MODEL_MEMORY = int(os.getenv("MAX_MODEL_MEMORY", "8192"))  # MB
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    # Request Configuration
    MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", "5000"))  # characters
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))  # seconds
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    LOG_FILE = os.getenv("LOG_FILE", "/app/logs/app.log")
    
    # Monitoring Configuration
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_RETENTION_HOURS = int(os.getenv("METRICS_RETENTION_HOURS", "24"))
    
    # Security Configuration
    API_KEY = os.getenv("API_KEY", None)
    ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # seconds
    
    # Available Models Configuration
    AVAILABLE_MODELS = {
        "llama2": {
            "type": "ollama",
            "model_name": "llama2:7b",
            "base_url": OLLAMA_BASE_URL,
            "description": "Llama 2 7B - General purpose language model with good instruction following",
            "memory_requirement": 4096,  # MB
            "supported_languages": ["en"],
            "context_length": 4096
        },
        "mistral": {
            "type": "ollama", 
            "model_name": "mistral:7b",
            "base_url": OLLAMA_BASE_URL,
            "description": "Mistral 7B - Enhanced instruction following and reasoning capabilities",
            "memory_requirement": 4096,
            "supported_languages": ["en", "fr", "de", "es", "it"],
            "context_length": 8192
        },
        "codellama": {
            "type": "ollama",
            "model_name": "codellama:7b",
            "base_url": OLLAMA_BASE_URL,
            "description": "Code Llama 7B - Specialized for code understanding and structured output",
            "memory_requirement": 4096,
            "supported_languages": ["en"],
            "context_length": 16384
        },
        "phi3": {
            "type": "ollama",
            "model_name": "phi3:mini",
            "base_url": OLLAMA_BASE_URL,
            "description": "Phi-3 Mini - Lightweight model for resource-constrained environments",
            "memory_requirement": 2048,
            "supported_languages": ["en"],
            "context_length": 4096
        },
        "dialoGPT": {
            "type": "huggingface",
            "model_name": "microsoft/DialoGPT-medium",
            "description": "DialoGPT Medium - Conversational AI model",
            "memory_requirement": 3072,
            "supported_languages": ["en"],
            "context_length": 1024
        }
    }
    
    # SemEval 2016 Configuration
    SEMEVAL_DATA_PATH = os.getenv("SEMEVAL_DATA_PATH", "/app/data/semeval_examples")
    VALIDATION_SET_SIZE = int(os.getenv("VALIDATION_SET_SIZE", "100"))
    
    # Performance Configuration
    RESPONSE_CACHE_TTL = int(os.getenv("RESPONSE_CACHE_TTL", "300"))  # seconds
    ENABLE_RESPONSE_CACHE = os.getenv("ENABLE_RESPONSE_CACHE", "false").lower() == "true"
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        if model_name not in cls.AVAILABLE_MODELS:
            raise ValueError(f"Model '{model_name}' not found in available models")
        return cls.AVAILABLE_MODELS[model_name]
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Check required directories
        required_dirs = [cls.MODEL_CACHE_DIR, cls.SEMEVAL_DATA_PATH]
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {dir_path}: {e}")
        
        # Validate default model
        if cls.DEFAULT_MODEL not in cls.AVAILABLE_MODELS:
            errors.append(f"Default model '{cls.DEFAULT_MODEL}' not in available models")
        
        # Check memory requirements
        default_model_config = cls.AVAILABLE_MODELS.get(cls.DEFAULT_MODEL, {})
        if default_model_config.get("memory_requirement", 0) > cls.MAX_MODEL_MEMORY:
            errors.append(f"Default model requires more memory than available")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
    
    @classmethod
    def get_log_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                },
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json" if cls.LOG_FORMAT == "json" else "standard",
                    "level": cls.LOG_LEVEL
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": cls.LOG_FILE,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "formatter": "json" if cls.LOG_FORMAT == "json" else "standard",
                    "level": cls.LOG_LEVEL
                }
            },
            "root": {
                "level": cls.LOG_LEVEL,
                "handlers": ["console", "file"]
            }
        }
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        directories = [
            cls.MODEL_CACHE_DIR,
            cls.SEMEVAL_DATA_PATH,
            os.path.dirname(cls.LOG_FILE),
            "/app/data/test_cases"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)