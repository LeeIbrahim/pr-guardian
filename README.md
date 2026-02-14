# 🛡️ PR Guardian: AI Code Reviewer

PR Guardian is a multi-agent AI system built with **LangGraph** to perform automated code security audits. It orchestrates multiple LLMs simultaneously to provide a comprehensive review of your Python code.

## 🚀 Key Features
- **Multi-Model Audit**: Compare results from OpenAI (GPT-4o), Groq (Llama 3.3), and Local Models.
- **Local LLM Support**: Fully private audits using Ollama (Llama 3.1 & 3.2).
- **LangGraph Orchestration**: Uses a stateful graph to manage the "Security Reviewer" and "Report Aggregator" nodes.
- **Safety Limits**: GUI restricted to **3 simultaneous models** to ensure stable performance.

## 🛠️ Setup

### 1. Installation
Run the automated installer to set up `uv`, dependencies, and local models:
```bash
chmod +x install.sh
./install.sh

2. Configuration

Add your API keys to the .env file:

    OPENAI_API_KEY

    GROQ_API_KEY

    HUGGINGFACE_API_KEY (Optional, for HF Router models)

3. Usage

Launch the entire suite (API + GUI) with one command:
Bash

./launch.sh

    GUI: http://localhost:8501

    API: http://localhost:8000

📂 Project Structure

    src/pr_guardian/graph.py: The LangGraph "brain" that routes requests to models.

    gui.py: Streamlit interface with a 3-model selection limit.

    main.py: FastAPI backend that streams reviews via SSE.