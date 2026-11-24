"""Rutas, metadatos y utilidades de sistema de archivos."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Vocappulary"
APP_VERSION = "2.0.0"
APP_EDITION = "Community"
GITHUB_URL = "https://github.com/agarnung/vocappulary"
SUPPORT_URL = "https://github.com/agarnung/vocappulary-community"
PRO_URL = os.environ.get(
    "VOCAPP_PRO_URL",
    "https://github.com/agarnung/vocappulary-community#vocappulary-pro",
)


def app_data_dir() -> Path:
    """Directorio de datos de usuario, multiplataforma."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = Path(base) / APP_NAME
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        path = Path(base) / "vocappulary"
    path.mkdir(parents=True, exist_ok=True)
    return path


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def project_dir() -> Path:
    return package_dir().parent


def data_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("VOCAPP_DATA_DIR")
    if env:
        roots.append(Path(env))
    roots.append(package_dir() / "data")
    roots.append(package_dir())
    roots.append(project_dir())
    roots.append(Path.cwd())
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        roots.append(exe_dir)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass))
    seen: set[Path] = set()
    unique: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        if resolved not in seen and resolved.exists():
            seen.add(resolved)
            unique.append(resolved)
    return unique


def find_data_file(relative: str) -> Path | None:
    """Busca un recurso de datos en desarrollo y en ejecutables empaquetados."""
    rel = Path(relative)
    if rel.is_absolute():
        return rel if rel.exists() else None
    for root in data_roots():
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return None
