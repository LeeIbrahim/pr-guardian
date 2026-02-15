# gui.py

import streamlit as st
import json
import requests

st.set_page_config(layout="wide")

# Initialize session state for individual model results
if "audit_results" not in st.session_state:
    st.session_state.audit_results = {}

def run_single_audit(m_id, code, thread_id, sequential):
    # Helper to call the backend for one specific model
    payload = {
        "code": code,
        "model_names": [m_id],
        "thread_id": thread_id,
        "sequential": sequential
    }
    try:
        with requests.post("http://127.0.0.1:8000/review", json=payload, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8').replace("data: ", "")
                    data = json.loads(decoded)
                    return data['review']
    except Exception as e:
        return f"ERROR: {str(e)}"

with st.sidebar:
    st.title("Settings")
    model_options = {
        "GPT-4o": "gpt-4o",
        "Groq: Llama 3.3": "groq",
        "Local: Llama 3.2": "local/llama3.2:latest",
        "Local: DeepSeek R1": "local/deepseek-r1:1.5b",
        "HF: Phi-3": "hf/microsoft/Phi-3-mini-4k-instruct"
    }

    selected_labels = st.multiselect(
        "Select Models to Audit", 
        list(model_options.keys()), 
        default=["GPT-4o"],
        key="selected_models"
    )
    selected_ids = [model_options[l] for l in selected_labels]
    
    st.divider()
    is_seq = st.toggle("Sequential Mode", help="Chains models together.")

st.title("🔍 Code Security Audit")
code_input = st.text_area("Paste code here:", height=200)

if st.button("Run Multi-Model Audit"):
    if not code_input.strip():
        st.warning("Please enter code.")
    else:
        st.session_state.audit_results = {m_id: "🔄 Auditing..." for m_id in selected_ids}
        
        # We run the initial batch audit
        payload = {
            "code": code_input,
            "model_names": selected_ids,
            "thread_id": f"audit-{hash(code_input)}",
            "sequential": is_seq
        }
        
        try:
            with requests.post("http://127.0.0.1:8000/review", json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').replace("data: ", "")
                        data = json.loads(decoded)
                        st.session_state.audit_results[data['model']] = data['review']
                        st.rerun() # Refresh to show stream
        except Exception as e:
            st.error(f"Connection error: {e}")

# Side-by-Side Display Logic
if st.session_state.audit_results:
    cols = st.columns(len(selected_ids))
    for i, m_id in enumerate(selected_ids):
        with cols[i]:
            friendly_name = [k for k, v in model_options.items() if v == m_id][0]
            st.subheader(f"🤖 {friendly_name}")
            
            content = st.session_state.audit_results.get(m_id, "Waiting...")
            
            with st.container(height=500, border=True):
                st.markdown(content)
            
            # Show Rerun button if the result contains an ERROR or if user wants to refresh
            if "ERROR" in content or "Error" in content:
                if st.button(f"Retry {friendly_name}", key=f"retry_{m_id}"):
                    st.session_state.audit_results[m_id] = "🔄 Retrying..."
                    new_result = run_single_audit(m_id, code_input, f"audit-{hash(code_input)}", is_seq)
                    st.session_state.audit_results[m_id] = new_result
                    st.rerun()