
# 🛡️ PR Guardian

PR Guardian is a secure, multi-agent AI code reviewer designed for high-stakes environments. It allows you to audit code using cloud-based LLMs (OpenAI, Groq, Together), local models (Ollama), and integrations with Google Drive and GitHub.

## ✨ Features

* **Multi-Source Code Ingestion**: 
    * **Local**: Upload files directly from your machine.
    * **Google Drive**: Browse and select files directly from your Drive folders via OAuth2.
    * **GitHub**: Fetch code and changes directly from repositories.
* **Multi-Model Parallel Auditing**: Compare reviews from up to 3 models (e.g., GPT-4o, DeepSeek-R1, Llama 3.2) simultaneously.
* **Secure Local Discovery**: Uses Caddy as a reverse proxy to provide a secure `https://guardian.local:11435` endpoint for local Ollama instances.
* **Self-Signed SSL**: Full end-to-end encryption for both the Streamlit UI and the FastAPI backend.
* **5-Pillar Audit Logic**: Standardized reviews focusing on Security, Performance, Readability, Maintainability, and Architectural Alignment.

## ⚙️ Installation

### 1. Prerequisites
* Python 3.10+
* **uv**: The fast Python package installer.
* **Ollama**: For running local models.
* **Caddy**: For the secure proxy.

### 2. Setup
Clone the repository and run the install script:
```bash
git clone <your-repo-url>
cd pr-guardian
chmod +x install.sh
./install.sh

The install script generates SSL certificates and adds guardian.local to your /etc/hosts file (requires sudo).
3. Environment Configuration

Create a .env file in the root directory. See the Environment Setup Guide below for details on obtaining these keys.
🚀 Getting Started

To launch the entire suite (Proxy, Backend, and GUI), use the provided launch script:
Bash

chmod +x launch.sh
./launch.sh
```

Accessing the App

    GUI: https://localhost:8501

    Backend API: https://guardian.local:8000/docs

🛠️ Technical Details
Google Drive Integration

The app uses Google OAuth2. Ensure you have a client_secrets.json file in the root directory and your URI_REDIRECT in .env matches your Google Cloud Console configuration.
Proxy Architecture

PR Guardian uses Caddy to bridge secure web contexts and local services:

    Ollama Proxy: Proxies https://guardian.local:11435 → http://localhost:11434




## 🔑 Environment Setup Guide (.env)

To make the app fully functional, you need to populate the following variables in your `.env` file:

### 1. LLM API Keys
* **OPENAI_API_KEY**: Get this from the [OpenAI Dashboard](https://platform.openai.com/).
* **GROQ_API_KEY**: Get this from the [Groq Console](https://console.groq.com/).
* **TOGETHER_API_KEY**: Get this from [Together AI](https://api.together.ai/).
* **HUGGINGFACE_API_TOKEN**: Get this from [Hugging Face Settings](https://huggingface.co/settings/tokens).

### 2. GitHub Integration
* **GITHUB_TOKEN**: 
    1.  Go to **GitHub Settings > Developer Settings > Personal access tokens > Tokens (classic)**.
    2.  Generate a new token with `repo` scope (to read private/public repositories).

### 3. Google Drive & Redirects
* **URI_REDIRECT**: Set this to `https://localhost:8501`. 
    * **Note**: This must match exactly what you enter in the **Google Cloud Console** under "Authorized redirect URIs" for your OAuth 2.0 Client ID.
* **BACKEND_URL**: Keep as `https://127.0.0.1:8000` unless you move the backend to a different port or machine.

### 4. Client Secrets (Google Drive)
You must also place a `client_secrets.json` file in your root folder. 
1.  Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the **Google Drive API**.
3.  Configure the **OAuth Consent Screen**.
4.  Create **OAuth 2.0 Client IDs** (Desktop or Web application).
5.  Download the JSON and rename it to `client_secrets.json`.
