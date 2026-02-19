# gui.py
import streamlit as st
import requests
import json
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

def local_css(file_name):
    # Injects external CSS file into the Streamlit app
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file {file_name} not found.")

# Apply the custom styles
local_css("style.css")

# Session state initialization
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
        # FastAPI backend endpoint
        response = requests.get("https://localhost:8000/models", verify=False, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except Exception:
        return {}

st.title("🛡️ PR Guardian")

available_models = fetch_available_models()

with st.sidebar:
    st.header("⚙️ Configuration")
    selected_labels = st.multiselect(
        "Select Models (Max 3)",
        options=list(available_models.keys()),
        default=[list(available_models.keys())[0]] if available_models else [],
        key="model_selector",
        max_selections=3
    )
    selected_ids = [available_models[name] for name in selected_labels]
    
    st.divider()
    user_instr = st.text_input("Additional Instructions:", placeholder="e.g. Focus on security logic")

# --- Constrained Input Section ---
st.markdown('<div class="paper-wrapper">', unsafe_allow_html=True)

col_upload, col_github = st.columns(2)

with col_upload:
    st.subheader("📁 Local Upload")
    uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True, label_visibility="collapsed")

with col_github:
    st.subheader("🌐 GitHub Pull")
    repo_input = st.text_input("Repository:", placeholder="owner/repo", label_visibility="collapsed")
    
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        branch_choice = st.selectbox("Branch:", options=st.session_state.available_branches, label_visibility="collapsed")
    with b_col2:
        if st.button("Fetch Branches", use_container_width=True):
            headers = get_github_headers()
            if repo_input and headers:
                try:
                    url = f"https://api.github.com/repos/{repo_input}/branches"
                    resp = requests.get(url, headers=headers)
                    if resp.status_code == 200:
                        st.session_state.available_branches = [b['name'] for b in resp.json()]
                        st.rerun()
                except Exception as e:
                    st.error(f"Err: {e}")

    if st.button("Fetch GitHub Files", use_container_width=True):
        headers = get_github_headers()
        if repo_input and branch_choice and headers:
            try:
                url = f"https://api.github.com/repos/{repo_input}/git/trees/{branch_choice}?recursive=1"
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    tree = resp.json().get("tree", [])
                    st.session_state.github_files = []
                    for item in tree:
                        if item["type"] == "blob" and item["path"].endswith(('.py', '.js', '.ts', '.go', '.rs')):
                            file_url = f"https://api.github.com/repos/{repo_input}/contents/{item['path']}?ref={branch_choice}"
                            f_resp = requests.get(file_url, headers=headers)
                            if f_resp.status_code == 200:
                                content = base64.b64decode(f_resp.json()["content"]).decode('utf-8', errors='ignore')
                                st.session_state.github_files.append({"name": item["path"], "content": content})
                    st.rerun()
            except Exception as e:
                st.error(str(e))

# --- Unified File Viewer ---
if uploaded_files or st.session_state.github_files:
    st.markdown('<div class="file-list-container">', unsafe_allow_html=True)
    st.caption("Ready for Audit:")
    
    if uploaded_files:
        for f in uploaded_files:
            st.markdown(f'''<div class="file-item">
                <span>📄 {f.name}</span>
                <span class="badge badge-local">Local</span>
            </div>''', unsafe_allow_html=True)
            
    if st.session_state.github_files:
        for gf in st.session_state.github_files:
            st.markdown(f'''<div class="file-item">
                <span>🌐 {gf["name"]}</span>
                <span class="badge badge-github">GitHub</span>
            </div>''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Action Button
st.markdown('<div class="button-center">', unsafe_allow_html=True)
run_audit = st.button("Run Audit", type="primary")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) # End paper-wrapper

# --- Full Width Results ---
if selected_labels:
    st.divider()
    tabs = st.tabs(selected_labels)
    placeholders = {}
    for i, label in enumerate(selected_labels):
        m_id = available_models[label]
        with tabs[i]:
            placeholders[m_id] = st.empty()
            if m_id in st.session_state.audit_results:
                placeholders[m_id].markdown(st.session_state.audit_results[m_id])
            else:
                placeholders[m_id].info("Awaiting audit trigger...")

# Execution Logic
if run_audit:
    if not selected_ids:
        st.error("Select models in the sidebar.")
    elif not uploaded_files and not st.session_state.github_files:
        st.warning("No code provided.")
    else:
        full_code = ""
        if uploaded_files:
            for f in uploaded_files:
                full_code += f"\n# --- Local File: {f.name} ---\n{f.getvalue().decode('utf-8')}\n"
        
        if st.session_state.github_files:
            for gf in st.session_state.github_files:
                full_code += f"\n# --- GitHub File: {gf['name']} ---\n{gf['content']}\n"

        for m_id in selected_ids:
            st.session_state.audit_results[m_id] = "🔄 Processing..."
            if m_id in placeholders:
                placeholders[m_id].markdown("🔄 Processing...")

        payload = {"code": full_code, "model_names": selected_ids, "user_message": user_instr}

        try:
            with requests.post("https://localhost:8000/review", json=payload, stream=True, verify=False, timeout=300) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').replace("data: ", "")
                        data = json.loads(decoded)
                        incoming_id = data.get("model")
                        review_text = data.get("review")
                        
                        if incoming_id in placeholders:
                            st.session_state.audit_results[incoming_id] = review_text
                            placeholders[incoming_id].markdown(review_text)
        except Exception as e:
            st.error(f"Audit failed: {e}")