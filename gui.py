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

# Suppress warnings for self-signed certificates
# TODO: WARNING - This is not recommended for production environments. Ensure proper SSL certificates are in place for secure communication.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

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

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "https://127.0.0.1:8000")
SUPPORTED_EXTENSIONS = (".py", ".rs", ".cpp", ".hpp", ".c", ".h", ".php", ".cs", ".js", ".jsx", ".ts", ".tsx", ".bas", ".vb", ".java", ".go")

def fetch_models():
    try:
        resp = requests.get(f"{BACKEND_URL}/models", verify=False, timeout=5)
        if resp.status_code == 200:
            st.session_state.available_models = resp.json()
    except Exception:
        pass

if not st.session_state.available_models:
    fetch_models()

st.title("🛡️ PR Guardian")

with st.container(border=True):
    if st.session_state.available_models:
        model_options = list(st.session_state.available_models.keys())
        selected_labels = st.multiselect(
            "Select Models for Review", 
            options=model_options, 
            default=[model_options[0]] if model_options else None,
            label_visibility="collapsed"
        )
        selected_ids = [st.session_state.available_models[l] for l in selected_labels]
    else:
        st.warning("📡 No models detected. Ensure the backend is running.")
        if st.button("🔌 Reconnect to Backend"):
            fetch_models()
            st.rerun()
        selected_ids = []

st.divider()

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
    else:
        st.info("Log in to Drive to browse files.")

st.divider()
audit_instructions = st.text_area("Audit Instructions (Optional)", height=100)

_, mid, _ = st.columns([0.3, 0.4, 0.3])
with mid:
    if st.button("🚀 Run Audit", type="primary", use_container_width=True):
        combined_code = ""

        if not combined_code:
            st.error("No code staged for review.")
        elif not selected_ids:
            st.warning("Please select at least one model.")
        else:
            st.session_state.audit_results = ""
            results_area = st.empty()
            payload = {"code": combined_code, "model_names": selected_ids, "user_message": audit_instructions}
            try:
                with requests.post(f"{BACKEND_URL}/review", json=payload, stream=True, verify=False) as r:
                    if r.status_code == 200:
                        for line in r.iter_lines():
                            if line:
                                data = json.loads(line.decode('utf-8').replace("data: ", ""))
                                st.session_state.audit_results += f"### 🤖 Model: {data['model']}\n{data['review']}\n\n"
                                results_area.markdown(st.session_state.audit_results)
            except Exception as e:
                st.error(f"Audit failed: {e}")

if st.session_state.audit_results and not mid:
    st.markdown("---")
    st.markdown(st.session_state.audit_results)