import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = f"sqlite:///{DATA_DIR / 'wfp.db'}"

HIBOB_BASE_URL = os.environ.get("HIBOB_API_URL", "https://api.hibob.com/v1")
HIBOB_SERVICE_USER = os.environ.get("HIBOB_SERVICE_USER", "")
HIBOB_API_TOKEN = os.environ.get("HIBOB_API_TOKEN", "")
