🛡️ PR Guardian: AI Code Reviewer

PR Guardian is a multi-agent AI system designed to perform automated code reviews. It utilizes LangGraph to coordinate specialized agents (Security, Style, and Logic) to audit your Python code before it hits production. It supports cloud models (OpenAI, Groq) and fully local models via Ollama.
🚀 Quick Start
1. Prerequisites

    Python 3.12+

    Ollama (for local Llama 3.1 support)

    API Keys: You will need at least one key (OpenAI or Groq) to use cloud models.

2. Installation

We have provided an automated installer that sets up your Python environment, installs uv, and pulls the necessary local LLM manifests.
Bash

chmod +x install.sh
./install.sh

3. Set Your API Keys

After running the installer, a .env file will be created in your root directory. Open it and add your credentials:
Bash

# .env file
OPENAI_API_KEY=sk-your-key-here
GROQ_API_KEY=gsk-your-key-here

4. Running the App

The application consists of a FastAPI backend and a Streamlit frontend. Use the launch script to start both simultaneously:
Bash

chmod +x launch.sh
./launch.sh

    Frontend UI: http://127.0.0.1:8501

    Backend API: http://127.0.0.1:8000

🧠 Supported Models
Provider	Model Tag	Best For
OpenAI	gpt-4o	Deep reasoning and logic audits.
Groq	llama-3.3-70b	Lightning-fast reviews (Free Tier).
Ollama	llama3.1	100% Private, offline code analysis.
📂 Project Structure

    src/pr_guardian/main.py: The FastAPI entry point.

    src/pr_guardian/graph.py: The LangGraph logic (The "Brain").

    gui.py: The Streamlit dashboard.

    install.sh: Full environment and dependency setup.

    launch.sh: Multi-process orchestrator.

⚠️ Important Notes

    Local Performance: Running llama3.1 locally requires at least 8GB of VRAM (GPU) or 16GB of System RAM (CPU) for smooth performance.

    Thread ID: The "Thread ID" in the sidebar allows the AI to maintain memory of your code changes. Using the same ID lets the agents remember previous context.
