"""Punto de entrada de Vocappulary."""

from __future__ import annotations

import sys


def main() -> None:
    if "--version" in sys.argv or "-V" in sys.argv:
        from vocapp.config import APP_VERSION

        print(f"Vocappulary Community {APP_VERSION}")
        return

    if sys.platform == "win32":
        try:
            from ctypes import windll

            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    import tkinter as tk

    from vocapp.app import App

    try:
        App().run()
    except tk.TclError as exc:
        print(f"No se pudo iniciar la interfaz gráfica: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
