# gui.py
import streamlit as st
# Standard library imports
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables for GITHUB_TOKEN
load_dotenv()

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# Persistent storage for session state
if "audit_results" not in st.session_state:
    st.session_state.audit_results = {}
if "github_files" not in st.session_state:
    st.session_state.github_files = []
if "available_branches" not in st.session_state:
    st.session_state.available_branches = []
if "available_models" not in st.session_state:
    st.session_state.available_models = {}

def get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token or "YOUR_GITHUB_TOKEN" in token:
        st.error("Missing GITHUB_TOKEN in .env")
        return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def fetch_available_models():
    try:
        # Connect to FastAPI backend
        response = requests.get("https://localhost:8000/models", verify=False, timeout=3)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

st.title("🛡️ PR Guardian")
st.markdown("### Secure Multi-Model Code Auditor")

# Fetch models for configuration
available_models = fetch_available_models()

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model Selection
    selected_labels = st.multiselect(
        "Select Models (Max 3)",
        options=list(available_models.keys()),
        default=[list(available_models.keys())[0]] if available_models else [],
        key="model_selector",
        max_selections=3
    )
    selected_ids = [available_models[name] for name in selected_labels]

    st.divider()

    # Repository Integration
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
                    st.error(f"Error: {resp.status_code}")
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
                            file_url = f"https://api.github.com/repos/{repo_input}/contents/{item['path']}?ref={branch_choice}"
                            f_resp = requests.get(file_url, headers=headers)
                            if f_resp.status_code == 200:
                                import base64
                                content = base64.b64decode(f_resp.json()["content"]).decode('utf-8')
                                st.session_state.github_files.append({"name": item["path"], "content": content})
                    st.success(f"Fetched {len(st.session_state.github_files)} files")
            except Exception as e:
                st.error(str(e))

    st.divider()

    # Local File Upload
    uploaded_files = st.file_uploader("Upload Source Files", accept_multiple_files=True)

# Main UI Inputs
code_input = st.text_area("Paste Code Directly:", height=200)
user_instr = st.text_input("Additional Instructions:")

# Run Audit Logic
if st.button("🚀 Run Parallel Audit", type="primary"):
    if not selected_ids:
        st.error("Select at least one model.")
    else:
        full_code = f"# Direct Input\n{code_input}\n" if code_input.strip() else ""
        
        # Process and filter local uploads
        if uploaded_files:
            for f in uploaded_files:
                if f.name.endswith(('.lock', '-lock.json')):
                    continue
                full_code += f"\n# --- Local File: {f.name} ---\n{f.getvalue().decode('utf-8')}\n"
        
        # Process and filter GitHub files
        if st.session_state.github_files:
            for gf in st.session_state.github_files:
                if gf['name'].endswith(('.lock', '-lock.json')):
                    continue
                full_code += f"\n# --- GitHub File: {gf['name']} ---\n{gf['content']}\n"

        # Safety truncation to prevent 422 error (Max 50,000 chars)
        if len(full_code) > 50000:
            st.warning("Code truncated to 50,000 characters to fit API limits.")
            full_code = full_code[:50000]

        st.session_state.audit_results = {m_id: "🔄 Processing..." for m_id in selected_ids}
        payload = {"code": full_code, "model_names": selected_ids, "user_message": user_instr}

        try:
            # Stream results from the backend
            with requests.post("https://localhost:8000/review", json=payload, stream=True, verify=False) as r:
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8').replace("data: ", ""))
                        m_id = data.get("model")
                        review = data.get("review")
                        if m_id in st.session_state.audit_results:
                            st.session_state.audit_results[m_id] = review
                        st.rerun()
        except Exception as e:
            st.error(f"Audit Failed: {e}")

# Results Display
if st.session_state.audit_results:
    st.divider()
    tabs = st.tabs([name for name, m_id in available_models.items() if m_id in selected_ids])
    for i, m_id in enumerate(selected_ids):
        with tabs[i]:
            st.markdown(st.session_state.audit_results.get(m_id, "No data."))