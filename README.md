# StanceLLM

A containerized stance detection API using large language models (LLMs) via Ollama and FastAPI.

## Overview

StanceLLM is a production-ready API for stance detection using large language models. It analyzes text to determine whether it expresses a FAVOR, AGAINST, or NONE stance toward a specified target entity or topic. The system uses Ollama to serve LLMs and provides a FastAPI interface for easy integration.

## Features

- Stance detection using state-of-the-art LLMs
- Multiple model support (llama2, mistral, codellama, phi3, dialoGPT)
- Docker containerization for easy deployment
- RESTful API with comprehensive documentation
- Health monitoring and metrics collection
- Model switching capability

## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/StanceLLM.git
cd StanceLLM
```

### 2. Start the Docker Containers

```bash
docker-compose up --build -d
```

This command builds the Docker images and starts the containers in detached mode. The first startup may take several minutes as Ollama downloads the LLM model.

### 3. Check Container Status

```bash
docker-compose ps
```

Wait until both containers show as running.

### 4. Verify the API is Working

```bash
# Linux/macOS
curl -X GET http://localhost:8000/health

# Windows PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health -Method GET | Select-Object -ExpandProperty Content
```

## Using the API

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/detect_stance` | POST | Detect stance in text toward a target |
| `/switch_model` | POST | Switch to a different LLM |
| `/available_models` | GET | List all available models |
| `/health` | GET | Check API health status |
| `/metrics` | GET | Get API performance metrics |
| `/` | GET | Root endpoint with API information |

### Swagger UI Documentation

Access the interactive API documentation at:
```
http://localhost:8000/docs
```

### Basic Usage Examples

#### 1. Detect Stance

**Using curl:**
```bash
curl -X 'POST' \
  'http://localhost:8000/detect_stance' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Climate change is a serious threat that requires immediate action.",
  "target": "Climate change"
}'
```

**Using PowerShell:**
```powershell
$body = @{
    text = "Climate change is a serious threat that requires immediate action."
    target = "Climate change"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/detect_stance -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

#### 2. Switch Model

**Using curl:**
```bash
curl -X 'POST' \
  'http://localhost:8000/switch_model' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model_name": "mistral"
}'
```

**Using PowerShell:**
```powershell
$body = @{
    model_name = "mistral"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/switch_model -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

#### 3. List Available Models

**Using curl:**
```bash
curl -X 'GET' 'http://localhost:8000/available_models' -H 'accept: application/json'
```

**Using PowerShell:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/available_models -Method GET | Select-Object -ExpandProperty Content
```

### Testing Your Own Tweets/Texts

To test your own tweets or texts, send a POST request to `/detect_stance` with your text and target:

```json
{
  "text": "Your tweet or text here.",
  "target": "Entity or topic here"
}
```

Example tweet formats to try:
- Political opinions: "I believe candidate X's policies will help the economy grow!"
- Product reviews: "This new phone is absolutely terrible, don't waste your money."
- Current events: "The recent changes to healthcare access are exactly what this country needed."
- Social issues: "Climate change policies are destroying jobs and hurting families."

The API will return one of three stance classifications:
- `FAVOR`: Supporting or positive toward the target
- `AGAINST`: Opposing or negative toward the target
- `NONE`: Neutral or no clear stance toward the target

## Stopping and Restarting the Application

### Stop the Application

```bash
docker-compose down
```

### Start the Application Again

```bash
docker-compose up -d
```

## Project Structure

```
StanceLLM/
├── app/                    # FastAPI application code
│   ├── models/             # LLM model implementations
│   ├── prompts/            # System prompts and templates
│   ├── utils/              # Utility functions
│   └── main.py             # FastAPI application entry point
├── config/                 # Configuration files
├── data/                   # Data files
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── requirements.txt        # Python dependencies
```