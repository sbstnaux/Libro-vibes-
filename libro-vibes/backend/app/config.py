"""Configuración centralizada, leída desde variables de entorno (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(PROJECT_DIR / ".env")


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else PROJECT_DIR / path


def _bool_from_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "si"}


def _default_model_path() -> Path:
    # En Vercel solo existe backend/, así que el modelo se versiona en backend/model/.
    bundled = BACKEND_DIR / "model" / "recommender.joblib"
    return bundled if bundled.exists() else PROJECT_DIR / "data" / "processed" / "recommender.joblib"


class Config:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    DATA_PATH = _path_from_env("DATA_PATH", PROJECT_DIR / "data" / "raw" / "goodreads_data.xlsx")
    MODEL_PATH = _path_from_env("MODEL_PATH", _default_model_path())
    FRONTEND_DIR = _path_from_env("FRONTEND_DIR", PROJECT_DIR / "frontend")

    # Separados por coma, p. ej. "https://usuario.github.io,http://localhost:5500"
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

    SERVE_FRONTEND = _bool_from_env("SERVE_FRONTEND", True)
    DEFAULT_RESULTS = int(os.getenv("DEFAULT_RESULTS", "5"))
    MAX_RESULTS = int(os.getenv("MAX_RESULTS", "20"))
