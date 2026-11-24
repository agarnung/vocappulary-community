"""Ventana principal y navegación."""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
import webbrowser

from . import limits
from .config import APP_EDITION, APP_NAME, APP_VERSION, PRO_URL, find_data_file
from .i18n import I18n
from .screens import (
    GameScreen,
    HomeScreen,
    ResultsScreen,
    SettingsScreen,
    StatsScreen,
)
from .session import Session
from .storage import Storage
from .theme import Theme
from .vocab import Vocabulary


class App:
    def __init__(self, storage: Storage | None = None, vocab: Vocabulary | None = None):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {APP_EDITION} · v{APP_VERSION}")
        self.root.minsize(880, 700)
        self.root.geometry("1000x820")

        self.storage = storage or Storage()
        self.settings = self.storage.load_settings()
        self.i18n = I18n(self.settings.get("ui_lang", "es"))
        self.vocab = vocab or Vocabulary()
        self._sanitize_settings()
        self.theme = Theme(self.settings.get("theme", "light"), self.root)

        self.session: Session | None = None
        self.last_summary: dict | None = None
        self.current: tk.Frame | None = None
        self._icon = None

        self.root.configure(bg=self.theme.c("bg"))
        self._set_icon()
        self._center()
        self.show_home()

    # ----------------------------------------------------------------- helpers
    def _sanitize_settings(self) -> None:
        changed = False
        available_languages = limits.languages(self.vocab.languages)
        if self.settings.get("source_lang") not in available_languages:
            self.settings["source_lang"] = (
                available_languages[0] if available_languages else "en"
            )
            changed = True
        if self.settings.get("direction") not in ("to_es", "to_source"):
            self.settings["direction"] = "to_es"
            changed = True
        if self.settings.get("practice_mode") not in limits.modes():
            self.settings["practice_mode"] = "learn"
            changed = True
        if self.settings.get("session_length") not in limits.session_lengths():
            self.settings["session_length"] = limits.session_lengths()[0]
            changed = True
        lang = self.settings.get("source_lang", "en")
        category = self.settings.get("category", "all")
        if category != "all" and category not in self.vocab.categories(lang):
            self.settings["category"] = "all"
            changed = True
        if self.settings.get("ui_lang") not in ("es", "en", "fr"):
            self.settings["ui_lang"] = "es"
            changed = True
        if self.settings.get("theme") not in limits.themes():
            self.settings["theme"] = "light"
            changed = True
        try:
            daily_goal = int(self.settings.get("daily_goal", 20))
        except (TypeError, ValueError):
            daily_goal = 20
        if daily_goal not in (10, 20, 30, 50):
            daily_goal = 20
        if self.settings.get("daily_goal") != daily_goal:
            self.settings["daily_goal"] = daily_goal
            changed = True
        if changed:
            self.storage.save_settings(self.settings)

    def t(self, key: str, **kwargs) -> str:
        return self.i18n.t(key, **kwargs)

    def _center(self) -> None:
        self.root.update_idletasks()
        width, height = 1000, 820
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 3)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _set_icon(self) -> None:
        path = find_data_file("favicon.png")
        if not path:
            return
        try:
            self._icon = tk.PhotoImage(file=str(path))
            self.root.iconphoto(True, self._icon)
        except tk.TclError:
            self._icon = None

    # --------------------------------------------------------------- navigation
    def show(self, screen_class, **kwargs) -> None:
        if self.current is not None:
            self.current.destroy()
        self.current = screen_class(self, **kwargs)
        self.current.pack(fill="both", expand=True)

    def show_home(self) -> None:
        self.show(HomeScreen)

    def show_stats(self) -> None:
        self.show(StatsScreen)

    def show_settings(self) -> None:
        self.show(SettingsScreen)

    def start_session(self, entries=None) -> None:
        if not limits.unlocked() and entries is None:
            self.settings["practice_mode"] = "learn"
            self.settings["session_length"] = 10
        lang = self.settings.get("source_lang", "en")
        self.session = Session(
            self.vocab, self.storage, self.settings, lang, entries=entries
        )
        self.show(GameScreen)

    def finish_session(self) -> None:
        if self.session is None:
            self.show_home()
            return
        self.last_summary = self.session.summary()
        self.storage.record_session()
        self.session = None
        self.show(ResultsScreen)

    # ------------------------------------------------------------------ settings
    def set_theme(self, mode: str) -> None:
        if mode not in limits.themes():
            mode = "light"
        self.settings["theme"] = mode
        self.storage.save_settings(self.settings)
        self.theme = Theme(mode, self.root)
        self.root.configure(bg=self.theme.c("bg"))

    def toggle_theme(self) -> None:
        if not limits.unlocked():
            return
        new_mode = "dark" if self.theme.mode == "light" else "light"
        self.set_theme(new_mode)
        self._rebuild_current()

    def set_ui_lang(self, lang: str) -> None:
        self.settings["ui_lang"] = lang
        self.i18n = I18n(lang)
        self.storage.save_settings(self.settings)
        self.show_settings()

    def _rebuild_current(self) -> None:
        if isinstance(self.current, HomeScreen):
            self.show_home()
        elif isinstance(self.current, SettingsScreen):
            self.show_settings()
        elif isinstance(self.current, StatsScreen):
            self.show_stats()
        elif isinstance(self.current, ResultsScreen):
            self.show(ResultsScreen)
        else:
            self.show_home()

    def open_pro(self) -> None:
        webbrowser.open(PRO_URL)

    def open_data_folder(self) -> None:
        path = str(self.storage.base)
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()
