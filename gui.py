# gui.py
import streamlit as st
import requests
import json
import os
import base64
import urllib3
import io
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Suppress local HTTPS warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# Google Configuration
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly'
]
# Ensure this matches your Google Cloud Console exactly
REDIRECT_URI = "https://localhost:8501/" 
BACKEND_URL = os.getenv("BACKEND_URL", "https://localhost:8000")

# Session state initialization
if "credentials" not in st.session_state:
    st.session_state.credentials = None
if "audit_results" not in st.session_state:
    st.session_state.audit_results = {}
if "github_files" not in st.session_state:
    st.session_state.github_files = []
if "drive_files" not in st.session_state:
    st.session_state.drive_files = []

# --- GOOGLE AUTH LOGIC ---

def get_auth_flow():
    # If this file isn't in your folder, the 'Login' button won't appear
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return None
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

def list_user_drive_files():
    # Only lists files the user has given us access to or common code files
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        query = "mimeType = 'text/x-python' or name contains '.py' or name contains '.js'"
        results = service.files().list(pageSize=10, q=query, fields="files(id, name)").execute()
        return results.get('files', [])
    except Exception as e:
        st.sidebar.error(f"Drive List Error: {e}")
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
        st.error(f"Failed to grab file: {e}")
        return None

# --- AUTH CALLBACK HANDLER ---
# Streamlit reads the 'code' from the URL after Google redirects back
if "code" in st.query_params and st.session_state.credentials is None:
    flow = get_auth_flow()
    if flow:
        flow.fetch_token(code=st.query_params["code"])
        st.session_state.credentials = flow.credentials
        st.success("Successfully authenticated with Google!")
        # Clear the code from the URL for a clean UI
        st.query_params.clear()

# --- UI LAYOUT ---

st.title("🛡️ PR Guardian")

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Login/Logout Toggle
    if not st.session_state.credentials:
        flow = get_auth_flow()
        if flow:
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.link_button("🔑 Login with Google", auth_url, use_container_width=True)
        else:
            st.warning("client_secrets.json missing.")
    else:
        st.success("Connected to Google Drive")
        if st.button("Logout", use_container_width=True):
            st.session_state.credentials = None
            st.rerun()
    
    st.divider()
    # Model selection from backend
    try:
        models_resp = requests.get(f"{BACKEND_URL}/models", verify=False, timeout=2)
        available_models = models_resp.json() if models_resp.status_code == 200 else {}
    except:
        available_models = {}

    selected_labels = st.multiselect("Models", list(available_models.keys()), max_selections=3)
    selected_ids = [available_models[name] for name in selected_labels]

# --- INPUT COLUMNS ---
st.markdown('<div class="paper-wrapper">', unsafe_allow_html=True)
col_local, col_github, col_drive = st.columns(3)

with col_local:
    st.subheader("📁 Local")
    uploaded = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")

with col_github:
    st.subheader("🌐 GitHub")
    repo = st.text_input("Repo", placeholder="owner/repo", label_visibility="collapsed")
    if st.button("Fetch Files"):
        # Existing GitHub logic goes here
        pass

with col_drive:
    st.subheader("☁️ Google Drive")
    if st.session_state.credentials:
        user_files = list_user_drive_files()
        if user_files:
            file_options = {f['name']: f['id'] for f in user_files}
            selected_file_name = st.selectbox("Pick a file", list(file_options.keys()))
            if st.button("Grab Code"):
                content = download_drive_file(file_options[selected_file_name])
                if content:
                    st.session_state.drive_files = [{"name": selected_file_name, "content": content}]
                    st.toast(f"Imported {selected_file_name}")
        else:
            st.info("No supported files found in Drive.")
    else:
        st.info("Login to access your Drive.")

# Display items ready for audit
if uploaded or st.session_state.github_files or st.session_state.drive_files:
    st.markdown("### Ready for Audit:")
    for df in st.session_state.drive_files:
        st.info(f"☁️ {df['name']} (from your Google Drive)")

if st.button("🚀 Start Audit", type="primary", use_container_width=True):
    # Consolidate code and send to backend
    pass

st.markdown('</div>', unsafe_allow_html=True)