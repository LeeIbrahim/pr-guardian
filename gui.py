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
from pr_guardian.github_utils import fetch_commit_files

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# # --- INITIALIZATION ---
if "available_models" not in st.session_state:
    st.session_state.available_models = {}
if "credentials" not in st.session_state:
    st.session_state.credentials = None
if "staged_files" not in st.session_state:
    st.session_state.staged_files = [] 
if "audit_results" not in st.session_state:
    st.session_state.audit_results = ""

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# # Load CSS
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# # Constants
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
@st.dialog("Google Drive Explorer", width="large")
def drive_explorer_dialog():
    # # Navigation logic for back button
    nav_col1, nav_col2 = st.columns([0.1, 0.9])
    if st.session_state.drive_current_folder != 'root':
        if nav_col1.button("⬅️"):
            st.session_state.drive_current_folder = st.session_state.drive_folder_stack.pop()
            st.rerun()
    
    nav_col2.subheader(f"Folder: {st.session_state.drive_current_folder}")
    st.divider()

    # # Fetch items from Google Drive API
    contents = list_user_drive_contents(st.session_state.drive_current_folder)
    
    if not contents:
        st.info("This folder is empty or has no supported code files.")

    for item in contents:
        col_icon, col_name, col_action = st.columns([0.05, 0.7, 0.25])
        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
        
        if is_folder:
            col_icon.write("📁")
            if col_name.button(item['name'], key=f"fld_{item['id']}", use_container_width=True):
                st.session_state.drive_folder_stack.append(st.session_state.drive_current_folder)
                st.session_state.drive_current_folder = item['id']
                st.rerun()
        else:
            col_icon.write("📄")
            col_name.write(item['name'])
            
            # # Check if already in the master staged_files list
            is_added = any(f.get('id') == item['id'] for f in st.session_state.staged_files)
            
            if is_added:
                col_action.button("Staged", key=f"btn_{item['id']}", disabled=True, use_container_width=True)
            else:
                if col_action.button("Add", key=f"btn_{item['id']}", use_container_width=True):
                    content = download_drive_file(item['id'])
                    if content:
                        st.session_state.staged_files.append({
                            "id": item['id'],
                            "name": item['name'],
                            "content": content,
                            "source": "Drive"
                        })
                        st.rerun()

# # --- GOOGLE UTILS ---
def list_user_drive_contents(folder_id='root'):
    if not st.session_state.credentials:
        return []
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        # # Query for folders and code-related files
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

# # Configuration Row
conf_col1, conf_col2 = st.columns([0.7, 0.3])

with conf_col1:
    try:
        models_resp = requests.get(f"{BACKEND_URL}/models", verify=False, timeout=2)
        if models_resp.status_code == 200:
            st.session_state.available_models = models_resp.json()
    except:
        if not st.session_state.available_models:
            st.session_state.available_models = {"GPT-4o": "gpt-4o-latest", "Grok 3": "grok-3"}

    # # Enforce max_selections=3 in the multiselect widget
    selected_labels = st.multiselect(
        "Select Audit Models (Max 3)", 
        options=list(st.session_state.available_models.keys()), 
        default=list(st.session_state.available_models.keys())[:2],
        max_selections=3
    )
    selected_ids = [st.session_state.available_models[name] for name in selected_labels]

st.divider()

# # File Ingestion
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
        # # If not logged in, show the login button here as well as the header
        flow = get_google_auth_flow()
        if flow:
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(
                f"""
                <a href="{auth_url}" target="_self">
                    <button style="
                        background-color: #4285F4;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: bold;
                        width: 100%;
                    ">
                        Sign in with Google
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )
        else:
            st.error("client_secrets.json not found.")
    else:
        # # If logged in, show the explorer trigger
        if st.button("📂 Open Drive Explorer", use_container_width=True):
            drive_explorer_dialog()
            
        # # Show a mini-list of Drive files currently in the audit stage
        drive_staged = [f for f in st.session_state.staged_files if f['source'] == "Drive"]
        if drive_staged:
            st.write("---")
            for i, f in enumerate(drive_staged):
                c_name, c_del = st.columns([0.8, 0.2])
                c_name.caption(f"☁️ {f['name']}")
                # # Find the index in the master list to delete correctly
                if c_del.button("🗑️", key=f"drive_del_{i}"):
                    st.session_state.staged_files = [sf for sf in st.session_state.staged_files if sf.get('id') != f.get('id')]
                    st.rerun()
        else:
            st.info("No Drive files added to audit.")

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
    
    # # Final Validation: Check for models and staged files
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

        st.session_state.audit_results = ""
        res_area = st.empty()
        payload = {"code": combined_code, "model_names": selected_ids, "user_message": audit_msg}
        try:
            with requests.post(f"{BACKEND_URL}/review", json=payload, stream=True, verify=False) as r:
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8').replace("data: ", ""))
                        st.session_state.audit_results += f"### 🤖 {data['model']}\n{data['review']}\n\n"
                        res_area.markdown(st.session_state.audit_results)
        except Exception as e:
            st.error(f"Audit failed: {e}")