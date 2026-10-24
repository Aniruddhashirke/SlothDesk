import os
from pathlib import Path

DATA_DIR = Path(os.getenv("SLOTHDESK_DATA_DIR", Path.home() / ".slothdesk"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_DIR = DATA_DIR / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "20"))
