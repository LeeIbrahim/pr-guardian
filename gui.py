# gui.py
import streamlit as st
# Standard networking and data handling imports
import requests
import json
import time
import os
from dotenv import load_dotenv

# Initialize configuration from .env file
load_dotenv()

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# Session state initialization for persistent data
if "audit_results" not in st.session_state:
    st.session_state.audit_results = {}
if "github_files" not in st.session_state:
    st.session_state.github_files = []
if "available_branches" not in st.session_state:
    st.session_state.available_branches = []
if "available_models" not in st.session_state:
    st.session_state.available_models = {}

def get_github_headers():
    # Authentication for GitHub API calls
    token = os.getenv("GITHUB_TOKEN")
    if not token or "YOUR_GITHUB_TOKEN" in token:
        st.error("Missing GITHUB_TOKEN in .env")
        return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def fetch_available_models():
    # Pull model list from FastAPI backend
    try:
        response = requests.get("https://localhost:8000/models", verify=False, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except Exception:
        return {}

st.title("🛡️ PR Guardian")
st.markdown("### Secure Multi-Model Code Auditor")

available_models = fetch_available_models()

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model selector (Maximum 3 models as restricted by backend)
    selected_labels = st.multiselect(
        "Select Models (Max 3)",
        options=list(available_models.keys()),
        default=[list(available_models.keys())[0]] if available_models else [],
        key="model_selector",
        max_selections=3
    )
    selected_ids = [available_models[name] for name in selected_labels]

    st.divider()

    # GitHub workflow integration
    st.header("GitHub Integration")
    repo_input = st.text_input("Repository (owner/repo):", placeholder="e.g., user/project")

    if st.button("Fetch Branches"):
        headers = get_github_headers()
        if repo_input and headers:
            try:
                url = f"https://api.github.com/repos/{repo_input}/branches"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    st.session_state.available_branches = [b['name'] for b in resp.json()]
                else:
                    st.error(f"GitHub Error: {resp.status_code}")
            except Exception as e:
                st.error(str(e))

    branch_choice = st.selectbox("Select Branch:", options=st.session_state.available_branches)

    if st.button("Fetch GitHub Files"):
        headers = get_github_headers()
        if repo_input and branch_choice and headers:
            try:
                url = f"https://api.github.com/repos/{repo_input}/git/trees/{branch_choice}?recursive=1"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    tree = resp.json().get("tree", [])
                    st.session_state.github_files = []
                    for item in tree:
                        if item["type"] == "blob":
                            # Exclude binary and lock files
                            if item["path"].endswith(('.lock', '-lock.json', '.png', '.jpg')):
                                continue
                            file_url = f"https://api.github.com/repos/{repo_input}/contents/{item['path']}?ref={branch_choice}"
                            f_resp = requests.get(file_url, headers=headers)
                            if f_resp.status_code == 200:
                                import base64
                                content = base64.b64decode(f_resp.json()["content"]).decode('utf-8', errors='ignore')
                                st.session_state.github_files.append({"name": item["path"], "content": content})
                    st.success(f"Fetched {len(st.session_state.github_files)} files")
            except Exception as e:
                st.error(str(e))

    st.divider()
    uploaded_files = st.file_uploader("Upload Source Files", accept_multiple_files=True)

# User code inputs
code_input = st.text_area("Paste Code Directly:", height=200)
user_instr = st.text_input("Additional Instructions (e.g., Focus on security):")

# Results container using tabs and placeholders
if selected_labels:
    st.divider()
    tabs = st.tabs(selected_labels)
    # Create a dictionary of placeholders to update without rerunning the whole script
    placeholders = {}
    for i, label in enumerate(selected_labels):
        m_id = available_models[label]
        with tabs[i]:
            placeholders[m_id] = st.empty()
            if m_id in st.session_state.audit_results:
                placeholders[m_id].markdown(st.session_state.audit_results[m_id])
            else:
                placeholders[m_id].info("Audit not started.")

if st.button("🚀 Run Parallel Audit", type="primary"):
    if not selected_ids:
        st.error("Select at least one model.")
    else:
        # Concatenate code from all active sources
        full_code = f"# Direct Input\n{code_input}\n" if code_input.strip() else ""
        
        if uploaded_files:
            for f in uploaded_files:
                if not f.name.endswith(('.lock', '-lock.json')):
                    full_code += f"\n# --- Local File: {f.name} ---\n{f.getvalue().decode('utf-8')}\n"
        
        if st.session_state.github_files:
            for gf in st.session_state.github_files:
                full_code += f"\n# --- GitHub File: {gf['name']} ---\n{gf['content']}\n"

        # Truncate large payloads to stay within model context limits
        if len(full_code) > 50000:
            st.warning("Input truncated to 50,000 characters.")
            full_code = full_code[:50000]

        # Reset UI state to Processing
        for m_id in selected_ids:
            st.session_state.audit_results[m_id] = "🔄 Processing..."
            if m_id in placeholders:
                placeholders[m_id].markdown("🔄 Processing...")

        payload = {"code": full_code, "model_names": selected_ids, "user_message": user_instr}

        try:
            # Connect with a high 300s timeout for local inference
            with requests.post("https://localhost:8000/review", json=payload, stream=True, verify=False, timeout=300) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').replace("data: ", "")
                        try:
                            data = json.loads(decoded)
                            incoming_id = data.get("model")
                            review_text = data.get("review")
                            # Direct placeholder update avoids st.rerun() killing the stream
                            if incoming_id in placeholders:
                                st.session_state.audit_results[incoming_id] = review_text
                                placeholders[incoming_id].markdown(review_text)
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.Timeout:
            st.error("The audit timed out. Local models might be under heavy load.")
        except Exception as e:
            st.error(f"Audit failed: {e}")