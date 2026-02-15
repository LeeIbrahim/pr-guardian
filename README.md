# 🛡️ PR Guardian

PR Guardian is a multi-model code security auditor that leverages LangGraph to chain local and cloud-based LLMs. It identifies vulnerabilities, cross-references findings, and detects false positives using a sequential audit strategy.

## ✨ Features

- **Side-by-Side Audits**: View results from multiple models simultaneously in a scrollable grid.
- **Sequential Mode**: Models review the code AND the findings of previous models to identify false positives.
- **Individual Reruns**: If a single model fails due to a timeout or API error, rerun just that model without restarting the whole audit.
- **Multi-Provider Support**:
    - OpenAI (GPT-4o)
    - Groq (Llama 3.3)
    - Local (Ollama: Llama 3.2, DeepSeek R1)
    - Hugging Face Inference API (Phi-3)
- **Memory-Persistent**: Uses `MemorySaver` to track conversation threads across reruns.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12+
- [Ollama](https://ollama.com/) (for local models)
- API Keys for OpenAI, Groq, or Hugging Face (stored in `.env`)

### 2. Installation
```bash
# Install dependencies
uv sync

# Start the FastAPI Backend
uv run fastapi dev src/pr_guardian/main.py

# Start the Streamlit GUI
uv run streamlit run gui.py