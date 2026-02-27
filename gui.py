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

# # Suppress warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# # --- INITIALIZATION ---
# # Initialize session state variables to ensure persistence across reruns
if "available_models" not in st.session_state:
    st.session_state.available_models = {}
if "credentials" not in st.session_state:
    st.session_state.credentials = None
if "drive_files" not in st.session_state:
    st.session_state.drive_files = [] 
if "drive_current_folder" not in st.session_state:
    st.session_state.drive_current_folder = 'root'
if "drive_folder_stack" not in st.session_state:
    st.session_state.drive_folder_stack = []
if "show_explorer" not in st.session_state:
    st.session_state.show_explorer = False
if "audit_results" not in st.session_state:
    st.session_state.audit_results = ""

st.set_page_config(
    page_title="PR Guardian", 
    page_icon="🛡️", 
    layout="wide"
)

# # Constants
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.readonly']
REDIRECT_URI = os.getenv("URI_REDIRECT", "https://localhost:8501/") 
BACKEND_URL = os.getenv("BACKEND_URL", "https://127.0.0.1:8000")

SUPPORTED_EXTENSIONS = (
    ".py", ".rs", ".cpp", ".hpp", ".c", ".h", ".php", ".cs", 
    ".js", ".jsx", ".ts", ".tsx", ".bas", ".vb", ".java", ".go"
)

def fetch_models():
    try:
        resp = requests.get(f"{BACKEND_URL}/models", verify=False, timeout=5)
        if resp.status_code == 200:
            st.session_state.available_models = resp.json()
    except Exception:
        pass

# Trigger initial fetch if the state is currently empty
if not st.session_state.available_models:
    fetch_models()

def get_auth_flow():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return None
    return Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)

def list_drive_contents(folder_id='root'):
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        ext_query = " or ".join([f"name contains '{ext}'" for ext in SUPPORTED_EXTENSIONS])
        query = f"('{folder_id}' in parents) and (mimeType = 'application/vnd.google-apps.folder' or {ext_query})"
        results = service.files().list(q=query, fields="files(id, name, mimeType)", orderBy="folder,name").execute()
        return results.get('files', [])
    except Exception:
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
        return fh.getvalue().decode('utf-8', errors='ignore')
    except Exception:
        return None

@st.dialog("Google Drive Browser", width="large")
def drive_explorer_dialog():
    c1, c2 = st.columns([0.1, 0.9])
    if st.session_state.drive_current_folder != 'root':
        if c1.button("⬅️", key="dlg_back"):
            st.session_state.drive_current_folder = st.session_state.drive_folder_stack.pop()
            st.rerun()
    c2.write(f"📁 **Location:** `/{st.session_state.drive_current_folder}`")
    st.divider()

    items = list_drive_contents(st.session_state.drive_current_folder)
    grid = st.columns(4) 
    for idx, item in enumerate(items):
        with grid[idx % 4]:
            is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
            icon = "📁" if is_folder else "📄"
            st.markdown(f"<div style='text-align: center; font-size: 35px;'>{icon}</div>", unsafe_allow_html=True)
            display_name = (item['name'][:15] + '..') if len(item['name']) > 18 else item['name']
            
            if is_folder:
                if st.button(display_name, key=f"f_{item['id']}", use_container_width=True):
                    st.session_state.drive_folder_stack.append(st.session_state.drive_current_folder)
                    st.session_state.drive_current_folder = item['id']
                    st.rerun()
            else:
                if st.button(display_name, key=f"a_{item['id']}", help=item['name'], use_container_width=True):
                    if not any(f['id'] == item['id'] for f in st.session_state.drive_files):
                        content = download_drive_file(item['id'])
                        if content:
                            st.session_state.drive_files.append({"id": item['id'], "name": item['name'], "content": content})
                            st.rerun()

# MAIN UI

st.title("🛡️ PR Guardian")

# MODEL SELECTOR (3-MODEL LIMIT)
with st.container(border=True):
    if st.session_state.available_models:
        model_options = list(st.session_state.available_models.keys())
        
        selected_labels = st.multiselect(
            "Select Models for Review (Max 3)", 
            options=model_options, 
            default=[model_options[0]] if model_options else None,
            label_visibility="collapsed"
        )
        
        if len(selected_labels) > 3:
            st.warning("⚠️ Only 3 models can be selected at once. Trimming selection.")
            selected_labels = selected_labels[:3]
            
        selected_ids = [st.session_state.available_models[l] for l in selected_labels]
    else:
        st.warning("📡 No models detected. Check if the backend is running at 127.0.0.1:8000.")
        if st.button("🔌 Reconnect"):
            fetch_models()
            st.rerun()
        selected_ids = []

st.divider()

# Handle OAuth Redirect
if "code" in st.query_params and st.session_state.credentials is None:
    flow = get_auth_flow()
    if flow:
        flow.fetch_token(code=st.query_params["code"])
        st.session_state.credentials = flow.credentials
        st.query_params.clear()
        st.rerun()

# Staging Area
if st.session_state.drive_files:
    st.subheader("Staged Files")
    st.markdown('<div class="staged-container">', unsafe_allow_html=True)
    chips = st.columns(6)
    for idx, f in enumerate(st.session_state.drive_files):
        with chips[idx % 6]:
            with st.container(border=True):
                st.write(f"📄 {f['name'][:10]}")
                if st.button("✕", key=f"del_{f['id']}"):
                    st.session_state.drive_files = [x for x in st.session_state.drive_files if x['id'] != f['id']]
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Input Selection
col_l, col_g, col_d = st.columns(3)

with col_l:
    st.subheader("📁 Local")
    uploaded_files = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")

with col_g:
    st.subheader("🌐 GitHub")
    repo_path = st.text_input("Repo Path", placeholder="owner/repo", label_visibility="collapsed")

with col_d:
    st.subheader("☁️ Drive")
    if st.session_state.credentials:
        if st.button("📂 Browse Files", use_container_width=True):
            st.session_state.show_explorer = True
        if st.session_state.show_explorer:
            drive_explorer_dialog()
    else:
        flow = get_auth_flow()
        if flow:
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.link_button("🔑 Login to Drive", auth_url, use_container_width=True, type="primary")

st.divider()
audit_instructions = st.text_area("Audit Instructions (Optional)", placeholder="e.g. Focus on security...", height=100)

_, mid, _ = st.columns([0.3, 0.4, 0.3])
with mid:
    if st.button("🚀 Run Audit", type="primary", use_container_width=True):
        combined_code = ""
        for df in st.session_state.drive_files:
            combined_code += f"\n# --- FILE: {df['name']} (Drive) ---\n{df['content']}\n"
        
        if uploaded_files:
            for lf in uploaded_files:
                combined_code += f"\n# --- FILE: {lf.name} (Local) ---\n{lf.getvalue().decode('utf-8')}\n"

        if not combined_code:
            st.error("Please stage at least one file before auditing.")
        elif not selected_ids:
            st.warning("Please select a model.")
        else:
            st.session_state.audit_results = ""
            results_area = st.empty()
            payload = {"code": combined_code, "model_names": selected_ids, "user_message": audit_instructions}

            try:
                # verify=False for local SSL certs; stream=True for real-time model output
                # TODO: In production, ensure proper SSL certificates and remove verify=False for secure communication.
                with requests.post(f"{BACKEND_URL}/review", json=payload, stream=True, verify=False) as r:
                    if r.status_code == 200:
                        for line in r.iter_lines():
                            if line:
                                data = json.loads(line.decode('utf-8').replace("data: ", ""))
                                st.session_state.audit_results += f"### 🤖 Model: {data['model']}\n{data['review']}\n\n"
                                results_area.markdown(st.session_state.audit_results)
                    else:
                        st.error(f"Backend Error: {r.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

if st.session_state.audit_results and not mid:
    st.markdown("---")
    st.markdown(st.session_state.audit_results)