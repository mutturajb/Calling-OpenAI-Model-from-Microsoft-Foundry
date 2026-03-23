Microsoft Foundry — sample chat app (Azure AI Projects + Entra ID only)
========================================================================

This app uses the **Azure AI Projects** Python SDK (`AIProjectClient`) and
**Microsoft Entra ID** for sign-in (`az login`). There are **no API keys** in `.env`.

What `.env` contains (configuration only — *where* to call, *which* deployment):
  - AZURE_AI_PROJECT_ENDPOINT — project URL from the Foundry portal
  - AZURE_AI_MODEL_DEPLOYMENT_NAME — name from Models → Deployments

What `az login` provides (identity):
  - `DefaultAzureCredential()` picks up your CLI session and obtains tokens.
  - `AIProjectClient` / `get_openai_client()` use those tokens (not a key from a file).

Flow in code:
  1) AIProjectClient(endpoint, credential)
  2) get_openai_client() → openai.OpenAI at …/openai/v1
  3) chat.completions.create(model=deployment_name, messages=…)


Prerequisites
-------------
- Python 3.10+
- A Microsoft Foundry project with a model deployed
- Azure CLI for `az login`


Install Azure CLI
-----------------
Official guide: https://learn.microsoft.com/cli/azure/install-azure-cli

Quick options:
- Linux (Ubuntu/Debian):  curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
- Windows:                winget install -e --id Microsoft.AzureCLI
- macOS:                  brew install azure-cli

Verify:
   az version
   az login


Next steps
----------
1) az login
2) Copy the **project endpoint** from Azure Portal / Foundry (often …/api/projects/…)
3) Copy the **deployment name** from Foundry → Build → Models → Deployments
4) Ensure your account has a role on the project (e.g. Azure AI User) — IAM in portal.
   https://learn.microsoft.com/azure/ai-foundry/concepts/rbac-foundry
5) Copy `.env.example` to `.env` and set the two variables (no keys).


Setup (Python)
--------------
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt


Run
---
   streamlit run app.py

Stop with Ctrl+C in the terminal.


Troubleshooting
---------------
- Auth errors: run `az login`, `az account set --subscription <id>` if needed, check IAM.
- Wrong deployment: `AZURE_AI_MODEL_DEPLOYMENT_NAME` must match Foundry exactly.

Remove old variables from your `.env` if you still have AZURE_OPENAI_* or
AZURE_INFERENCE_* — this sample no longer reads them.
