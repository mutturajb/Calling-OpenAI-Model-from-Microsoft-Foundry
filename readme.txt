Azure OpenAI / Microsoft Foundry — sample chat app
==================================================

This folder contains a small Streamlit app (`app.py`) that calls your Azure OpenAI
deployment using credentials from a `.env` file.


Prerequisites
-------------
- Python 3.10 or newer installed
- An Azure OpenAI or Microsoft Foundry deployment, plus endpoint URL, API key,
  and deployment name


Setup (first time only)
------------------------
Open a terminal in this project folder, then run:

1) Create a virtual environment (recommended):

   python3 -m venv .venv

2) Activate the virtual environment:

   On Linux or macOS:
   source .venv/bin/activate

   On Windows (Command Prompt):
   .venv\Scripts\activate.bat

   On Windows (PowerShell):
   .venv\Scripts\Activate.ps1

3) Install dependencies:

   pip install -r requirements.txt

4) Configure secrets:

   Copy `.env.example` to `.env` and edit `.env` with your real values:

   - AZURE_OPENAI_ENDPOINT — resource URL (for Foundry, use the host like
     https://your-resource.services.ai.azure.com if unsure)
   - AZURE_OPENAI_API_KEY — key from Azure Portal or Foundry
   - AZURE_OPENAI_DEPLOYMENT_NAME — name of your model deployment (example: DeepSeek-V3.2)


Run the app
-----------
With the virtual environment activated and dependencies installed:

   streamlit run app.py

Your browser should open to the local Streamlit URL (often http://localhost:8501).
Type messages in the chat box at the bottom to talk to your deployment.


Stop the app
------------
In the terminal where Streamlit is running, press Ctrl+C.


Notes
-----
- Do not commit your real `.env` file or API keys to source control.
- If you see API errors, check that the endpoint, key, and deployment name match
  what Azure / Foundry shows for your project.
