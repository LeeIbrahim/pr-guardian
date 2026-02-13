import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide")

with st.sidebar:
    st.header("Model Comparison")
    
    model_options = {
        "GPT-4o": "gpt-4o",
        "Groq: Llama 3.3": "groq",
        "Together: Llama 3.3": "together",
        "Local: Llama 3.1": "local",
        "HF: CodeLlama 34B": "hf/codellama/CodeLlama-34b-Instruct-hf",
        "HF: WizardCoder 15B": "hf/WizardLMTeam/WizardCoder-15B-V1.0",
        "HF: StarCoder2 7B": "hf/bigcode/starcoder2-7b"
    }
    
    selected_labels = st.multiselect(
        "Select up to 3 models",
        options=list(model_options.keys()),
        default=["GPT-4o"],
        max_selections=3
    )
    selected_ids = [model_options[label] for label in selected_labels]

code_input = st.text_area("Paste Python Code:", height=300)

if "model_results" not in st.session_state:
    st.session_state.model_results = {}

# Helper: check if API key is present for a model
def check_missing_keys(model_id):
    missing = []
    if model_id.startswith("hf/") and not os.getenv("HUGGINGFACE_API_KEY"):
        missing.append("HUGGINGFACE_API_KEY")
    if model_id == "together" and not os.getenv("TOGETHER_API_KEY"):
        missing.append("TOGETHER_API_KEY")
    if model_id == "groq" and not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if model_id == "gpt-4o" and not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    return missing

# Show warnings for missing keys
all_missing = []
for m_id in selected_ids:
    all_missing.extend(check_missing_keys(m_id))

if all_missing:
    st.warning(
        "Warning: The following models may fail due to missing API keys: "
        + ", ".join(all_missing)
    )

def run_models(model_ids):
    with st.spinner("Analyzing selected models..."):
        try:
            resp = requests.post(
                "http://localhost:8000/review",
                json={
                    "code": code_input,
                    "thread_id": "comparison",
                    "model_names": model_ids
                }
            )
            resp.raise_for_status()
            return resp.json().get("reviews", {})
        except requests.exceptions.RequestException as e:
            return {m: f"ERROR: {str(e)}" for m in model_ids}

if st.button("Run Comparison Audit"):
    if code_input and selected_ids:
        st.session_state.model_results = run_models(selected_ids)

cols = st.columns(len(selected_ids))
for i, m_id in enumerate(selected_ids):
    with cols[i]:
        st.subheader(selected_labels[i])
        content = st.session_state.model_results.get(m_id, "No output yet.")
        if "ERROR:" in content:
            st.error(content)
            if st.button(f"Retry {selected_labels[i]}", key=f"retry_{m_id}"):
                retry_result = run_models([m_id])
                st.session_state.model_results[m_id] = retry_result.get(m_id, "No output returned.")
                st.experimental_rerun()
        else:
            st.markdown(content)
