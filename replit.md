# AI-Manus - AI Agent Platform

## Overview
AI-Manus is an AI agent platform migrated from https://github.com/Simpleyyt/ai-manus. It provides an AI-powered assistant that can execute commands, manage files, and browse the web through a sandbox environment.

## Architecture
- **Frontend**: Vue.js 3 + Vite + TypeScript (port 5000)
- **Backend**: Python FastAPI (port 8000)
- **Sandbox**: Python FastAPI service for shell/file operations (port 8080)
- **Database**: MongoDB (external - MongoDB Atlas)
- **Cache/Queue**: Redis (external)
- **LLM Provider**: Groq API (llama-3.3-70b-versatile)

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
├── setup.sh           # Auto-download all dependencies
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
- Backend starts gracefully even if MongoDB/Redis are unavailable
- MongoDB uses certifi for SSL certificate validation
- Connection timeouts reduced (10s MongoDB, 5s Redis) for faster startup

## Required Secrets
- `API_KEY`: Groq API key
- `MONGODB_URI`: MongoDB Atlas connection string (mongodb+srv://...)
- `REDIS_HOST`: Redis host address
- `REDIS_PASSWORD`: Redis password
- `JWT_SECRET_KEY`: JWT secret for authentication

## Environment Variables (configured)
- `API_BASE`: https://api.groq.com/openai/v1
- `MODEL_NAME`: llama-3.3-70b-versatile
- `SANDBOX_ADDRESS`: localhost (local sandbox)
- `AUTH_PROVIDER`: local (default admin login)
- `LOCAL_AUTH_EMAIL`: admin@example.com
- `LOCAL_AUTH_PASSWORD`: admin123
- `BACKEND_URL`: http://localhost:8000

## Login
- Email: admin@example.com
- Password: admin123
- Auth provider: local (no database required for login)

## Setup
Run `bash setup.sh` to install all dependencies automatically.

## Known Issues
- MongoDB Atlas free tier cluster may pause after inactivity. Resume from Atlas dashboard if connection fails.
- MongoDB Atlas requires IP whitelist: set 0.0.0.0/0 to allow all IPs for Replit.

## Recent Changes
- 2026-02-22: Initial migration from GitHub, Docker dependencies removed, sandbox and frontend configured for Replit
- 2026-02-22: All dependencies installed, API configured for Groq, backend graceful startup without MongoDB/Redis, auto-setup script created
