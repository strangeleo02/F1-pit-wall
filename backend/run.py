import sys
import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Ensure backend directory is in Python path so 'app' module can be imported cleanly
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Load .env file from root or backend directory if present
root_env = ROOT_DIR / ".env"
backend_env = BACKEND_DIR / ".env"

if root_env.exists():
    load_dotenv(root_env)
elif backend_env.exists():
    load_dotenv(backend_env)

def main():
    """Entry point to run the PitWall AI FastAPI server from the root directory."""
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("🏎️ Starting PitWall AI backend server...")
    print(f"📁 Backend path: {BACKEND_DIR}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BACKEND_DIR)]
    )

if __name__ == "__main__":
    main()
