Here is the updated README.md for PR Guardian. I have incorporated all the current features, the specific "local discovery" architecture we fixed, and the correct startup sequence to ensure the environment variables and proxy are handled properly.
🛡️ PR Guardian

PR Guardian is a secure, multi-agent AI code reviewer designed for high-stakes environments. It allows you to audit code using both cloud-based LLMs (OpenAI, Groq) and local models (Ollama) via a secure internal proxy.
✨ Features

    Multi-Model Parallel Auditing: Compare reviews from GPT-4o, DeepSeek-R1, and Llama 3.2 simultaneously.

    Secure Local Discovery: Uses Caddy as a reverse proxy to provide a secure https://guardian.local:11435 endpoint for local Ollama instances.

    Self-Signed SSL: Full end-to-end encryption for both the Streamlit UI and the FastAPI backend.

    Automated "Clean" Launch: A dedicated launch script that manages port collisions, process cleanup, and environment paths automatically.

    5-Pillar Audit Logic: Standardized reviews focusing on Security, Performance, Readability, Maintainability, and Architectural Alignment.

⚙️ Installation
1. Prerequisites

    Python 3.10+

    uv: The fast Python package installer.

    Ollama: For running local models.

    Caddy: For the secure proxy.

2. Setup

Clone the repository and run the install script:
Bash

git clone <your-repo-url>
cd pr-guardian
chmod +x install.sh
./install.sh

The install script will generate your SSL certificates and add guardian.local to your /etc/hosts file (requires sudo).
3. Environment Configuration

Create a .env file in the root directory:
Bash

OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

🚀 Getting Started

To launch the entire suite (Proxy, Backend, and GUI), use the provided launch script.

    Note: Run this as a normal user. It will request sudo only for the Caddy proxy and port clearing.

Bash

chmod +x launch.sh
./launch.sh

Accessing the App

Once the script logs show 🚀 Launching Backend... and 💻 Launching GUI...:

    GUI: https://localhost:8501

    Backend API: https://guardian.local:8000/docs

🛠️ Technical Details
Proxy Architecture

PR Guardian uses Caddy to bridge the gap between secure web contexts and local services:

    Ollama Proxy: Proxies https://guardian.local:11435 → http://localhost:11434

    SSL: Automatically manages internal certificates for the .local domain.

Project Structure
Plaintext

.
├── src/pr_guardian/
│   ├── main.py          # FastAPI Backend & Model Discovery
│   └── graph.py         # LangGraph Review Logic
├── gui.py               # Streamlit Frontend
├── Caddyfile            # Proxy Configuration
├── launch.sh            # Automated Startup Script
└── install.sh           # Initial Environment Setup

🧪 Troubleshooting

Model Discovery Error:
If the UI doesn't show local models, verify Caddy is listening:
Bash

sudo lsof -i :11435