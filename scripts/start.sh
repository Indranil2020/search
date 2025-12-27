#!/bin/bash

# Search System Start Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

case "$1" in
    setup)
        echo "Setting up Search System..."
        
        # Backend setup
        echo "Setting up Python backend..."
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
        
        # Frontend setup
        echo "Setting up TypeScript frontend..."
        cd frontend
        npm install
        cd ..
        
        echo "Setup complete!"
        echo "Copy .env.example to .env and configure your API keys."
        ;;
    
    backend)
        echo "Starting backend server..."
        cd backend
        source venv/bin/activate
        python app.py
        ;;
    
    frontend)
        echo "Starting frontend dev server..."
        cd frontend
        npm run dev
        ;;
    
    dev)
        echo "Starting both servers..."
        
        # Start backend in background
        cd "$SCRIPT_DIR/backend"
        source venv/bin/activate
        python app.py &
        BACKEND_PID=$!
        
        # Start frontend
        cd "$SCRIPT_DIR/frontend"
        npm run dev &
        FRONTEND_PID=$!
        
        # Wait for interrupt
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
        wait
        ;;
    
    *)
        echo "Usage: $0 {setup|backend|frontend|dev}"
        echo ""
        echo "Commands:"
        echo "  setup    - Install dependencies"
        echo "  backend  - Start backend server"
        echo "  frontend - Start frontend dev server"
        echo "  dev      - Start both servers"
        exit 1
        ;;
esac
