import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'wfp.db'}"

HIBOB_API_KEY = os.environ.get("HIBOB_API_KEY", "")
HIBOB_BASE_URL = "https://api.hibob.com/v1"
