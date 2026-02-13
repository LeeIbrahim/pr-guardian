#!/bin/bash

# Color codes for clarity
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🛡️ Starting PR Guardian Full System Install...${NC}"

# Install uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✅ uv is already installed.${NC}"
else
    echo -e "${YELLOW}uv not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Setup Python Environment & Dependencies
echo -e "${BLUE}📦 Setting up Python environment...${NC}"
if [ ! -f "pyproject.toml" ]; then
    echo "Initializing new uv project..."
    uv init --lib
fi

# Install all required dependencies (Added Anthropic, Together, HF, and Testing tools)
echo "Installing/Syncing dependencies..."
uv add fastapi uvicorn streamlit requests langgraph langchain-openai langchain-groq \
       langchain-anthropic langchain-together langchain-huggingface python-dotenv

# Install dev dependencies for testing
uv add --dev pytest pytest-asyncio

# Ollama Setup
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama binary is already installed.${NC}"
else
    echo -e "${YELLOW}Ollama not found. Installing...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Model Sync
echo -e "${BLUE}📥 Synchronizing local models...${NC}"
ollama serve &
sleep 5
ollama pull llama3.1
pkill ollama

# .env Verification
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Creating .env template...${NC}"
    cat <<EOT >> .env
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
EOT
    echo "Please update your .env file with actual keys."
fi

echo -e "${GREEN}✨ FULL SETUP COMPLETE!${NC}"