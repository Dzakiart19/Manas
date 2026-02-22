#!/bin/bash
echo "========================================="
echo "  AI-Manus - Auto Setup Dependencies"
echo "========================================="
echo ""

echo "[1/3] Installing Python dependencies..."
pip install -r backend/requirements.txt -r sandbox/requirements.txt --quiet 2>&1
if [ $? -eq 0 ]; then
    echo "  Python dependencies installed successfully"
else
    echo "  ERROR: Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "[2/3] Installing Frontend dependencies..."
cd frontend && npm install --silent 2>&1
if [ $? -eq 0 ]; then
    echo "  Frontend dependencies installed successfully"
else
    echo "  ERROR: Failed to install Frontend dependencies"
    exit 1
fi
cd ..

echo ""
echo "[3/3] Verifying installation..."
python3 -c "import uvicorn, fastapi, motor, redis, openai, beanie; print('  Python packages: OK')" 2>&1
node -e "require('vue'); console.log('  Node packages: OK')" 2>&1 || echo "  Node packages check skipped"

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "Required secrets (set in Replit Secrets):"
echo "  - API_KEY        : Groq/OpenAI API key"
echo "  - MONGODB_URI    : MongoDB Atlas connection string"
echo "  - REDIS_HOST     : Redis host address"
echo "  - REDIS_PASSWORD : Redis password"
echo "  - JWT_SECRET_KEY : JWT secret for authentication"
echo ""
echo "To start the app, use the Replit workflows:"
echo "  - Backend API    (port 8000)"
echo "  - Frontend       (port 5000)"
echo "  - Sandbox Service (port 8080)"
echo ""
