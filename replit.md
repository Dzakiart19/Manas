# AI-Manus - AI Agent Platform

## Overview
AI-Manus is an AI agent platform migrated from https://github.com/Simpleyyt/ai-manus. It provides an AI-powered assistant that can execute commands, manage files, and browse the web through a sandbox environment.

## Architecture
- **Frontend**: Vue.js 3 + Vite + TypeScript (port 5000)
- **Backend**: Python FastAPI (port 8000)
- **Sandbox**: Python FastAPI service for shell/file operations (port 8080)
- **Database**: MongoDB (external - MongoDB Atlas)
- **Cache/Queue**: Redis (external)

## Project Structure
```
/
├── frontend/          # Vue.js frontend app
├── backend/           # FastAPI backend API
│   └── app/
│       ├── main.py
│       ├── core/config.py
│       ├── domain/         # Domain models and interfaces
│       ├── infrastructure/ # External service implementations
│       └── interfaces/     # API routes and dependencies
├── sandbox/           # Sandbox service for command execution
│   └── app/
│       ├── main.py
│       ├── services/       # Shell, file, supervisor services
│       └── api/            # API routes
└── replit.md
```

## Workflows
- **Frontend**: `cd frontend && npx vite --host 0.0.0.0 --port 5000` (webview, port 5000)
- **Backend API**: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (console, port 8000)
- **Sandbox Service**: `cd sandbox && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080` (console, port 8080)

## Key Modifications from Original
- Docker dependency removed from backend sandbox client
- Supervisor service mocked for local operation (no Docker/supervisord)
- Frontend configured to run on port 5000 with proxy to backend on port 8000
- Environment variables managed through Replit secrets system

## Required Secrets
- `API_KEY`: LLM API key (OpenAI or compatible)
- `MONGODB_URI`: MongoDB connection string (e.g., MongoDB Atlas)
- `REDIS_HOST`: Redis host
- `REDIS_PASSWORD`: Redis password
- `JWT_SECRET_KEY`: JWT secret for authentication

## Environment Variables (configured)
- `API_BASE`: LLM API base URL
- `MODEL_NAME`: LLM model name
- `SANDBOX_ADDRESS`: localhost (local sandbox)
- `AUTH_PROVIDER`: local (default admin login)
- `BACKEND_URL`: http://localhost:8000

## Recent Changes
- 2026-02-22: Initial migration from GitHub, Docker dependencies removed, sandbox and frontend configured for Replit
