# AI-Manus - AI Agent Platform

## Overview
AI-Manus is an AI agent platform migrated from https://github.com/Simpleyyt/ai-manus. It provides an AI-powered assistant that can execute commands, manage files, and browse the web through a sandbox environment.

## Architecture
- **Frontend**: Vue.js 3 + Vite + TypeScript (port 5000)
- **Backend**: Python FastAPI (port 8000 dev, port 5000 production)
- **Sandbox**: Python FastAPI service for shell/file operations (port 8080)
- **Database**: MongoDB (external - MongoDB Atlas)
- **Cache/Queue**: Redis (external - RedisLabs, port 16364)
- **LLM Provider**: Anthropic Claude API (claude-sonnet-4-20250514)

## Project Structure
```
/
├── frontend/          # Vue.js frontend app
│   └── dist/          # Built static files (production)
├── backend/           # FastAPI backend API
│   └── app/
│       ├── main.py              # App entry, serves frontend in production
│       ├── core/config.py       # Settings and env vars
│       ├── domain/              # Domain models and interfaces
│       │   ├── models/memory.py # Memory management
│       │   └── services/agents/ # Agent logic, tool handling
│       ├── infrastructure/      # External service implementations
│       │   └── external/llm/openai_llm.py  # Anthropic Claude LLM client
│       └── interfaces/          # API routes and dependencies
├── sandbox/           # Sandbox service for command execution
│   └── app/
│       ├── main.py
│       ├── services/            # Shell, file, supervisor services
│       └── api/                 # API routes
└── replit.md
```

## Workflows (Development)
- **Frontend**: `cd frontend && npx vite --host 0.0.0.0 --port 5000` (webview, port 5000)
- **Backend API**: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (console, port 8000)
- **Sandbox Service**: `cd sandbox && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080` (console, port 8080)

## Production Deployment
- **Build**: `cd frontend && npm run build` (creates dist/ with static files)
- **Run**: Backend serves built frontend + API on port 5000, Sandbox on port 8080
- **Type**: VM deployment (stateful, always running)

## LLM Provider: OpenAI-compatible Custom API
- LLM client (openai_llm.py) uses httpx to POST directly to custom OpenAI-compatible endpoint
- Base URL: configured via API_BASE env var
- Model: configured via MODEL_NAME env var
- Messages sent in standard OpenAI chat completion format (no conversion needed)
- Supports tools, tool_choice, response_format pass-through
- max_tokens: 4096

## Required Secrets
- `API_KEY`: Custom API key for OpenAI-compatible endpoint
- `MONGODB_URI`: MongoDB Atlas connection string (mongodb+srv://...)
- `REDIS_HOST`: Redis host address
- `REDIS_PASSWORD`: Redis password
- `JWT_SECRET_KEY`: JWT secret for authentication

## Environment Variables (configured)
- `API_BASE`: https://api--ngad4kbh.replit.app/v1/agent/completions
- `MODEL_NAME`: openai
- `SANDBOX_ADDRESS`: localhost (local sandbox)
- `AUTH_PROVIDER`: local (default admin login)
- `LOCAL_AUTH_EMAIL`: admin@example.com
- `LOCAL_AUTH_PASSWORD`: admin123
- `BACKEND_URL`: http://localhost:8000
- `REDIS_PORT`: 16364

## Login
- Email: admin@example.com
- Password: admin123
- Auth provider: local (no database required for login)

## Known Issues
- MongoDB Atlas free tier cluster may pause after inactivity
- MongoDB Atlas requires IP whitelist: set 0.0.0.0/0 for Replit

## Recent Changes
- 2026-02-22: Initial migration from GitHub, Docker dependencies removed
- 2026-02-22: All dependencies installed, API configured for Groq
- 2026-02-22: Fixed Groq API compatibility (response_format, tool_choice, function_name)
- 2026-02-22: Fixed Redis port (16364), MongoDB SSL, memory sanitization
- 2026-02-22: Production deployment configured (VM, frontend build + backend serving)
- 2026-02-22: End-to-end testing passed: login, session creation, AI chat response
- 2026-02-22: Migrated LLM from Groq to Anthropic Claude API
- 2026-02-22: Fixed response leak bug (internal reasoning no longer shown to users)
- 2026-02-22: Removed Groq-specific workarounds (function_name sanitization, response_format restrictions)
