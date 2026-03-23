"""
Microsoft Foundry chat — Azure AI Projects client + Microsoft Entra ID

Run:
    streamlit run app.py

Before running:
    az login

Configuration (`.env` — only *where* to call and *which* deployment; no API keys):
    AZURE_AI_PROJECT_ENDPOINT   — your Foundry project URL from the portal
    AZURE_AI_MODEL_DEPLOYMENT_NAME — model deployment name in Foundry

How auth works (no secrets in `.env`):
    DefaultAzureCredential() uses your `az login` session (or other Azure dev
    credentials). AIProjectClient exchanges that for tokens to call Azure AI.

How the SDK fits together:
    1) AIProjectClient(endpoint, credential)  — Foundry *project* entry point
    2) get_openai_client()  — returns openai.OpenAI wired to …/openai/v1 + bearer token
    3) chat.completions.create(model=deployment, messages=…)  — chat with your deployment
"""

# -----------------------------------------------------------------------------
# 1. Imports
# -----------------------------------------------------------------------------

import os

import streamlit as st
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from openai import OpenAIError

# -----------------------------------------------------------------------------
# 2. Constants
# -----------------------------------------------------------------------------

DEFAULT_DEPLOYMENT_NAME = "DeepSeek-V3.2"
SYSTEM_PROMPT = "You are a helpful assistant."


# -----------------------------------------------------------------------------
# 3. Settings (only endpoint + deployment — identity comes from `az login`)
# -----------------------------------------------------------------------------


def read_settings() -> dict:
    """Load `.env`. API keys are not used; sign in with `az login` instead."""
    load_dotenv()

    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "").strip()
    deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "").strip()
    if not deployment:
        deployment = DEFAULT_DEPLOYMENT_NAME

    return {
        "project_endpoint": project_endpoint,
        "deployment_name": deployment,
    }


def missing_settings(settings: dict) -> list[str]:
    """Only the project URL is required; deployment defaults in code if unset."""
    if not settings["project_endpoint"]:
        return ["AZURE_AI_PROJECT_ENDPOINT"]
    return []


def api_error_text(exc: BaseException) -> str:
    text = str(exc)
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            body = response.text or ""
            if body.strip():
                text = text + "\n\n" + body.strip()
        except Exception:
            pass
    return text


# -----------------------------------------------------------------------------
# 4. Azure AI Projects client → OpenAI SDK (cached for Streamlit reruns)
# -----------------------------------------------------------------------------


@st.cache_resource
def openai_client_from_project(project_endpoint: str):
    """
    Privileged Foundry flow (Entra ID only):

    - AIProjectClient: official Azure AI *Projects* SDK for your workspace.
    - get_openai_client(): hands you openai.OpenAI with the right base URL and
      token provider (scope https://ai.azure.com/.default — handled inside SDK).

    Requires: `az login` (or another credential DefaultAzureCredential understands).
    """
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    # Keep AIProjectClient alive for the lifetime of the cached OpenAI client (do not
    # use a `with` block here — closing the project can invalidate the returned client).
    project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)
    return project_client.get_openai_client()


# -----------------------------------------------------------------------------
# 5. UI
# -----------------------------------------------------------------------------


def inject_app_styles() -> None:
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
    st.markdown(
        """
<div class="pro-title-wrap">
  <p class="pro-title">Foundry Chat</p>
  <p class="pro-subtitle">Azure AI Projects · Entra ID (`az login`) · no API key in .env</p>
</div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 6. Main
# -----------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="Foundry Chat",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    settings = read_settings()
    inject_app_styles()
    render_page_header()

    missing = missing_settings(settings)
    if missing:
        st.error(
            "Set these in `.env` (see `.env.example`): " + ", ".join(missing)
        )
        st.stop()

    with st.sidebar:
        st.markdown("### Sign-in (required)")
        st.markdown(
            """
This app uses **only** Microsoft Entra ID via the Azure SDK:

1. Run **`az login`** in a terminal (`readme.txt` has CLI install steps).
2. Your account needs a role on the Foundry project (e.g. **Azure AI User**).
3. **No API key** in `.env` — tokens come from your login.

`.env` only stores **which project** and **which deployment** to call.
            """
        )
        st.divider()
        st.markdown("### Session")
        if st.button("Clear conversation", type="primary", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.markdown("**Project endpoint** (preview)")
        _ep = settings["project_endpoint"]
        st.caption(_ep if len(_ep) <= 72 else _ep[:69] + "…")
        st.markdown("**Deployment**")
        st.code(settings["deployment_name"], language=None)

    try:
        client = openai_client_from_project(settings["project_endpoint"])
    except ClientAuthenticationError as e:
        st.error(
            "Sign-in failed. Run `az login` and check IAM on the project.\n\n"
            + api_error_text(e)
        )
        st.stop()
    except Exception as e:
        st.error("Could not create the client:\n\n" + api_error_text(e))
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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

        with st.spinner("Calling your deployment…"):
            try:
                response = client.chat.completions.create(
                    model=settings["deployment_name"],
                    messages=messages_for_api,
                )
                assistant_text = (response.choices[0].message.content or "").strip()
            except OpenAIError as e:
                st.session_state.messages.pop()
                st.error(api_error_text(e))
                st.stop()
            except Exception as e:
                st.session_state.messages.pop()
                st.error(api_error_text(e))
                st.stop()

        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        st.rerun()


if __name__ == "__main__":
    main()
