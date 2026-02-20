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

# Drive Navigation Keys
if "drive_files" not in st.session_state:
    st.session_state.drive_files = []
if "drive_current_folder" not in st.session_state:
    st.session_state.drive_current_folder = 'root'
if "drive_folder_stack" not in st.session_state:
    st.session_state.drive_folder_stack = []

@st.dialog("Google Drive File Viewer", width="large")
def drive_viewer_dialog():
    st.write("Select code files from your Drive to include in the audit.")
    
    # Fetch current files from user's drive
    drive_contents = list_user_drive_files() 
    
    if not drive_contents:
        st.info("No supported code files found in your Drive.")
        return

    # Table Header
    cols = st.columns([0.6, 0.2, 0.2])
    cols[0].write("**File Name**")
    cols[1].write("**Type**")
    cols[2].write("**Action**")
    st.divider()

    for f in drive_contents:
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        
        # Determine file type icon
        icon = "🐍" if f['name'].endswith('.py') else "📜"
        c1.write(f"{icon} {f['name']}")
        
        ext = f['name'].split('.')[-1].upper() if '.' in f['name'] else "FILE"
        c2.write(f"`{ext}`")

        # Check if already added to state
        is_added = any(df['id'] == f['id'] for df in st.session_state.drive_files)

        if is_added:
            c3.button("Added", key=f"btn_{f['id']}", disabled=True, use_container_width=True)
        else:
            if c3.button("Add", key=f"btn_{f['id']}", use_container_width=True):
                content = download_drive_file(f['id'])
                if content:
                    st.session_state.drive_files.append({
                        "id": f['id'],
                        "name": f['name'],
                        "content": content
                    })
                    st.rerun() # Refresh to update "Added" status

# --- FILE REMOVAL HELPER ---
def unadd_drive_file(file_id):
    st.session_state.drive_files = [
        f for f in st.session_state.drive_files if f['id'] != file_id
    ]

def get_auth_flow():
    # If this file isn't in your folder, the 'Login' button won't appear
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return None
    return Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

# gui.py

def list_user_drive_contents(folder_id='root'):
    try:
        service = build('drive', 'v3', credentials=st.session_state.credentials)
        # Query: Look for code files OR folders within the specific folder_id
        query = f"('{folder_id}' in parents) and (mimeType = 'application/vnd.google-apps.folder' or name contains '.py' or name contains '.js')"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            orderBy="folder,name" # Folders first, then alphabetically
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.sidebar.error(f"Drive Error: {e}")
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

@st.dialog("Google Drive Explorer", width="large")
def drive_explorer_dialog():
    # Navigation header
    nav_col1, nav_col2 = st.columns([0.1, 0.9])
    
    # Back button: Only shows if we aren't at the root
    if st.session_state.drive_current_folder != 'root':
        if nav_col1.button("⬅️", help="Go back"):
            # Pull the previous folder ID from the stack
            st.session_state.drive_current_folder = st.session_state.drive_folder_stack.pop()
            st.rerun()
    
    nav_col2.subheader(f"Current Folder ID: `{st.session_state.drive_current_folder}`")
    st.divider()

    # Fetch contents for the current folder
    contents = list_user_drive_contents(st.session_state.drive_current_folder)
    
    if not contents:
        st.info("This folder is empty or contains no supported code files.")

    for item in contents:
        col_icon, col_name, col_action = st.columns([0.05, 0.7, 0.25])
        
        # Check if it's a folder or a file
        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
        
        if is_folder:
            col_icon.write("📁")
            # Clicking the folder name updates the current folder ID
            if col_name.button(item['name'], key=f"folder_{item['id']}", use_container_width=True):
                # Save where we were so we can go back
                st.session_state.drive_folder_stack.append(st.session_state.drive_current_folder)
                st.session_state.drive_current_folder = item['id']
                st.rerun()
        else:
            col_icon.write("📄")
            col_name.write(item['name'])
            
            # Check if this specific file ID is already in our audit list
            already_added = any(f['id'] == item['id'] for f in st.session_state.drive_files)
            
            if already_added:
                col_action.button("Added", key=f"add_{item['id']}", disabled=True, use_container_width=True)
            else:
                if col_action.button("Add", key=f"add_{item['id']}", use_container_width=True):
                    file_content = download_drive_file(item['id'])
                    if file_content:
                        # Append only this specific file to the list
                        st.session_state.drive_files.append({
                            "id": item['id'],
                            "name": item['name'],
                            "content": file_content
                        })
                        st.rerun()

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

# Inside the col_drive block in the main app

with col_drive:
    st.subheader("☁️ Google Drive")
    if st.session_state.credentials:
        if st.button("📂 Open Drive Explorer", use_container_width=True):
            drive_explorer_dialog()
            
        if st.session_state.drive_files:
            st.write("---")
            # Loop through the list and create a unique button for each file
            for file_obj in st.session_state.drive_files:
                f_col, b_col = st.columns([0.8, 0.2])
                f_col.info(f"☁️ {file_obj['name']}")
                
                # The 'key' argument here is what makes it specific!
                if b_col.button("🗑️", key=f"del_{file_obj['id']}"):
                    # Filter the list to keep everything EXCEPT this ID
                    st.session_state.drive_files = [
                        f for f in st.session_state.drive_files if f['id'] != file_obj['id']
                    ]
                    st.rerun()
    else:
        st.info("Log in via sidebar to view Drive.")

# Display items ready for audit
if uploaded or st.session_state.github_files or st.session_state.drive_files:
    st.markdown("### Ready for Audit:")
    for df in st.session_state.drive_files:
        st.info(f"☁️ {df['name']} (from your Google Drive)")

if st.button("🚀 Start Audit", type="primary", use_container_width=True):
    # Consolidate code and send to backend
    pass

st.markdown('</div>', unsafe_allow_html=True)