# gui.py

import streamlit as st
import os
import json
import requests

def get_hf_status(model_id: str):
    if model_id.startswith("local/"): return "🏠 Local"
    if not model_id.startswith("hf/"): return "🟢 Ready"
    
    repo_id = model_id.split("/", 1)[1]
    api_url = f"https://router.huggingface.co/hf-inference/models/{repo_id}"
    hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    headers = {"Authorization": f("Bearer {hf_key}")}
    
    try:
        payload = {"inputs": "ping", "parameters": {"max_new_tokens": 1}, "use_cache": True}
        response = requests.post(api_url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200: return "🟢 Online"
        if response.status_code == 503: return "🟡 Loading"
        return "🔵 Active" 
    except:
        return "🔴 Offline"

with st.sidebar:
    st.title("Settings")
    
    model_options = {
        "GPT-4o": "gpt-4o",
        "Groq: Llama 3.3": "groq",
        "Local: Llama 3.2": "local/llama3.2:latest",
        "Local: DeepSeek R1": "local/deepseek-r1:1.5b",
        "HF: Qwen 2.5 Coder": "hf/Qwen/Qwen2.5-Coder-7B-Instruct"
    }

    if st.button("🗑️ Clear All Selection"):
        st.session_state.selected_models = []
        st.rerun()

    selected_labels = st.multiselect(
        "Select Models to Audit (Max 3)",
        options=list(model_options.keys()),
        max_selections=3,
        key="selected_models"
    )
    
    selected_ids = [model_options[label] for label in selected_labels]

    if selected_ids:
        st.divider()
        st.subheader("Model Status")
        for label in selected_labels:
            st.caption(f"**{label}**: {get_hf_status(model_options[label])}")

if not selected_ids:
    st.header("PR Guardian")
    st.info("Select a model in the sidebar to begin.")
    st.stop()

st.title("🔍 Code Security Audit")
code_input = st.text_area("Paste code here:", height=300, key="code_input")

if st.button("Run Multi-Model Audit"):
    if not code_input.strip():
        st.warning("Please enter code.")
    else:
        st.divider()
        completed_count = 0
        total_models = len(selected_ids)
        
        progress_bar = st.progress(0, text="Initializing requests...")
        
        # Create UI columns for the models
        cols = st.columns(total_models)
        placeholders = {}
        for idx, m_id in enumerate(selected_ids):
            with cols[idx]:
                st.subheader(f"🤖 {m_id.split('/')[-1]}")
                placeholders[m_id] = st.empty()
                placeholders[m_id].info("Waiting for results...")

        payload = {
            "code": code_input,
            "thread_id": "user-session-123",
            "model_names": selected_ids
        }

        try:
            # The backend handles all the async/parallel work
            # The GUI just listens to the stream
            with requests.post("http://127.0.0.1:8000/review", json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data = json.loads(decoded_line.replace("data: ", ""))
                            model_key = data['model']
                            review_content = data['review']
                            
                            with placeholders[model_key]:
                                st.markdown(review_content)
                            
                            completed_count += 1
                            progress_val = int((completed_count / total_models) * 100)
                            progress_bar.progress(progress_val, text=f"Received: {model_key}")
                            
            st.success("All audits completed!")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")