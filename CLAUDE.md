# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready LegalTech AI application designed for the Red Hat Hackathon, providing document analysis and intelligent chat functionality using IBM watsonx.ai. The application is containerized and optimized for OpenShift deployment with comprehensive monitoring, logging, and health checks.

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run locally
python -m legaltech_ai.main

# Run tests (when available)
pytest tests/

# Modern linting and formatting
ruff check src/
ruff format src/

# Traditional formatting (also available)
black src/
flake8 src/
```

### Production/OpenShift Deployment
```bash
# Build container
docker build -t legaltech-ai:latest .

# Deploy to OpenShift
cd openshift/
./deploy.sh

# Check deployment status
oc get pods -l app=legaltech-ai
oc logs -f deployment/legaltech-ai
```

### Health Monitoring
```bash
# Health endpoints (when deployed)
curl https://your-route/_health    # Comprehensive health + watsonx.ai status
curl https://your-route/_ready     # Readiness probe  
curl https://your-route/_live      # Liveness probe
```

## Architecture

### Production Structure

The application follows a modular, production-ready architecture:

```
src/legaltech_ai/
├── config/           # Configuration management
│   ├── settings.py   # Environment variables and config classes
│   └── logging.py    # Centralized logging configuration
├── services/         # Business logic services
│   └── watsonx_service.py # IBM watsonx.ai integration
├── utils/           # Utility modules
│   └── document_processor.py # Document text extraction
├── ui/              # User interface
│   └── streamlit_app.py # Main Streamlit application
├── health.py        # Health monitoring system
├── health_server.py # HTTP health endpoints
└── main.py          # Application entry point
```

### Key Components

**Configuration Management** (`config/`):
- Environment-based configuration with fallbacks
- Separate watsonx.ai and application configs
- Production-ready logging setup with structured output
- Support for OpenShift ConfigMaps and Secrets

**Service Layer** (`services/watsonx_service.py`):
- Production-ready IBM watsonx.ai service with comprehensive error handling
- Separate methods for compliance analysis and document summarization
- Intelligent Q&A functionality using advanced prompting
- Built-in health checks and connection monitoring
- IBM Cloud IAM authentication with automatic token refresh

**Document Processing** (`utils/document_processor.py`):
- Multi-format support (PDF, DOCX, TXT) with graceful degradation
- File size validation and security checks
- Comprehensive error handling and logging
- Optional dependency management

**Health Monitoring** (`health.py`, `health_server.py`):
- Background health checking with configurable intervals
- Kubernetes-compatible health endpoints (/_health, /_ready, /_live)
- Comprehensive status reporting including watsonx.ai connectivity
- Separate HTTP server for health probes

### OpenShift Integration

**Container** (Red Hat UBI8-based):
- Multi-stage build for optimized image size
- Non-root user for security compliance
- Health checks integrated at container level
- Production environment variables

**Kubernetes Resources**:
- Deployment with 2 replicas and resource limits
- Service and Route for external access
- ConfigMap for non-sensitive configuration
- Secret template for watsonx.ai credentials
- BuildConfig for automated CI/CD

**Monitoring & Observability**:
- Structured logging with appropriate levels
- Health check endpoints for OpenShift probes
- Background watsonx.ai connectivity monitoring
- Resource usage tracking and limits

### Environment Variables

Required for production deployment:

**IBM watsonx.ai Configuration**:
- `WATSONX_API_KEY`, `WATSONX_URL`, `WATSONX_PROJECT_ID`
- `MODEL_ID` (default: meta-llama/llama-3-3-70b-instruct)
- `USE_LOGPROBS`, `TOP_N_TOKENS`
- Alternative names: `IBM_API_KEY`, `WX_CLOUD_URL`, `WX_PROJECT_ID`

**Application Configuration**:
- `PORT` (default: 8080), `HOST` (default: 0.0.0.0)
- `LOG_LEVEL` (default: INFO), `DEBUG` (default: false)
- `MAX_FILE_SIZE_MB` (default: 10)

### Security Features

- Non-root container execution
- Secret management via OpenShift Secrets
- Input validation and file size limits
- Secure error handling without information leakage
- HTTPS termination at route level