#!/bin/bash

# Color codes for clarity
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️ Starting PR Guardian Full System Install...${NC}"

# 1. Install uv (The Python Project Manager)
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✅ uv is already installed.${NC}"
else
    echo -e "${YELLOW}uv not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# 2. Setup Python Project
echo -e "${BLUE}📦 Setting up Python environment...${NC}"
if [ ! -f "pyproject.toml" ]; then
    echo "Initializing new uv project..."
    uv init --lib
fi

# 3. Install Dependencies
# We use 'uv add' which automatically updates pyproject.toml and uv.lock
echo "Installing/Syncing core dependencies..."
uv add fastapi uvicorn streamlit requests langgraph langchain-openai langchain-groq \
       langchain-anthropic langchain-together langchain-huggingface python-dotenv

# Install dev dependencies (pytest and async support)
echo "Installing development dependencies..."
uv add --dev pytest pytest-asyncio

# 4. Ollama Setup (Local LLM Support)
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama binary is already installed.${NC}"
else
    echo -e "${YELLOW}Ollama not found. Installing...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 5. Model Sync
echo -e "${BLUE}📥 Synchronizing local models...${NC}"
# Start ollama temporarily to pull the model
ollama serve &
OLLAMA_PID=$!
sleep 5
ollama pull llama3.1
kill $OLLAMA_PID

# 6. .env Verification
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Creating .env template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        cat <<EOT >> .env
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here
EOT
    fi
    echo "Please edit the .env file with your actual API keys."
fi

# 7. Post-Installation Verification
echo -e "${BLUE}🧪 Running system health check...${NC}"
if [ -d "tests" ] || [ -f "test_graph.py" ]; then
    uv run pytest
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✨ Installation successful and tests passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Installation finished, but some tests failed. Check the logs above.${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  No tests found to run. System ready.${NC}"
fi

echo -e "${GREEN}🚀 PR Guardian is ready. Use ./launch.sh to start.${NC}"