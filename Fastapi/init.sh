#!/bin/bash

# Create .env file for backend
if [ ! -f "./backend/.env" ]; then
    echo "Creating backend/.env file..."
    mkdir -p ./backend
    cat > ./backend/.env <<EOL
# Add your backend environment variables here
OPENAI_API_KEY=value
EOL
else
    echo "backend/.env already exists."
fi

# Create .env file for frontend
if [ ! -f "./frontend/.env" ]; then
    echo "Creating frontend/.env file..."
    mkdir -p ./frontend
    cat > ./frontend/.env <<EOL
# Add your frontend environment variables here
VITE_BACKEND_URL=value
EOL
else
    echo "frontend/.env already exists."
fi

# Install backend dependencies
cd backend
if [ -f "requirements.txt" ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found in backend."
fi
# Install frontend dependencies
cd ../frontend
if [ -f "package.json" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "No package.json found in frontend."
fi

echo "Initialization complete."