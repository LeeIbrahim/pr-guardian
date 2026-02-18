import streamlit as st
import requests
import json
<<<<<<< HEAD

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# Persistent storage for results
=======
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# Persistent storage for session state
>>>>>>> 1fc32dc (Updates to multiple files adding git and debugging)
if "audit_results" not in st.session_state:
    st.session_state.audit_results = {}
if "github_files" not in st.session_state:
    st.session_state.github_files = []
if "available_branches" not in st.session_state:
    st.session_state.available_branches = []
if "available_models" not in st.session_state:
    st.session_state.available_models = {}

<<<<<<< HEAD
def fetch_available_models():
    try:
        # Use https and verify=False to match your uvicorn SSL launch
        response = requests.get("https://localhost:8000/models", verify=False, timeout=2)
=======
def get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token or "YOUR_GITHUB_TOKEN" in token:
        st.error("Missing GITHUB_TOKEN in .env")
        return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def fetch_available_models():
    try:
        response = requests.get("https://localhost:8000/models", verify=False, timeout=3)
>>>>>>> 1fc32dc (Updates to multiple files adding git and debugging)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

<<<<<<< HEAD
st.title("🛡️ PR Guardian")
available_models = fetch_available_models()

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # 1. Model Selection
    selected_labels = st.multiselect(
        "Select Models (Max 3)",
        options=list(available_models.keys()),
        default=[list(available_models.keys())[0]] if available_models else [],
        key="model_selector",
        max_selections=3
    )
    selected_ids = [available_models[name] for name in selected_labels]

    st.divider()

    # 2. Grayed-out Button Logic
    # Pulling values from session_state keys to ensure responsiveness
    manual_code = st.session_state.get("manual_code_input", "")
    has_files = st.session_state.get("file_uploader") is not None and len(st.session_state.get("file_uploader", [])) > 0
    
    # Disable button if no model selected OR (no text AND no files)
    is_disabled = not selected_ids or (not manual_code.strip() and not has_files)
    
    run_audit = st.button(
        "🚀 Run Parallel Audit", 
        type="primary", 
        disabled=is_disabled,
        use_container_width=True
    )

    st.divider()

    # 3. File Upload at bottom
    uploaded_files = st.file_uploader(
        "Upload Source Files", 
        accept_multiple_files=True, 
        key="file_uploader"
    )

# Main UI
code_input = st.text_area("Paste Code Directly:", height=250, key="manual_code_input")
user_instr = st.text_input("Additional Instructions:")

# Display Results Side-by-Side
if selected_ids:
    st.divider()
    cols = st.columns(len(selected_ids))
    
    for i, m_id in enumerate(selected_ids):
        with cols[i]:
            display_name = [k for k, v in available_models.items() if v == m_id][0]
            st.subheader(f"🤖 {display_name}")
            
            content = st.session_state.audit_results.get(m_id, "")
            with st.container(height=500, border=True):
                if content:
                    st.code(content, language="markdown")
                else:
                    st.info("Awaiting audit...")

    if run_audit:
        # 1. Clean up multi-line comments as requested [2026-02-13]
        full_code = f"# Source Audit\n{code_input}"
        if uploaded_files:
            for f in uploaded_files:
                full_code += f"\n# --- File: {f.name} ---\n{f.getvalue().decode('utf-8')}"

        st.session_state.audit_results = {m_id: "🔄 Processing..." for m_id in selected_ids}
        payload = {"code": full_code, "model_names": selected_ids, "user_message": user_instr}

        try:
            with requests.post("https://localhost:8000/review", json=payload, stream=True, verify=False) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').replace("data: ", "")
                        data = json.loads(decoded)
                        
                        incoming_id = data.get("model")
                        review_text = data.get("review")

                        # If the incoming ID matches a specific selection, update it
                        if incoming_id in st.session_state.audit_results:
                            st.session_state.audit_results[incoming_id] = review_text
                        else:
                            # FALLBACK: If the ID is generic (like "mock_review"), 
                            # update EVERY model currently stuck on "Processing"
                            for m_id in selected_ids:
                                if "Processing" in st.session_state.audit_results.get(m_id, ""):
                                    st.session_state.audit_results[m_id] = review_text
                        
            # Rerun once after the full stream is consumed
            st.rerun()
        except Exception as e:
            st.error(f"Streaming Error: {e}")
=======
def fetch_branches(repo_name):
    headers = get_github_headers()
    if not headers: return []
    clean_repo = repo_name.strip().replace("https://github.com/", "").rstrip("/")
    url = f"https://api.github.com/repos/{clean_repo}/branches"
    try:
        response = requests.get(url, headers=headers)
        return [branch['name'] for branch in response.json()] if response.status_code == 200 else []
    except:
        return []

def fetch_github_commit_files(repo_name, ref):
    headers = get_github_headers()
    if not headers: return []
    clean_repo = repo_name.strip().replace("https://github.com/", "").rstrip("/")
    api_url = f"https://api.github.com/repos/{clean_repo}/commits/{ref}"
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            commit_data = response.json()
            files = []
            for file in commit_data.get("files", []):
                content_resp = requests.get(file.get("raw_url"))
                if content_resp.status_code == 200:
                    files.append({"name": file["filename"], "content": content_resp.text})
            return files
        return []
    except:
        return []

st.title("🛡️ PR Guardian")

# Refresh models on startup
if not st.session_state.available_models:
    st.session_state.available_models = fetch_available_models()

available_models = st.session_state.available_models

with st.sidebar:
    st.header("⚙️ Configuration")
    if not available_models:
        st.error("❌ Backend Connection Failed")
        if st.button("Retry"): st.rerun()
    else:
        selected_labels = st.multiselect("Models", options=list(available_models.keys()), default=[list(available_models.keys())[0]] if available_models else [])
        selected_ids = [available_models[name] for name in selected_labels]
        st.divider()
        st.subheader("🌐 GitHub Integration")
        repo_input = st.text_input("Repository (owner/repo)")
        if st.button("Get Branches", use_container_width=True):
            st.session_state.available_branches = fetch_branches(repo_input)
        if st.session_state.available_branches:
            selected_branch = st.selectbox("Select Branch", options=st.session_state.available_branches)
            if st.button("Fetch Files", use_container_width=True):
                with st.spinner("Downloading GitHub content..."):
                    st.session_state.github_files = fetch_github_commit_files(repo_input, selected_branch)
        st.divider()
        # The button triggers the audit, but we'll use a session_state flag to handle the rerun issue
        run_audit = st.button("🚀 Run Security Audit", type="primary", use_container_width=True)
        user_instr = st.text_area("Custom Instructions", height=100)
        
        if st.button("🗑️ Clear Results"):
            st.session_state.audit_results = {}
            st.rerun()

# Main UI
code_input = st.text_area("Paste Code", height=150, key="manual_code_input")
uploaded_files = st.file_uploader("Upload Local Files", accept_multiple_files=True)

# Define placeholders and persistent display
if selected_ids:
    st.divider()
    cols = st.columns(len(selected_ids))
    placeholders = []
    
    for i, m_id in enumerate(selected_ids):
        with cols[i]:
            display_name = [k for k, v in available_models.items() if v == m_id][0]
            st.subheader(f"🤖 {display_name}")
            placeholders.append(st.empty())
            
            # Show existing data if available
            if m_id in st.session_state.audit_results:
                placeholders[i].markdown(st.session_state.audit_results[m_id])
            else:
                placeholders[i].info("Awaiting audit...")

    if run_audit:
        # 1. Gather and Clean Sources (Using # comments)
        all_sources = []
        if code_input:
            all_sources.append({"name": "Manual Input", "content": code_input})
        if uploaded_files:
            for f in uploaded_files:
                all_sources.append({"name": f.name, "content": f.getvalue().decode('utf-8')})
        if st.session_state.github_files:
            for gf in st.session_state.github_files:
                all_sources.append({"name": gf['name'], "content": gf['content']})

        # 2. Chunking logic (40k char limit)
        batches = []
        current_batch = ""
        for src in all_sources:
            # Clean up headers to use normal # comments
            entry = f"\n# --- File: {src['name']} ---\n{src['content']}\n"
            if len(current_batch) + len(entry) > 40000:
                batches.append(current_batch)
                current_batch = entry
            else:
                current_batch += entry
        if current_batch:
            batches.append(current_batch)

        # 3. Execution with Spinner
        with st.spinner("🔍 Streaming audit results..."):
            # Clear previous results for selected models to start fresh
            for m_id in selected_ids:
                st.session_state.audit_results[m_id] = "🔄 Initializing..."
                
            total_batches = len(batches)
            for idx, batch_code in enumerate(batches):
                payload = {
                    "code": batch_code, 
                    "model_names": selected_ids, 
                    "user_message": f"(Batch {idx+1}/{total_batches}) {user_instr}"
                }

                try:
                    with requests.post("https://localhost:8000/review", json=payload, stream=True, verify=False) as r:
                        if r.status_code != 200:
                            st.error(f"Error {r.status_code}: {r.text}")
                            break
                            
                        for line in r.iter_lines():
                            if line:
                                decoded = line.decode('utf-8').replace("data: ", "")
                                try:
                                    data = json.loads(decoded)
                                    m_id = data.get("model")
                                    new_review = data.get("review")

                                    if m_id in selected_ids:
                                        idx_in_selection = selected_ids.index(m_id)
                                        
                                        # Handling multi-batch concatenation
                                        if idx == 0 and "🔄" in st.session_state.audit_results[m_id]:
                                            st.session_state.audit_results[m_id] = new_review
                                        elif idx > 0:
                                            # Append subsequent batches
                                            if "---" not in st.session_state.audit_results[m_id]:
                                                 st.session_state.audit_results[m_id] = f"### Full Audit Report\n\n{st.session_state.audit_results[m_id]}"
                                            st.session_state.audit_results[m_id] += f"\n\n---\n#### Analysis: Part {idx+1}\n{new_review}"
                                        else:
                                            st.session_state.audit_results[m_id] = new_review
                                        
                                        # Live update of the UI
                                        placeholders[idx_in_selection].markdown(st.session_state.audit_results[m_id])
                                except json.JSONDecodeError:
                                    continue
                except Exception as e:
                    st.error(f"Connection failed: {e}")
            
            st.success("✅ Audit Complete!")
>>>>>>> 1fc32dc (Updates to multiple files adding git and debugging)
