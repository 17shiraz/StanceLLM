from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import logging
import time
from contextlib import asynccontextmanager

from .models.model_factory import ModelFactory
from .prompts.system_prompts import STANCE_DETECTION_SYSTEM_PROMPT
from .prompts.prompt_templates import create_stance_prompt
from .utils.response_parser import StanceResponseParser
from .utils.logging_config import setup_logging
from .utils.health_checker import HealthChecker
from .middleware.error_handler import setup_error_handlers
from .middleware.metrics import MetricsCollector
from .config import Config

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global variables
current_model = None
health_checker = None
metrics_collector = MetricsCollector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global current_model, health_checker
    
    # Startup
    logger.info("Starting LLM Stance Detection API")
    try:
        # Initialize health checker
        health_checker = HealthChecker()
        
        # Load default model
        logger.info(f"Loading default model: {Config.DEFAULT_MODEL}")
        model_config = Config.AVAILABLE_MODELS[Config.DEFAULT_MODEL]
        current_model = ModelFactory.create_model(model_config["type"], model_config)
        
        if current_model.load_model():
            logger.info(f"Successfully loaded model: {Config.DEFAULT_MODEL}")
        else:
            logger.error(f"Failed to load default model: {Config.DEFAULT_MODEL}")
            current_model = None
            
        # Start health monitoring
        health_checker.start_monitoring()
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        yield
    
    # Shutdown
    logger.info("Shutting down LLM Stance Detection API")
    if health_checker:
        health_checker.stop_monitoring()

# Initialize FastAPI app
app = FastAPI(
    title="LLM Stance Detection API",
    description="Production-ready API for stance detection using large language models",
    version="1.0.0",
    lifespan=lifespan
)

# Setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)

# Pydantic models
class StanceRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze for stance")
    target: Optional[str] = Field(None, max_length=200, description="Target entity for stance detection")
    model_name: Optional[str] = Field(None, description="Specific model to use for this request")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Trump's policies will make America great again!",
                "target": "Donald Trump",
                "model_name": "llama2"
            }
        }

class StanceResponse(BaseModel):
    stance: str = Field(..., description="Detected stance: FAVOR, AGAINST, or NONE")
    reasoning: str = Field(..., description="Explanation for the stance classification")
    confidence: Optional[float] = Field(None, description="Confidence score (if available)")
    model_used: str = Field(..., description="Name of the model used for detection")
    target: str = Field(..., description="Target entity for stance detection")
    processing_time: float = Field(..., description="Time taken to process the request (seconds)")

class ModelSwitchRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to switch to")
    
    class Config:
        schema_extra = {
            "example": {
                "model_name": "mistral"
            }
        }

class HealthResponse(BaseModel):
    status: str
    current_model: Optional[str]
    available_models: List[str]
    uptime: float
    memory_usage: Dict[str, Any]
    system_info: Dict[str, Any]

class MetricsResponse(BaseModel):
    total_requests: int
    average_response_time: float
    error_rate: float
    model_usage: Dict[str, int]
    uptime: float

# Dependency for metrics collection
async def collect_metrics(request: Request):
    start_time = time.time()
    
    def record_metrics(response_status: int):
        processing_time = time.time() - start_time
        metrics_collector.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response_status,
            processing_time=processing_time,
            model_name=getattr(current_model, 'model_name', 'unknown') if current_model else 'none'
        )
    
    request.state.record_metrics = record_metrics
    return request

# API Endpoints
@app.post("/detect_stance", response_model=StanceResponse)
async def detect_stance(request: StanceRequest, req: Request):
    # Apply metrics collection manually
    req = await collect_metrics(req)
    """Detect stance in the provided text towards a target entity"""
    global current_model
    
    start_time = time.time()
    
    try:
        # Validate model availability
        if not current_model:
            raise HTTPException(status_code=503, detail="No model currently loaded")
        
        # Switch model if requested
        if request.model_name and request.model_name != current_model.model_name:
            if request.model_name not in Config.AVAILABLE_MODELS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Model '{request.model_name}' not available. Available models: {list(Config.AVAILABLE_MODELS.keys())}"
                )
            
            logger.info(f"Switching model from {current_model.model_name} to {request.model_name}")
            model_config = Config.AVAILABLE_MODELS[request.model_name]
            new_model = ModelFactory.create_model(model_config["type"], model_config)
            
            if not new_model.load_model():
                raise HTTPException(status_code=500, detail=f"Failed to load model: {request.model_name}")
            
            current_model = new_model
            logger.info(f"Successfully switched to model: {request.model_name}")
        
        # Use provided target or extract from context
        target = request.target or "the mentioned topic"
        
        # Create prompt
        user_prompt = create_stance_prompt(target, request.text)
        
        # Generate response
        logger.debug(f"Generating stance detection for text: {request.text[:100]}...")
        llm_response = current_model.generate_response(user_prompt, STANCE_DETECTION_SYSTEM_PROMPT)
        
        # Parse response
        stance, reasoning, confidence = StanceResponseParser.parse_stance_response(llm_response)
        
        processing_time = time.time() - start_time
        
        response = StanceResponse(
            stance=stance,
            reasoning=reasoning,
            confidence=confidence,
            model_used=current_model.model_name,
            target=target,
            processing_time=processing_time
        )
        
        # Record metrics
        req.state.record_metrics(200)
        
        logger.info(f"Stance detection completed: {stance} for target '{target}' in {processing_time:.2f}s")
        return response
        
    except HTTPException:
        req.state.record_metrics(400)
        raise
    except Exception as e:
        req.state.record_metrics(500)
        logger.error(f"Stance detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/switch_model")
async def switch_model(request: ModelSwitchRequest, req: Request):
    # Apply metrics collection manually
    req = await collect_metrics(req)
    """Switch to a different language model"""
    global current_model
    
    try:
        if request.model_name not in Config.AVAILABLE_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model_name}' not available. Available models: {list(Config.AVAILABLE_MODELS.keys())}"
            )
        
        if current_model and request.model_name == current_model.model_name:
            req.state.record_metrics(200)
            return {
                "message": f"Model '{request.model_name}' is already active",
                "current_model": request.model_name
            }
        
        logger.info(f"Switching to model: {request.model_name}")
        model_config = Config.AVAILABLE_MODELS[request.model_name]
        new_model = ModelFactory.create_model(model_config["type"], model_config)
        
        if not new_model.load_model():
            raise HTTPException(status_code=500, detail=f"Failed to load model: {request.model_name}")
        
        current_model = new_model
        req.state.record_metrics(200)
        
        logger.info(f"Successfully switched to model: {request.model_name}")
        return {
            "message": f"Successfully switched to {request.model_name}",
            "current_model": request.model_name
        }
        
    except HTTPException:
        req.state.record_metrics(400)
        raise
    except Exception as e:
        req.state.record_metrics(500)
        logger.error(f"Model switch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")

@app.get("/available_models")
async def list_available_models():
    """List all available models and their configurations"""
    return {
        "available_models": list(Config.AVAILABLE_MODELS.keys()),
        "current_model": current_model.model_name if current_model else None,
        "model_details": {
            name: {
                "type": config["type"],
                "description": config.get("description", "No description available")
            }
            for name, config in Config.AVAILABLE_MODELS.items()
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_data = health_checker.get_health_status() if health_checker else {}
        
        return HealthResponse(
            status="healthy" if current_model and current_model.is_available() else "unhealthy",
            current_model=current_model.model_name if current_model else None,
            available_models=list(Config.AVAILABLE_MODELS.keys()),
            uptime=health_data.get("uptime", 0),
            memory_usage=health_data.get("memory", {}),
            system_info=health_data.get("system", {})
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get API performance metrics"""
    try:
        metrics = metrics_collector.get_metrics()
        return MetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LLM Stance Detection API",
        "version": "1.0.0",
        "status": "operational",
        "current_model": current_model.model_name if current_model else None,
        "documentation": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.DEBUG,
        log_level="info"
    )