# gui.py
import streamlit as st
import requests
import json
import os
import urllib3
import io
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from .github_utils import fetch_commit_files

load_dotenv()

if os.getenv("ENVIRONMENT", "development"):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if "drive_current_folder" not in st.session_state:
    st.session_state.drive_current_folder = 'root'
if "drive_folder_stack" not in st.session_state:
    st.session_state.drive_folder_stack = []
if "available_models" not in st.session_state:
    st.session_state.available_models = {}
if "credentials" not in st.session_state:
    st.session_state.credentials = None
if "staged_files" not in st.session_state:
    st.session_state.staged_files = [] 
if "audit_results" not in st.session_state:
    st.session_state.audit_results = ""

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BACKEND_URL = os.getenv("BACKEND_URL", "https://127.0.0.1:8000")
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(__file__), "client_secrets.json")
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
REDIRECT_URI = os.getenv("URI_REDIRECT", "https://localhost:8501/")

# # --- GITHUB LOGIC ---
def fetch_latest_from_github(repo_name, branch="main"):
    from github import Github
    token = os.getenv("GITHUB_TOKEN")
    g = Github(token)
    try:
        repo = g.get_repo(repo_name)
        sha = repo.get_branch(branch).commit.sha
        return fetch_commit_files(repo_name, sha)
    except Exception as e:
        st.error(f"GitHub Error: {e}")
        return []

# # --- GOOGLE AUTH ---
def get_google_auth_flow():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return None
    return Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)

if "code" in st.query_params and st.session_state.credentials is None:
    flow = get_google_auth_flow()
    if flow:
        flow.fetch_token(code=st.query_params["code"])
        st.session_state.credentials = flow.credentials
        st.query_params.clear()
        st.rerun()

# # --- GOOGLE DRIVE LOGIC ---
@st.dialog("Google Drive File Browser", width="large")
def drive_explorer_dialog():
    # # Header & Back Button
    cols = st.columns([0.1, 0.7, 0.2])
    if st.session_state.drive_folder_stack:
        if cols[0].button("⬅️"):
            st.session_state.drive_current_folder = st.session_state.drive_folder_stack.pop()
            st.rerun()
    
    cols[1].markdown(f"**Location:** `{st.session_state.drive_current_folder}`")
    
    st.divider()

    items = list_user_drive_contents(st.session_state.drive_current_folder)
    
    if not items:
        st.info("No supported files found here.")

    for item in items:
        c1, c2, c3 = st.columns([0.05, 0.75, 0.2])
        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
        icon = "📁" if is_folder else "📄"
        
        c1.write(icon)
        
        # Navigation for folders
        if is_folder:
            if c2.button(item['name'], key=f"nav_{item['id']}", use_container_width=True):
                st.session_state.drive_folder_stack.append(st.session_state.drive_current_folder)
                st.session_state.drive_current_folder = item['id']
                st.rerun()
            # Optional: Add whole folder logic here if needed
        else:
            c2.write(item['name'])
            
            # Check if already added
            already_added = any(f.get('id') == item['id'] for f in st.session_state.staged_files)
            
            if already_added:
                c3.button("Added", key=f"add_{item['id']}", disabled=True, use_container_width=True)
            else:
                if c3.button("Select", key=f"add_{item['id']}", use_container_width=True):
                    content = download_drive_file(item['id'])
                    if content:
                        st.session_state.staged_files.append({
                            "id": item['id'],
                            "name": item['name'], 
                            "content": content, 
                            "source": "Drive"
                        })
                        st.toast(f"Added {item['name']}")
                        st.rerun()

    st.divider()
    if st.button("Close Explorer", use_container_width=True):
        st.rerun()

# # --- GOOGLE UTILS ---
def list_user_drive_contents(folder_id='root'):
    if not st.session_state.credentials:
        return []
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query, 
            fields="files(id, name, mimeType)",
            pageSize=50
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Drive List Error: {e}")
        return []

def download_drive_file(file_id):
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue().decode('utf-8')
    except Exception as e:
        st.error(f"Download Error: {e}")
        return None

# # --- UI LAYOUT ---
st.title("🛡️ PR Guardian")

conf_col1, conf_col2 = st.columns([0.7, 0.3])

with conf_col1:
    try:
        # # verify=False for local self-signed certificates
        models_resp = requests.get(f"{BACKEND_URL}/models", verify=False, timeout=2)
        if models_resp.status_code == 200:
            st.session_state.available_models = models_resp.json()
    except Exception:
        # # Silent fallback to avoid persistent error messages on the main screen
        if not st.session_state.available_models:
            st.session_state.available_models = {
                "GPT-4o": "gpt-4o-latest",
                "Grok 3": "grok-3",
                "DeepSeek (Local)": "local/deepseek-r1",
                "Llama 3 (Local)": "local/llama3"
            }

    selected_labels = st.multiselect(
        "Select Audit Models (Max 3)", 
        options=list(st.session_state.available_models.keys()), 
        default=list(st.session_state.available_models.keys())[:1], # Default to just one
        max_selections=3
    )
    selected_ids = [st.session_state.available_models[name] for name in selected_labels]

st.divider()

# File Ingestion
st.markdown('<div class="paper-wrapper">', unsafe_allow_html=True)
col_local, col_github, col_drive = st.columns(3)

with col_local:
    st.subheader("📁 Local")
    uploaded = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        for f in uploaded:
            if not any(sf['name'] == f.name for sf in st.session_state.staged_files):
                st.session_state.staged_files.append({"name": f.name, "content": f.read().decode("utf-8"), "source": "Local"})

with col_github:
    st.subheader("🌐 GitHub")
    repo_path = st.text_input("Repo", placeholder="owner/repo", label_visibility="collapsed")
    branch_input = st.text_input("Branch", value="main", label_visibility="collapsed")
    if st.button("Fetch Latest", use_container_width=True):
        if repo_path:
            files = fetch_latest_from_github(repo_path, branch_input)
            for f in files:
                if not any(sf['name'] == f['filename'] for sf in st.session_state.staged_files):
                    st.session_state.staged_files.append({"name": f['filename'], "content": f['content'], "source": "GitHub"})
            st.rerun()

with col_drive:
    st.subheader("☁️ Google Drive")
    if not st.session_state.credentials:
        flow = get_google_auth_flow()
        if flow:
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.link_button("🔑 Login with Google", auth_url, use_container_width=True)
    else:
        # # Main Entry Point
        if st.button("📂 Browse Files", use_container_width=True):
            drive_explorer_dialog()
            
        # # Mini-Status
        drive_count = len([f for f in st.session_state.staged_files if f.get('source') == "Drive"])
        if drive_count > 0:
            st.caption(f"✅ {drive_count} files selected from Drive")

st.markdown('</div>', unsafe_allow_html=True)

# # Audit Execution
if st.session_state.staged_files:
    st.divider()
    st.subheader("Staged for Audit")
    for i, file in enumerate(st.session_state.staged_files):
        c1, c2 = st.columns([0.9, 0.1])
        c1.info(f"{file['source']}: {file['name']}")
        if c2.button("🗑️", key=f"del_{i}"):
            st.session_state.staged_files.pop(i)
            st.rerun()

    audit_msg = st.text_area("Audit Instructions (Optional)", height=100)
    
    if len(selected_ids) > 3:
        st.error("⚠️ Maximum of 3 models allowed. Please deselect some models above.")
        run_disabled = True
    elif not selected_ids:
        st.warning("Please select at least one model to begin.")
        run_disabled = True
    else:
        run_disabled = False
    
    if st.button("🚀 Start 5-Pillar Audit", type="primary", use_container_width=True, disabled=run_disabled):
        combined_code = ""
        for f in st.session_state.staged_files:
            combined_code += f"--- FILE: {f['name']} ---\n{f['content']}\n\n"

        st.session_state.audit_results = {model: "" for model in selected_labels}

        result_cols = st.columns(len(selected_labels))

        placeholders = {model: result_cols[i].empty() for i, model in enumerate(selected_labels)}

        payload = {"code": combined_code, "model_names": selected_ids, "user_message": audit_msg}

        try:
            with requests.post(f"{BACKEND_URL}/review", json=payload, stream=True, verify=False) as r:
                for line in r.iter_lines():
                    if line:
                        raw_data = line.decode('utf-8').replace("data: ", "")
                        data = json.loads(raw_data)

                        model_name = data['model']
                        review_text = data['review']
                        
                        st.session_state.audit_results[model_name] += f"{review_text}\n\n"
                        
                        with placeholders[model_name].container():
                            st.markdown(f"### 🤖 {model_name}")
                            st.markdown(st.session_state.audit_results[model_name])
        except Exception as e:
            st.error(f"Audit failed: {e}")