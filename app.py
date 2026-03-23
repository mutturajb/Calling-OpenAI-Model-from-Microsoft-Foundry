"""
Azure OpenAI chat (Microsoft Foundry) — learning example.

Run in a terminal:
    streamlit run app.py

What this file does (in order):
    1. Read secrets from a .env file
    2. Build an Azure OpenAI client
    3. Show a chat page; send with the Send button; Clear resets history
"""

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------

import os
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAIError


# -----------------------------------------------------------------------------
# 2. Constants (defaults you can change)
# -----------------------------------------------------------------------------

DEFAULT_API_VERSION = "2024-10-21"
DEFAULT_DEPLOYMENT_NAME = "DeepSeek-V3.2"
SYSTEM_PROMPT = "You are a helpful assistant."


# -----------------------------------------------------------------------------
# 3. Helper functions
# -----------------------------------------------------------------------------


def fix_foundry_endpoint(url: str) -> str:
    """
    Sometimes the Azure portal shows a long “project” URL like:
        https://xxx.services.ai.azure.com/api/projects/my-project

    The Python SDK expects the shorter resource URL:
        https://xxx.services.ai.azure.com
    """
    url = url.strip().rstrip("/")
    if not url:
        return url

    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    path = parts.path or ""

    if "services.ai.azure.com" in host and "/api/projects" in path:
        return f"{parts.scheme}://{parts.netloc}"

    return url


def read_env_settings():
    """Load variables from .env into a dictionary."""
    load_dotenv()

    raw_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    if not raw_endpoint:
        raw_endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT", "").strip()

    endpoint_url = fix_foundry_endpoint(raw_endpoint)
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()

    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "").strip()
    if not deployment:
        deployment = DEFAULT_DEPLOYMENT_NAME

    api_version = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION).strip()
    if not api_version:
        api_version = DEFAULT_API_VERSION

    return {
        "endpoint_url": endpoint_url,
        "api_key": api_key,
        "deployment": deployment,
        "api_version": api_version,
    }


def check_required_settings(settings: dict) -> list:
    """Return a list of missing setting names (empty = OK)."""
    missing = []
    if not settings["endpoint_url"]:
        missing.append("AZURE_OPENAI_ENDPOINT (or AZURE_INFERENCE_ENDPOINT)")
    if not settings["api_key"]:
        missing.append("AZURE_OPENAI_API_KEY")
    return missing


def openai_error_text(error: OpenAIError) -> str:
    """Turn an OpenAI / HTTP error into a string we can show on screen."""
    text = str(error)
    response = getattr(error, "response", None)
    if response is not None:
        try:
            body = response.text or ""
            if body.strip():
                text = text + "\n\n" + body.strip()
        except Exception:
            pass
    return text


def inject_app_styles() -> None:
    """Light theme: fonts and spacing (Streamlit theme in .streamlit/config.toml)."""
    st.markdown(
        """
<style>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap");

html, body, [data-testid="stAppViewContainer"] {
  font-family: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
}

[data-testid="stAppViewContainer"] {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
}

.block-container {
  max-width: 900px !important;
  padding-top: 1.5rem !important;
}

.pro-title-wrap {
  padding: 1.25rem 1.5rem;
  margin: 0 0 1.5rem 0;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
}

.pro-title {
  margin: 0;
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #0f172a;
}

.pro-subtitle {
  margin: 0.4rem 0 0 0;
  font-size: 0.92rem;
  font-weight: 500;
  color: #64748b;
}

[data-testid="stChatMessage"] {
  border-radius: 12px !important;
  border: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
  margin-bottom: 0.75rem !important;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06) !important;
}

[data-testid="stForm"] {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem 1rem 0.75rem 1rem;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-right: 1px solid #e2e8f0;
}

footer { visibility: hidden; height: 0; }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header() -> None:
    """Title and subtitle shown at the top of the main area."""
    st.markdown(
        """
<div class="pro-title-wrap">
  <p class="pro-title">Foundry Chat</p>
  <p class="pro-subtitle">Azure OpenAI · Microsoft Foundry</p>
</div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 4. Main program
# -----------------------------------------------------------------------------


def main():
    st.set_page_config(
        page_title="Foundry Chat",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_app_styles()
    render_page_header()

    settings = read_env_settings()
    missing = check_required_settings(settings)

    if missing:
        st.error(
            "Missing values in `.env`. Copy `.env.example` to `.env` and set: "
            + ", ".join(missing)
        )
        st.stop()

    client = AzureOpenAI(
        azure_endpoint=settings["endpoint_url"],
        api_key=settings["api_key"],
        api_version=settings["api_version"],
    )
    deployment_name = settings["deployment"]

    # Sidebar: session controls and deployment info
    with st.sidebar:
        st.markdown("### Session")
        st.caption("Clear removes all messages in this browser session.")
        if st.button("Clear conversation", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.markdown("**Active deployment**")
        st.code(deployment_name, language=None)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input: text area + Send (form clears the box after submit)
    with st.form("message_form", clear_on_submit=True):
        st.markdown("**Your message**")
        user_text = st.text_area(
            "Message",
            height=120,
            placeholder="Write your question here, then click Send.",
            label_visibility="collapsed",
        )
        send = st.form_submit_button("Send", type="primary", use_container_width=False)

    if send and user_text and user_text.strip():
        user_text = user_text.strip()
        st.session_state.messages.append({"role": "user", "content": user_text})

        messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_for_api.extend(st.session_state.messages)

        with st.spinner("Waiting for the model…"):
            try:
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=messages_for_api,
                )
            except OpenAIError as e:
                st.session_state.messages.pop()
                st.error(openai_error_text(e))
                st.stop()

            assistant_text = response.choices[0].message.content or ""

        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        st.rerun()


if __name__ == "__main__":
    main()
