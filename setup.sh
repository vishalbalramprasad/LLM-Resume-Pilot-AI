#!/bin/bash

echo "================================"
echo "Resume Parser & Job Matcher Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r backend/requirements.txt

# Setup environment file
echo -e "${YELLOW}Setting up environment configuration...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please edit it with your API keys.${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p chroma_db
mkdir -p data

echo ""
echo -e "${GREEN}Setup completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Claude API key"
echo "2. Run the backend: cd backend && python main.py"
echo "3. Run the frontend: cd frontend && python -m http.server 8001"
echo ""
