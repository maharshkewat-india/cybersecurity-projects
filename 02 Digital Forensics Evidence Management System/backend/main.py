"""
backend/main.py - Entry point for running the FastAPI backend with uvicorn.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        # Avoid creating a reload supervisor when launched by RUN_ME.bat.
        # On Windows, closing only the parent can leave a child server behind
        # to retain port 8000. Use ``uvicorn app:app --reload`` explicitly
        # during development when live reloading is needed.
        reload=False,
        log_level="info",
    )
