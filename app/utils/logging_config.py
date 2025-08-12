# app/utils/logging_config.py
import logging
import logging.config
import os
from pythonjsonlogger import jsonlogger
from ..config import Config

def setup_logging():
    """Setup structured logging configuration"""
    Config.create_directories()
    
    log_config = Config.get_log_config()
    logging.config.dictConfig(log_config)
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)