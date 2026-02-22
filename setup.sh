#!/bin/bash
echo "========================================="
echo "  AI-Manus - Auto Setup Dependencies"
echo "========================================="
echo ""

echo "[1/4] Installing Python backend dependencies..."
pip install -r backend/requirements.txt --quiet 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ Backend Python dependencies installed"
else
    echo "  ✗ Failed to install backend Python dependencies"
    exit 1
fi

echo ""
echo "[2/4] Installing Python sandbox dependencies..."
pip install -r sandbox/requirements.txt --quiet 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ Sandbox Python dependencies installed"
else
    echo "  ✗ Failed to install sandbox Python dependencies"
    exit 1
fi

echo ""
echo "[3/4] Installing Frontend dependencies..."
cd frontend && npm install --silent 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ Frontend dependencies installed"
else
    echo "  ✗ Failed to install frontend dependencies"
    exit 1
fi
cd ..

echo ""
echo "[4/4] Verifying installation..."
echo ""

PYTHON_OK=true
python3 -c "
import importlib, sys
packages = [
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('openai', 'openai'),
    ('anthropic', 'anthropic'),
    ('pydantic', 'pydantic'),
    ('pydantic_settings', 'pydantic-settings'),
    ('dotenv', 'python-dotenv'),
    ('sse_starlette', 'sse-starlette'),
    ('httpx', 'httpx'),
    ('rich', 'rich'),
    ('playwright', 'playwright'),
    ('markdownify', 'markdownify'),
    ('docker', 'docker'),
    ('websockets', 'websockets'),
    ('motor', 'motor'),
    ('pymongo', 'pymongo'),
    ('beanie', 'beanie'),
    ('async_lru', 'async-lru'),
    ('redis', 'redis'),
    ('bs4', 'beautifulsoup4'),
    ('multipart', 'python-multipart'),
    ('mcp', 'mcp'),
    ('jwt', 'pyjwt'),
    ('cryptography', 'cryptography'),
    ('certifi', 'certifi'),
    ('email_validator', 'email-validator'),
]
missing = []
for mod, pkg in packages:
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(pkg)

if missing:
    print('  Python packages MISSING: ' + ', '.join(missing))
    sys.exit(1)
else:
    print('  ✓ All Python packages verified (' + str(len(packages)) + ' packages)')
" 2>&1

if [ $? -ne 0 ]; then
    PYTHON_OK=false
    echo "  Attempting to install missing Python packages..."
    pip install certifi email-validator --quiet 2>&1
fi

cd frontend
node -e "
const deps = Object.keys(require('./package.json').dependencies || {});
const missing = [];
const fs = require('fs');
const path = require('path');
deps.forEach(d => {
    const modPath = path.join('node_modules', d);
    if (!fs.existsSync(modPath)) missing.push(d);
});
if (missing.length > 0) {
    console.log('  Frontend packages MISSING: ' + missing.join(', '));
    process.exit(1);
} else {
    console.log('  ✓ All Frontend packages verified (' + deps.length + ' packages)');
}
" 2>&1
cd ..

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Default Login Credentials:"
echo "  Email:    admin@example.com"
echo "  Password: admin123"
echo ""
echo "Required Secrets (set in Replit Secrets tab):"
echo "  - API_KEY        : Anthropic (Claude) API key"
echo "  - MONGODB_URI    : MongoDB Atlas connection string"
echo "  - REDIS_HOST     : Redis host address"
echo "  - REDIS_PASSWORD : Redis password"
echo "  - REDIS_PORT     : Redis port (default: 16364)"
echo "  - JWT_SECRET_KEY : JWT secret for authentication"
echo ""
echo "Environment Variables (pre-configured):"
echo "  - API_BASE        : https://api.anthropic.com"
echo "  - MODEL_NAME      : claude-sonnet-4-20250514"
echo "  - AUTH_PROVIDER    : local"
echo ""
echo "Workflows to start:"
echo "  1. Backend API     (port 8000)"
echo "  2. Frontend        (port 5000)"
echo "  3. Sandbox Service (port 8080)"
echo ""
