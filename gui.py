# gui.py

import streamlit as st
import asyncio
import os
import requests
from src.pr_guardian.main import run_model

def get_hf_status(model_id: str):
    if model_id.startswith("local/"): return "🏠 Local"
    if not model_id.startswith("hf/"): return "🟢 Ready"
    
    repo_id = model_id.split("/", 1)[1]
    # Ping the 2026 router for model availability
    api_url = f"https://router.huggingface.co/hf-inference/models/{repo_id}"
    hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    headers = {"Authorization": f"Bearer {hf_key}"}
    
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
    
    # Selection list updated to include Local Llama and stable HF options
    model_options = {
        "GPT-4o": "gpt-4o",
        "Groq: Llama 3.3": "groq",
        "Local: Llama 3.2": "local/llama3.2:latest",
        "HF: DeepSeek R1": "hf/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "HF: Qwen 2.5 Coder": "hf/Qwen/Qwen2.5-Coder-7B-Instruct"
    }

    if st.button("🗑️ Clear All Selection"):
        st.session_state.selected_models = []
        st.rerun()

    selected_labels = st.multiselect(
        "Select Models to Audit (Max 3)",
        options=list(model_options.keys()),
        max_selections=3, # User can't pick more than 3
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
    st.info("Select a model to begin.")
    st.stop()

st.title("🔍 Code Security Audit")
code_input = st.text_area("Paste code here:", height=300)

if st.button("Run Multi-Model Audit"):
    if not code_input.strip():
        st.warning("Please enter code.")
    else:
        st.divider()
        cols = st.columns(len(selected_ids))
        async def perform_audits():
            tasks = [run_model(code_input, m_id, "user-thread") for m_id in selected_ids]
            return await asyncio.gather(*tasks)

        results = asyncio.run(perform_audits())
        for i, (m_id, content) in enumerate(results):
            with cols[i]:
                label = [k for k, v in model_options.items() if v == m_id][0]
                st.subheader(label)
                st.markdown(content)