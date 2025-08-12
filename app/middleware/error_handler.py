# app/middleware/error_handler.py
import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

def setup_error_handlers(app: FastAPI):
    """Setup global error handlers for the FastAPI application"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP {exc.status_code} error at {request.url}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.warning(f"Starlette HTTP {exc.status_code} error at {request.url}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error at {request.url}: {exc}")
        
        # Format validation errors
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "status_code": 422,
                "message": "Request validation failed",
                "details": errors,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle value errors"""
        logger.error(f"Value error at {request.url}: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Value Error",
                "status_code": 400,
                "message": str(exc),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(f"Unhandled exception at {request.url}: {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "status_code": 500,
                "message": "An unexpected error occurred",
                "path": str(request.url.path),
                "type": type(exc).__name__
            }
        )