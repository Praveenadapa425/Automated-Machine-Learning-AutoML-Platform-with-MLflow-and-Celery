import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
API_DIR = ROOT_DIR / "api"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.main import app  # noqa: E402