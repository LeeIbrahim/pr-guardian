import streamlit as st
import requests
import json

st.set_page_config(page_title="PR Guardian", page_icon="🛡️", layout="wide")

# Persistent storage for results
if "audit_results" not in st.session_state:
    st.session_state.audit_results = {}

def fetch_available_models():
    try:
        # Use https and verify=False to match your uvicorn SSL launch
        response = requests.get("https://localhost:8000/models", verify=False, timeout=2)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

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