# AI Security & Threat Auditor

## What this project does

This is a Streamlit web app for AI-assisted, defensive review of text supplied by
the user. It sends a suspicious URL, IP address, or server-log snippet to Groq's
`openai/gpt-oss-120b` model and displays a threat assessment, a risk level,
and defensive remediation suggestions.

The app does not connect to or scan the supplied target. Its output is an
AI-generated assessment, not a verified security finding.

## Why it exists

The project is a cybersecurity-minor demonstration of using a language model to
summarize common security indicators and explain possible defensive next steps.
Treat its output as guidance to verify, not as a substitute for an investigation
by a security professional.

## Where the files are

- `app.py` contains the Streamlit interface.
- `agent.py` sends the analysis request to the Groq API.
- `requirements.txt` lists the Python dependencies.
- `setup.bat` creates a local virtual environment, installs dependencies, and
  starts the app on Windows.

Run commands from the project root: the folder containing `app.py`.

## Setup and run on Windows

1. Install Python and ensure the `py` launcher is available.
2. Create a Groq API key. The key must be supplied locally; never put it in
   source code or commit it.
   If you used a key that was previously embedded in this project, revoke it
   and create a replacement before running the app.
3. In PowerShell, from this folder, set the key for the current terminal:

   ```powershell
   $env:GROQ_API_KEY = "your-groq-api-key"
   ```

   Alternatively, create a `.env` file in this folder containing
   `GROQ_API_KEY=your-groq-api-key`. `.env` is excluded by `.gitignore`.
4. Run `setup.bat`. It creates `.venv`, installs `requirements.txt`, and starts
   Streamlit. The app is then available at the local address printed in the
   terminal (normally `http://localhost:8501`).

To start it manually after setup:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If `GROQ_API_KEY` is missing, the app displays an actionable configuration
error when an analysis is requested. API access and internet connectivity are
required for analysis.

If Groq returns `401 Unauthorized` / `Invalid API Key`, the key is invalid,
revoked, expired, or incomplete. Create a fresh key in your Groq account,
replace the value of `GROQ_API_KEY` in `.env`, and restart Streamlit. Never
paste API keys into chat or commit them to source control.
