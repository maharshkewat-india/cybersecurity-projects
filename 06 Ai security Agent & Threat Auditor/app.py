import streamlit as st
from groq import AuthenticationError, GroqError

from agent import run_security_agent

# Page Configuration
st.set_page_config(
    page_title="AI Cybersecurity Agent",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for UI styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stTextArea textarea {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 8px;
    }
    .stButton button {
        background-color: #238636;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        width: 100%;
    }
    .stButton button:hover {
        background-color: #2ea043;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar UI
with st.sidebar:
    st.image("https://img.icons8.com/color/96/cyber-security.png", width=80)
    st.title("Cyber Agent Panel")
    st.info(
        "AI-assisted defensive analysis of user-provided text. The app does not "
        "connect to or scan the supplied target."
    )
    st.markdown("---")
    st.markdown("**Technologies Used:**")
    st.markdown("- Python & Streamlit")
    st.markdown("- Groq LLM (GPT-OSS 120B)")
    st.markdown("- On-demand model analysis")

# Main Interface Header
st.title("🛡️ AI Security Agent & Threat Auditor")
st.markdown("##### AI-assisted defensive guidance")
st.markdown("---")

def load_sample(value: str) -> None:
    st.session_state["target_input"] = value


# Layout columns for UI
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Target Input Panel")
    target_input = st.text_area(
        "Enter a suspicious URL, IP address, or server-log snippet:",
        placeholder="e.g., Failed password for root from 192.168.1.50 port 22 ssh2",
        height=150,
        key="target_input",
    )

with col2:
    st.subheader("💡 Quick Test Samples")
    st.markdown("Click below to load sample logs:")
    st.button(
        "Load Brute-Force Log",
        on_click=load_sample,
        args=("Failed password for root from 192.168.1.100 port 22",),
    )
    st.button(
        "Load Suspicious URL",
        on_click=load_sample,
        args=("http://malicious-login-verify-account-update.com/signin",),
    )

# Analysis trigger button
if st.button("🚀 Run AI Security Analysis", use_container_width=True):
    if not target_input.strip():
        st.warning("⚠️ Please enter a valid target or log text before running the scan!")
    else:
        with st.spinner("🤖 AI assistant is reviewing the supplied text..."):
            try:
                result = run_security_agent(target_input)
                st.success("✅ Analysis Completed Successfully!")
                st.markdown("---")
                st.markdown("### 📊 Comprehensive Threat Audit Report")
                st.markdown(result)
            except AuthenticationError:
                st.error(
                    "Groq rejected the API key (401 Unauthorized). Create a new "
                    "API key in your Groq account, replace GROQ_API_KEY in the "
                    "project's .env file, and restart Streamlit. Do not share "
                    "the key in chat or commit it."
                )
            except (GroqError, RuntimeError) as e:
                st.error(f"❌ An error occurred during agent execution: {e}")
