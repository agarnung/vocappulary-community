"""Pantallas de la aplicación."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox
import webbrowser

from . import limits
from .config import APP_EDITION, APP_VERSION, GITHUB_URL, PRO_URL, SUPPORT_URL
from .i18n import LANGUAGES
from .widgets import (
    Card,
    EntryField,
    Pill,
    ProgressBar,
    RoundedButton,
    SelectableCard,
    SegmentedControl,
    StatTile,
    ToggleRow,
    parent_bg,
    rounded_points,
)


class Screen(tk.Frame):
    def __init__(self, app):
        self.app = app
        self.theme = app.theme
        self.t = app.t
        super().__init__(app.root, bg=self.theme.c("bg"))
        self.build()

    def build(self):
        raise NotImplementedError

    def pro_button(self, parent, width: int = 168, height: int = 38, font_size: int = 10):
        return RoundedButton(
            parent,
            self.app,
            text=self.t("go_pro"),
            icon="★",
            variant="primary",
            width=width,
            height=height,
            font_size=font_size,
            command=self.app.open_pro,
        )

    def topbar(self, parent, back=None, title: str | None = None, actions=None):
        bar = tk.Frame(parent, bg=self.theme.c("bg"))
        bar.pack(fill="x")
        if back is not None:
            RoundedButton(
                bar,
                self.app,
                text=self.t("back"),
                icon="←",
                variant="ghost",
                width=112,
                height=38,
                font_size=10,
                command=back,
            ).pack(side="left")
        if title:
            tk.Label(
                bar,
                text=title,
                bg=self.theme.c("bg"),
                fg=self.theme.c("text"),
                font=self.theme.font(13, "bold"),
            ).pack(side="left", padx=12)
        items = list(actions or [])
        if not limits.unlocked():
            items.insert(0, self.pro_button(bar, width=160, height=36, font_size=9))
        for widget in reversed(items):
            widget.pack(side="right", padx=(6, 0))
        return bar


class HomeScreen(Screen):
    def build(self):
        t = self.t
        th = self.theme
        settings = self.app.settings

        outer = tk.Frame(self, bg=th.c("bg"))
        outer.pack(fill="both", expand=True, padx=42, pady=18)

        bar = tk.Frame(outer, bg=th.c("bg"))
        bar.pack(fill="x")
        brand = tk.Frame(bar, bg=th.c("bg"))
        brand.pack(side="left")
        logo = tk.Canvas(
            brand, width=38, height=38, bg=th.c("bg"), highlightthickness=0
        )
        logo.pack(side="left", padx=(0, 10))
        logo.create_oval(2, 2, 36, 36, fill=th.c("primary"), outline="")
        logo.create_text(
            19,
            19,
            text="V",
            fill=th.c("on_primary"),
            font=th.font(18, "bold"),
        )
        titles = tk.Frame(brand, bg=th.c("bg"))
        titles.pack(side="left")
        tk.Label(
            titles,
            text=f"{t('app_name')} {APP_EDITION}",
            bg=th.c("bg"),
            fg=th.c("text"),
            font=th.font(18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            titles,
            text=t("tagline"),
            bg=th.c("bg"),
            fg=th.c("muted"),
            font=th.font(8),
        ).pack(anchor="w")
        actions = []
        if limits.unlocked():
            actions.append(
                RoundedButton(
                    bar,
                    self.app,
                    text=t("dark") if th.mode == "light" else t("light"),
                    icon="☀" if th.mode == "light" else "☾",
                    variant="ghost",
                    width=112,
                    height=38,
                    font_size=10,
                    command=self.app.toggle_theme,
                )
            )
        actions.extend(
            [
                RoundedButton(
                    bar,
                    self.app,
                    text=t("stats"),
                    icon="▥",
                    variant="ghost",
                    width=118,
                    height=38,
                    font_size=10,
                    command=self.app.show_stats,
                ),
                RoundedButton(
                    bar,
                    self.app,
                    text=t("settings"),
                    icon="⚙",
                    variant="ghost",
                    width=122,
                    height=38,
                    font_size=10,
                    command=self.app.show_settings,
                ),
            ]
        )
        if not limits.unlocked():
            actions.insert(0, self.pro_button(bar))
        for widget in actions:
            widget.pack(side="right", padx=(6, 0))

        hero = tk.Frame(outer, bg=th.c("bg"))
        hero.pack(fill="x", pady=(14, 10))
        tk.Label(
            hero,
            text=t("hero_title"),
            bg=th.c("bg"),
            fg=th.c("text"),
            font=th.font(22, "bold"),
            anchor="w",
            justify="left",
            wraplength=820,
        ).pack(anchor="w")
        tk.Label(
            hero,
            text=t("hero_subtitle"),
            bg=th.c("bg"),
            fg=th.c("muted"),
            font=th.font(11),
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(6, 0))
        if not limits.unlocked():
            tk.Label(
                hero,
                text=t("more_note"),
                bg=th.c("bg"),
                fg=th.c("subtle"),
                font=th.font(9, "bold"),
                anchor="w",
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

        lang_label = tk.Frame(outer, bg=th.c("bg"))
        lang_label.pack(fill="x", pady=(0, 6))
        tk.Label(
            lang_label,
            text=t("choose_language").upper(),
            bg=th.c("bg"),
            fg=th.c("subtle"),
            font=th.font(9, "bold"),
        ).pack(anchor="w")

        lang_row = tk.Frame(outer, bg=th.c("bg"))
        lang_row.pack(fill="x")
        self.lang_cards: dict[str, SelectableCard] = {}
        codes = limits.languages(list(self.app.vocab.languages.keys()))
        for index, code in enumerate(codes):
            card = self._language_card(lang_row, code, index == len(codes) - 1)
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 0) if index == len(codes) - 1 else (0, 12),
            )
            self.lang_cards[code] = card

        options = Card(outer, self.app, padding=14)
        options.pack(fill="x", pady=(16, 0))
        options.grid_columnconfigure(1, weight=1)

        if limits.unlocked():
            tk.Label(
                options,
                text=t("mode"),
                bg=options["bg"],
                fg=th.c("muted"),
                font=th.font(10, "bold"),
                anchor="w",
            ).grid(row=0, column=0, sticky="w", pady=(0, 8), padx=(0, 14))
            direction_var = tk.StringVar(value=settings.get("direction", "to_es"))
            SegmentedControl(
                options,
                self.app,
                options=[("to_es", t("to_spanish")), ("to_source", t("to_source"))],
                variable=direction_var,
                command=lambda value: self._set_setting("direction", value),
                height=34,
                font_size=9,
            ).grid(row=0, column=1, sticky="ew", pady=(0, 8))

            tk.Label(
                options,
                text=t("practice"),
                bg=options["bg"],
                fg=th.c("muted"),
                font=th.font(10, "bold"),
                anchor="w",
            ).grid(row=1, column=0, sticky="w", pady=(0, 8), padx=(0, 14))
            mode_var = tk.StringVar(value=settings.get("practice_mode", "learn"))
            SegmentedControl(
                options,
                self.app,
                options=[
                    ("learn", t("learn")),
                    ("review", t("review")),
                    ("quick", t("quick")),
                ],
                variable=mode_var,
                command=lambda value: self._set_setting("practice_mode", value),
                height=34,
                font_size=9,
            ).grid(row=1, column=1, sticky="ew", pady=(0, 8))

        if limits.unlocked():
            tk.Label(
                options,
                text=t("category"),
                bg=options["bg"],
                fg=th.c("muted"),
                font=th.font(10, "bold"),
                anchor="w",
            ).grid(row=2, column=0, sticky="w", pady=(0, 8), padx=(0, 14))
            category_options = self.app.vocab.category_options(
                settings.get("source_lang", "fr"),
                settings.get("ui_lang", "es"),
                t("all_categories"),
                t("category_general"),
            )
            self.category_map = {label: value for value, label in category_options}
            current_category = settings.get("category", "all")
            current_label = next(
                (label for value, label in category_options if value == current_category),
                category_options[0][1],
            )
            self.category_var = tk.StringVar(value=current_label)
            category_menu = tk.OptionMenu(
                options,
                self.category_var,
                *[label for _, label in category_options],
                command=self._category_changed,
            )
            category_menu.config(
                bg=th.c("surface_alt"),
                fg=th.c("text"),
                activebackground=th.c("surface_hover"),
                activeforeground=th.c("text"),
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=th.c("border"),
                font=th.font(9),
                anchor="w",
                padx=10,
            )
            category_menu["menu"].config(
                bg=th.c("surface"),
                fg=th.c("text"),
                activebackground=th.c("primary"),
                activeforeground=th.c("on_primary"),
                font=th.font(9),
            )
            category_menu.grid(row=2, column=1, sticky="ew", pady=(0, 8))

        if not limits.unlocked():
            options.pack_forget()

        if limits.unlocked():
            tk.Label(
                options,
                text=t("session_length"),
                bg=options["bg"],
                fg=th.c("muted"),
                font=th.font(10, "bold"),
                anchor="w",
            ).grid(row=3, column=0, sticky="w", padx=(0, 14))
            length_var = tk.StringVar(value=str(settings.get("session_length", 10)))
            SegmentedControl(
                options,
                self.app,
                options=[("10", "10"), ("20", "20"), ("50", "50"), ("all", t("all_words"))],
                variable=length_var,
                command=lambda value: self._set_setting(
                    "session_length", value if value == "all" else int(value)
                ),
                height=34,
                font_size=9,
            ).grid(row=3, column=1, sticky="ew")

        RoundedButton(
            outer,
            self.app,
            text=t("start"),
            icon="▶",
            variant="primary",
            width=220,
            height=48,
            font_size=13,
            command=self.app.start_session,
        ).pack(pady=(12, 0))

        stats_row = tk.Frame(outer, bg=th.c("bg"))
        stats_row.pack(fill="x", pady=(12, 0))
        lang = settings.get("source_lang", "fr")
        direction = settings.get("direction", "to_es")
        entries = self.app.vocab.entries(lang)
        category = settings.get("category", "all")
        if category != "all":
            entries = [entry for entry in entries if entry.category == category]
        total_answers = int(self.app.storage.stats.get("total_answers", 0))
        accuracy = self.app.storage.accuracy()
        streak = int(self.app.storage.stats.get("current_streak", 0))
        due = self.app.storage.due_count(entries, lang, direction)
        tiles = [
            (str(total_answers), t("total_answers"), th.c("text")),
            (f"{accuracy:.0f}%", t("accuracy"), th.c("success")),
            (str(streak), t("current_streak"), th.c("warning")),
            (str(due), t("due_today"), th.c("primary")),
        ]
        for index, (value, label, accent) in enumerate(tiles):
            tile = StatTile(stats_row, self.app, value, label, accent=accent)
            tile.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 0) if index == len(tiles) - 1 else (0, 10),
            )

        footer = tk.Frame(outer, bg=th.c("bg"))
        footer.pack(fill="x", pady=(8, 0))
        tk.Label(
            footer,
            text=f"{t('made_with')} · v{APP_VERSION}",
            bg=th.c("bg"),
            fg=th.c("subtle"),
            font=th.font(9),
        ).pack(side="left")
        goal = max(1, int(settings.get("daily_goal", 20) or 20))
        done = self.app.storage.daily_answers()
        if done >= goal:
            goal_text = f"{t('goal_reached')}  {done}/{goal}"
            goal_color = th.c("success")
        else:
            goal_text = f"{t('today')}  {done}/{goal}"
            goal_color = th.c("muted")
        Pill(footer, self.app, text=goal_text, fg=goal_color).pack(
            side="left", padx=(12, 0)
        )
        RoundedButton(
            footer,
            self.app,
            text=t("support"),
            icon="♥",
            variant="ghost",
            width=150,
            height=30,
            font_size=9,
            command=lambda: webbrowser.open(SUPPORT_URL),
        ).pack(side="right")

    def _language_card(self, parent, code: str, last: bool) -> SelectableCard:
        th = self.theme
        t = self.t
        settings = self.app.settings
        info = self.app.vocab.language(code)
        selected = code == settings.get("source_lang")
        total = self.app.vocab.total(code)
        card = SelectableCard(
            parent,
            self.app,
            selected=selected,
            command=lambda: self._select_language(code),
            padding=14,
        )
        top = tk.Frame(card, bg=card["bg"])
        top.pack(fill="x")
        badge = tk.Canvas(
            top, width=42, height=42, bg=card["bg"], highlightthickness=0
        )
        badge.pack(side="left", padx=(0, 10))
        badge.create_oval(2, 2, 40, 40, fill=info.color, outline="")
        badge.create_text(
            21,
            21,
            text=info.label,
            fill="#FFFFFF",
            font=th.font(12, "bold"),
        )
        texts = tk.Frame(top, bg=card["bg"])
        texts.pack(side="left", fill="x", expand=True)
        tk.Label(
            texts,
            text=info.name(settings.get("ui_lang", "es")),
            bg=card["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            texts,
            text=f"{total} {t('words_count')}",
            bg=card["bg"],
            fg=th.c("muted"),
            font=th.font(9),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            top,
            text="✓" if selected else "",
            bg=card["bg"],
            fg=th.c("primary"),
            font=th.font(16, "bold"),
        ).pack(side="right")

        bottom = tk.Frame(card, bg=card["bg"])
        bottom.pack(fill="x", pady=(8, 0))
        direction = settings.get("direction", "to_es")
        if direction == "to_es":
            arrow = f"{info.label} → ES"
        else:
            arrow = f"ES → {info.label}"
        tk.Label(
            bottom,
            text=arrow,
            bg=card["bg"],
            fg=th.c("muted"),
            font=th.font(9, "bold"),
        ).pack(side="left")
        learned = self.app.storage.learned_count(
            self.app.vocab.entries(code), code, direction
        )
        tk.Label(
            bottom,
            text=f"{learned}/{total}",
            bg=card["bg"],
            fg=th.c("subtle"),
            font=th.font(9),
        ).pack(side="right")
        return card

    def _select_language(self, code: str) -> None:
        if self.app.settings.get("source_lang") == code:
            return
        self.app.settings["source_lang"] = code
        self.app.settings["category"] = "all"
        self.app.storage.save_settings(self.app.settings)
        self.app.show_home()

    def _set_setting(self, key: str, value) -> None:
        self.app.settings[key] = value
        self.app.storage.save_settings(self.app.settings)
        if key == "direction":
            self.app.show_home()

    def _category_changed(self, label: str) -> None:
        value = self.category_map.get(label, "all")
        self._set_setting("category", value)


class GameScreen(Screen):
    def build(self):
        t = self.t
        th = self.theme
        self.session = self.app.session
        self.answered = False
        self.after_id = None
        self.hint_level = 0

        outer = tk.Frame(self, bg=th.c("bg"))
        outer.pack(fill="both", expand=True, padx=42, pady=22)

        bar = tk.Frame(outer, bg=th.c("bg"))
        bar.pack(fill="x")
        RoundedButton(
            bar,
            self.app,
            text=t("back"),
            icon="←",
            variant="ghost",
            width=112,
            height=36,
            font_size=10,
            command=self.leave,
        ).pack(side="left")
        self.progress_label = tk.Label(
            bar,
            text="",
            bg=th.c("bg"),
            fg=th.c("muted"),
            font=th.font(10, "bold"),
        )
        self.progress_label.pack(side="left", padx=12)
        self.streak_pill = Pill(bar, self.app, text="", fg=th.c("warning"))
        self.streak_pill.pack(side="right", padx=(8, 0))
        self.score_pill = Pill(bar, self.app, text="", fg=th.c("primary"))
        self.score_pill.pack(side="right")

        self.progress = ProgressBar(outer, self.app, height=8)
        self.progress.pack(fill="x", pady=(12, 18))

        card = Card(outer, self.app, padding=26)
        card.pack(fill="both", expand=True)
        center = tk.Frame(card, bg=card["bg"])
        center.pack(fill="both", expand=True)
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(0, weight=1)
        content = tk.Frame(center, bg=card["bg"])
        content.grid(row=0, column=0)

        self.lang_label = tk.Label(
            content,
            text="",
            bg=card["bg"],
            fg=th.c("subtle"),
            font=th.font(9, "bold"),
        )
        self.lang_label.pack()

        self.prompt_label = tk.Label(
            content,
            text="",
            bg=card["bg"],
            fg=th.c("text"),
            font=th.font(34, "bold"),
            wraplength=700,
            justify="center",
        )
        self.prompt_label.pack(pady=(8, 0))

        self.hint_label = tk.Label(
            content,
            text="",
            bg=card["bg"],
            fg=th.c("muted"),
            font=th.font(11),
            wraplength=700,
            justify="center",
        )
        self.hint_label.pack(pady=(8, 0))

        self.entry = EntryField(
            content, self.app, placeholder=t("type_answer"), font_size=18
        )
        self.entry.pack(fill="x", pady=(22, 0))
        self.entry.bind_return(self.submit)

        self.feedback_frame = tk.Frame(content, bg=card["bg"])
        self.feedback_label = tk.Label(
            self.feedback_frame,
            text="",
            bg=card["bg"],
            fg=th.c("text"),
            font=th.font(11, "bold"),
            wraplength=660,
            justify="center",
            padx=14,
            pady=10,
        )
        self.feedback_label.pack()

        buttons = tk.Frame(content, bg=card["bg"])
        buttons.pack(fill="x", pady=(18, 0))
        self.hint_btn = RoundedButton(
            buttons,
            self.app,
            text=t("hint"),
            icon="?",
            variant="secondary",
            width=110,
            height=42,
            font_size=10,
            command=self.hint,
        )
        self.hint_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.skip_btn = RoundedButton(
            buttons,
            self.app,
            text=t("skip"),
            icon="→",
            variant="secondary",
            width=110,
            height=42,
            font_size=10,
            command=self.skip,
        )
        self.skip_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.check_btn = RoundedButton(
            buttons,
            self.app,
            text=t("check"),
            icon="↵",
            variant="primary",
            width=160,
            height=42,
            font_size=10,
            command=self.submit,
        )
        self.check_btn.pack(side="left", fill="x", expand=True)

        footer = tk.Frame(outer, bg=th.c("bg"))
        footer.pack(fill="x", pady=(10, 0))
        self.footer_label = tk.Label(
            footer,
            text="",
            bg=th.c("bg"),
            fg=th.c("subtle"),
            font=th.font(9),
        )
        self.footer_label.pack()

        self.bind("<Escape>", lambda event: self.leave())
        self.bind("<Control-h>", lambda event: self.hint())

        if not self.session or not self.session.questions:
            self._build_empty(card, content)
            return
        self._show_question()

    def _build_empty(self, card, content):
        t = self.t
        th = self.theme
        for child in content.winfo_children():
            child.destroy()
        tk.Label(
            content,
            text=t("session_empty"),
            bg=card["bg"],
            fg=th.c("text"),
            font=th.font(22, "bold"),
        ).pack(pady=(0, 8))
        tk.Label(
            content,
            text=t("session_empty_desc"),
            bg=card["bg"],
            fg=th.c("muted"),
            font=th.font(11),
            wraplength=520,
            justify="center",
        ).pack(pady=(0, 18))
        RoundedButton(
            content,
            self.app,
            text=t("go_home"),
            icon="←",
            variant="primary",
            width=200,
            height=44,
            command=self.app.show_home,
        ).pack()
        self.progress_label.config(text="")
        self.footer_label.config(text="")
        self.progress.set_ratio(0)
        self.score_pill.set_text(f"0 {t('points')}")
        self.streak_pill.set_text(f"{t('streak')} 0")

    def _show_question(self):
        t = self.t
        th = self.theme
        question = self.session.current()
        if question is None:
            self.app.finish_session()
            return
        self.answered = False
        self.hint_level = 0
        self.feedback_frame.pack_forget()
        self.entry.configure(bg=th.c("border"))
        self.hint_label.config(text="")
        self.footer_label.config(
            text=f"{t('press_enter_check')}  ·  {t('esc_back')}  ·  {t('ctrl_hint')}"
        )
        self.entry.set_readonly(False)
        self.entry.clear()
        self.entry.focus()
        self.check_btn.set_command(self.submit)
        self.check_btn.set_text(t("check"))
        self.check_btn.set_variant("primary")
        self.check_btn.set_enabled(True)
        self.hint_btn.set_enabled(True)
        self.skip_btn.set_enabled(True)

        total = len(self.session.questions)
        self.progress_label.config(
            text=f"{t('question')} {self.session.index + 1} {t('of')} {total}"
        )
        self.progress.set_ratio(self.session.index / max(total, 1))
        self.score_pill.set_text(f"{self.session.score} {t('points')}")
        self.streak_pill.set_text(f"{t('streak')} {self.session.streak}")

        lang_info = self.app.vocab.language(self.session.lang)
        lang_name = lang_info.name(self.app.settings.get("ui_lang", "es"))
        if self.session.direction == "to_es":
            label = f"{lang_name.upper()}  →  {t('spanish').upper()}"
        else:
            label = f"{t('spanish').upper()}  →  {lang_name.upper()}"
        self.lang_label.config(text=label)
        self.prompt_label.config(text=question.prompt)

    def submit(self):
        if self.answered:
            self.continue_()
            return
        answer = self.entry.get().strip()
        if not answer:
            self._show_feedback("warning", self.t("empty_answer"))
            return
        result = self.session.submit(answer)
        if result is None:
            return
        self.answered = True
        self.entry.set_readonly(True)
        self.hint_btn.set_enabled(False)
        self.skip_btn.set_enabled(False)
        self.check_btn.set_enabled(False)
        self.footer_label.config(text=self.t("press_enter_continue"))
        self._show_result(result)
        self.progress.set_ratio(
            (self.session.index + 1) / max(len(self.session.questions), 1)
        )
        self.score_pill.set_text(f"{self.session.score} {self.t('points')}")
        self.streak_pill.set_text(f"{self.t('streak')} {self.session.streak}")
        if self.app.settings.get("sound", True) and result.status == "wrong":
            try:
                self.app.root.bell()
            except tk.TclError:
                pass
        delay = 900 if result.status == "correct" else 1600
        if result.status == "wrong":
            delay = 2000
        self.check_btn.set_command(self.continue_)
        self.check_btn.set_text(self.t("continue"))
        self.check_btn.set_variant("primary")
        self.check_btn.set_enabled(True)
        if self.app.settings.get("auto_advance", True):
            self.after_id = self.after(delay, self.continue_)

    def skip(self):
        if self.answered:
            return
        result = self.session.skip()
        if result is None:
            return
        self.answered = True
        self.entry.set_readonly(True)
        self.hint_btn.set_enabled(False)
        self.skip_btn.set_enabled(False)
        self.check_btn.set_enabled(False)
        self.footer_label.config(text=self.t("press_enter_continue"))
        self._show_result(result)
        self.progress.set_ratio(
            (self.session.index + 1) / max(len(self.session.questions), 1)
        )
        self.score_pill.set_text(f"{self.session.score} {self.t('points')}")
        self.streak_pill.set_text(f"{self.t('streak')} {self.session.streak}")
        delay = 1600
        self.check_btn.set_command(self.continue_)
        self.check_btn.set_text(self.t("continue"))
        self.check_btn.set_variant("primary")
        self.check_btn.set_enabled(True)
        if self.app.settings.get("auto_advance", True):
            self.after_id = self.after(delay, self.continue_)

    def hint(self):
        if self.answered:
            return
        question = self.session.current()
        if question is None or not question.expected:
            return
        expected = question.expected[0]
        self.hint_level = min(self.hint_level + 1, max(len(expected), 1))
        self.session.mark_hint()
        masked = "".join(
            char if index < self.hint_level or char.isspace() else "_"
            for index, char in enumerate(expected)
        )
        self.hint_label.config(
            text=f"{self.t('hint_label')}: {masked}  ({len(expected)})"
        )

    def _show_result(self, result):
        if result.status == "correct":
            self._show_feedback("success", f"✓ {self.t('correct')} · {result.expected}")
        elif result.status == "almost":
            reason = result.reason
            reason_text = ""
            if reason in ("accent", "typo", "plural", "article"):
                reason_text = f" ({self.t('feedback_' + reason)})"
            self._show_feedback(
                "warning",
                f"≈ {self.t('almost')}{reason_text} · {self.t('answer_was')}: {result.expected}",
            )
        else:
            if result.reason == "skipped":
                self._show_feedback(
                    "danger",
                    f"✕ {self.t('feedback_skipped')} · {self.t('answer_was')}: {result.expected}",
                )
            else:
                self._show_feedback(
                    "danger",
                    f"✕ {self.t('wrong')} · {self.t('answer_was')}: {result.expected}",
                )

    def _show_feedback(self, kind: str, text: str):
        th = self.theme
        if kind == "success":
            color = th.c("success")
            soft = th.c("success_soft")
        elif kind == "warning":
            color = th.c("warning")
            soft = th.c("warning_soft")
        else:
            color = th.c("danger")
            soft = th.c("danger_soft")
        self.feedback_frame.config(bg=soft)
        self.feedback_label.config(text=text, fg=color, bg=soft)
        self.entry.configure(bg=color)
        self.feedback_frame.pack(fill="x", pady=(18, 0))

    def continue_(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
        if self.session.index + 1 >= len(self.session.questions):
            self.session.advance()
            self.app.finish_session()
            return
        self.session.advance()
        self._show_question()

    def leave(self):
        if self.after_id is not None:
            try:
                self.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None
        if self.session and self.session.records:
            if not messagebox.askyesno(
                self.t("app_name"), self.t("leave_confirm")
            ):
                return
        self.app.show_home()


class ActivityChart(tk.Canvas):
    def __init__(self, parent, app, data, height: int = 150, **kwargs):
        self.app = app
        self.theme = app.theme
        self.data = data
        super().__init__(
            parent,
            height=height,
            bg=parent_bg(parent, self.theme),
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.bind("<Configure>", lambda event: self._draw())
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        if not self.data:
            return
        maximum = max((answers for _, answers, _ in self.data), default=0)
        if maximum <= 0:
            self.create_text(
                width / 2,
                height / 2,
                text=self.app.t("no_data"),
                fill=self.theme.c("subtle"),
                font=self.theme.font(10),
            )
            return
        count = len(self.data)
        gap = 10
        bar_width = (width - gap * (count - 1)) / count
        bottom = height - 24
        usable = height - 40
        names = self.app.t("weekdays_short").split()
        if len(names) < 7:
            names = ["L", "M", "X", "J", "V", "S", "D"]
        for index, (day, answers, good) in enumerate(self.data):
            x = index * (bar_width + gap)
            total_height = usable * answers / maximum
            good_height = usable * good / maximum
            if total_height > 0:
                self.create_polygon(
                    rounded_points(
                        x, bottom - total_height, x + bar_width, bottom, 6
                    ),
                    smooth=True,
                    fill=self.theme.c("primary_soft"),
                    outline="",
                )
            if good_height > 0:
                self.create_polygon(
                    rounded_points(
                        x, bottom - good_height, x + bar_width, bottom, 6
                    ),
                    smooth=True,
                    fill=self.theme.c("primary"),
                    outline="",
                )
            try:
                weekday = date.fromisoformat(day).weekday()
                label = names[weekday]
            except ValueError:
                label = day[-2:]
            self.create_text(
                x + bar_width / 2,
                bottom + 12,
                text=label,
                fill=self.theme.c("muted"),
                font=self.theme.font(9, "bold"),
            )
            if answers:
                self.create_text(
                    x + bar_width / 2,
                    bottom - total_height - 8,
                    text=str(answers),
                    fill=self.theme.c("muted"),
                    font=self.theme.font(8),
                )


class ResultsScreen(Screen):
    def build(self):
        t = self.t
        th = self.theme
        summary = self.app.last_summary
        if not summary:
            self.app.show_home()
            return

        outer = tk.Frame(self, bg=th.c("bg"))
        outer.pack(fill="both", expand=True, padx=42, pady=24)

        self.topbar(outer, back=self.app.show_home, title=t("result"))

        tk.Label(
            outer,
            text=t("session_complete"),
            bg=th.c("bg"),
            fg=th.c("text"),
            font=th.font(26, "bold"),
        ).pack(anchor="w", pady=(20, 2))
        tk.Label(
            outer,
            text=t("perfect") if summary["wrong"] == 0 else t("keep_going"),
            bg=th.c("bg"),
            fg=th.c("muted"),
            font=th.font(11),
        ).pack(anchor="w", pady=(0, 16))

        tiles_row = tk.Frame(outer, bg=th.c("bg"))
        tiles_row.pack(fill="x")
        minutes = int(summary["elapsed"] // 60)
        seconds = int(summary["elapsed"] % 60)
        tiles = [
            (str(summary["score"]), t("score"), th.c("primary")),
            (f"{summary['accuracy']:.0f}%", t("accuracy"), th.c("success")),
            (str(summary["best_streak"]), t("best_streak"), th.c("warning")),
            (f"{minutes}:{seconds:02d}", t("time"), th.c("text")),
        ]
        for index, (value, label, accent) in enumerate(tiles):
            tile = StatTile(tiles_row, self.app, value, label, accent=accent)
            tile.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 0) if index == len(tiles) - 1 else (0, 10),
            )

        breakdown = tk.Frame(outer, bg=th.c("bg"))
        breakdown.pack(fill="x", pady=(10, 0))
        for label, value, color in (
            (t("correct_answers"), summary["correct"], th.c("success")),
            (t("almost_answers"), summary["almost"], th.c("warning")),
            (t("wrong_answers"), summary["wrong"], th.c("danger")),
        ):
            Pill(
                breakdown,
                self.app,
                text=f"{label}: {value}",
                fg=color,
                bg=th.c("surface_alt"),
            ).pack(side="left", padx=(0, 8))

        missed = summary.get("missed", [])
        missed_card = Card(outer, self.app, padding=18)
        missed_card.pack(fill="both", expand=True, pady=(16, 0))
        tk.Label(
            missed_card,
            text=f"{t('missed_words')} ({len(missed)})",
            bg=missed_card["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        if missed:
            for record in missed[:8]:
                row = tk.Frame(missed_card, bg=missed_card["bg"])
                row.pack(fill="x", pady=3)
                tk.Label(
                    row,
                    text=record.prompt,
                    bg=missed_card["bg"],
                    fg=th.c("text"),
                    font=th.font(11, "bold"),
                    anchor="w",
                ).pack(side="left")
                tk.Label(
                    row,
                    text=f"{record.answer or '—'}  →  {record.expected}",
                    bg=missed_card["bg"],
                    fg=th.c("muted"),
                    font=th.font(10),
                    anchor="e",
                ).pack(side="right")
            if len(missed) > 8:
                tk.Label(
                    missed_card,
                    text=f"+{len(missed) - 8}",
                    bg=missed_card["bg"],
                    fg=th.c("subtle"),
                    font=th.font(9),
                ).pack(anchor="w", pady=(4, 0))
            tk.Label(
                missed_card,
                text=t("review_missed_desc"),
                bg=missed_card["bg"],
                fg=th.c("subtle"),
                font=th.font(9),
            ).pack(side="bottom", anchor="w", pady=(8, 0))
        else:
            tk.Label(
                missed_card,
                text=t("no_missed"),
                bg=missed_card["bg"],
                fg=th.c("success"),
                font=th.font(11, "bold"),
            ).pack(anchor="w")

        buttons = tk.Frame(outer, bg=th.c("bg"))
        buttons.pack(side="bottom", fill="x", pady=(16, 0))
        if missed:
            RoundedButton(
                buttons,
                self.app,
                text=t("repeat_missed"),
                icon="↻",
                variant="secondary",
                width=180,
                height=44,
                font_size=10,
                command=self._repeat_missed,
            ).pack(side="left", padx=(0, 8))
        RoundedButton(
            buttons,
            self.app,
            text=t("new_session"),
            icon="▶",
            variant="primary",
            width=180,
            height=44,
            font_size=10,
            command=self.app.start_session,
        ).pack(side="left", padx=(0, 8))
        RoundedButton(
            buttons,
            self.app,
            text=t("home"),
            icon="⌂",
            variant="ghost",
            width=130,
            height=44,
            font_size=10,
            command=self.app.show_home,
        ).pack(side="left")
        self.bind("<Escape>", lambda event: self.app.show_home())

    def _repeat_missed(self):
        summary = self.app.last_summary
        if not summary:
            return
        entries = [record.entry for record in summary.get("missed", [])]
        self.app.start_session(entries=entries)


class StatsScreen(Screen):
    def build(self):
        t = self.t
        th = self.theme
        storage = self.app.storage
        settings = self.app.settings
        direction = settings.get("direction", "to_es")

        outer = tk.Frame(self, bg=th.c("bg"))
        outer.pack(fill="both", expand=True, padx=42, pady=24)

        self.topbar(outer, back=self.app.show_home, title=t("stats"))
        tk.Label(
            outer,
            text=t("stats"),
            bg=th.c("bg"),
            fg=th.c("text"),
            font=th.font(24, "bold"),
        ).pack(anchor="w", pady=(18, 0))
        tk.Label(
            outer,
            text=t("stats_subtitle"),
            bg=th.c("bg"),
            fg=th.c("muted"),
            font=th.font(10),
        ).pack(anchor="w", pady=(2, 14))

        tiles_row = tk.Frame(outer, bg=th.c("bg"))
        tiles_row.pack(fill="x")
        stats = storage.stats
        tiles = [
            (str(stats.get("total_answers", 0)), t("total_answers"), th.c("text")),
            (f"{storage.accuracy():.0f}%", t("accuracy"), th.c("success")),
            (str(stats.get("current_streak", 0)), t("current_streak"), th.c("warning")),
            (str(stats.get("best_streak", 0)), t("best_streak"), th.c("primary")),
        ]
        for index, (value, label, accent) in enumerate(tiles):
            tile = StatTile(tiles_row, self.app, value, label, accent=accent)
            tile.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0, 0) if index == len(tiles) - 1 else (0, 10),
            )

        columns = tk.Frame(outer, bg=th.c("bg"))
        columns.pack(fill="both", expand=True, pady=(16, 0))
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=1)

        languages_card = Card(columns, self.app, padding=18)
        languages_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(
            languages_card,
            text=t("language"),
            bg=languages_card["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        for code, info in self.app.vocab.languages.items():
            entries = self.app.vocab.entries(code)
            total = len(entries)
            learned = storage.learned_count(entries, code, direction)
            due = storage.due_count(entries, code, direction)
            accuracy = storage.accuracy(code)
            row = tk.Frame(languages_card, bg=languages_card["bg"])
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text=info.name(settings.get("ui_lang", "es")),
                bg=languages_card["bg"],
                fg=th.c("text"),
                font=th.font(10, "bold"),
            ).pack(side="left")
            tk.Label(
                row,
                text=f"{learned}/{total} · {due} {t('due_words').lower()} · {accuracy:.0f}%",
                bg=languages_card["bg"],
                fg=th.c("muted"),
                font=th.font(9),
            ).pack(side="right")
            bar = ProgressBar(languages_card, self.app, height=6)
            bar.pack(fill="x", pady=(2, 6))
            bar.set_ratio(learned / total if total else 0)

        if limits.unlocked():
            activity_card = Card(columns, self.app, padding=18)
            activity_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
            tk.Label(
                activity_card,
                text=t("last_7_days"),
                bg=activity_card["bg"],
                fg=th.c("text"),
                font=th.font(13, "bold"),
            ).pack(anchor="w", pady=(0, 8))
            chart = ActivityChart(
                activity_card, self.app, storage.activity(7), height=150
            )
            chart.pack(fill="both", expand=True)

            hardest_card = Card(outer, self.app, padding=18)
            hardest_card.pack(fill="x", pady=(16, 0))
            tk.Label(
                hardest_card,
                text=t("hardest_words"),
                bg=hardest_card["bg"],
                fg=th.c("text"),
                font=th.font(13, "bold"),
            ).pack(anchor="w", pady=(0, 6))
            hardest = storage.hardest_words(5)
            if not hardest:
                tk.Label(
                    hardest_card,
                    text=t("no_data"),
                    bg=hardest_card["bg"],
                    fg=th.c("subtle"),
                    font=th.font(10),
                ).pack(anchor="w")
            else:
                for lang, word, data in hardest:
                    entry = self.app.vocab.find_entry(lang, word)
                    if not entry:
                        continue
                    row = tk.Frame(hardest_card, bg=hardest_card["bg"])
                    row.pack(fill="x", pady=2)
                    tk.Label(
                        row,
                        text=entry.source,
                        bg=hardest_card["bg"],
                        fg=th.c("text"),
                        font=th.font(10, "bold"),
                    ).pack(side="left")
                    tk.Label(
                        row,
                        text=f"{entry.display_translations} · {data.get('wrong', 0)} {t('wrong_answers').lower()}",
                        bg=hardest_card["bg"],
                        fg=th.c("muted"),
                        font=th.font(9),
                    ).pack(side="right")

        footer = tk.Frame(outer, bg=th.c("bg"))
        footer.pack(fill="x", pady=(14, 0))
        RoundedButton(
            footer,
            self.app,
            text=t("reset_stats"),
            icon="⌫",
            variant="danger",
            width=160,
            height=38,
            font_size=10,
            command=self._reset,
        ).pack(side="right")
        RoundedButton(
            footer,
            self.app,
            text=t("home"),
            icon="←",
            variant="ghost",
            width=120,
            height=38,
            font_size=10,
            command=self.app.show_home,
        ).pack(side="left")
        self.bind("<Escape>", lambda event: self.app.show_home())

    def _reset(self):
        if messagebox.askyesno(self.t("app_name"), self.t("reset_confirm")):
            self.app.storage.reset_progress()
            self.app.show_stats()


class SettingsScreen(Screen):
    def build(self):
        t = self.t
        th = self.theme
        settings = self.app.settings

        outer = tk.Frame(self, bg=th.c("bg"))
        outer.pack(fill="both", expand=True, padx=42, pady=24)

        self.topbar(outer, back=self.app.show_home, title=t("settings"))
        tk.Label(
            outer,
            text=t("settings"),
            bg=th.c("bg"),
            fg=th.c("text"),
            font=th.font(24, "bold"),
        ).pack(anchor="w", pady=(18, 0))
        tk.Label(
            outer,
            text=t("settings_subtitle"),
            bg=th.c("bg"),
            fg=th.c("muted"),
            font=th.font(10),
        ).pack(anchor="w", pady=(2, 14))

        columns = tk.Frame(outer, bg=th.c("bg"))
        columns.pack(fill="both", expand=True)
        columns.grid_columnconfigure(0, weight=1)
        columns.grid_columnconfigure(1, weight=1)
        columns.grid_rowconfigure(0, weight=1)
        columns.grid_rowconfigure(1, weight=1)

        appearance = Card(columns, self.app, padding=18)
        appearance.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        tk.Label(
            appearance,
            text=t("appearance"),
            bg=appearance["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        if limits.unlocked():
            self._row_label(appearance, t("theme")).pack(fill="x", pady=(0, 4))
            theme_var = tk.StringVar(value=settings.get("theme", "light"))
            SegmentedControl(
                appearance,
                self.app,
                options=[("light", t("light")), ("dark", t("dark"))],
                variable=theme_var,
                command=self._set_theme,
                height=34,
                font_size=9,
            ).pack(fill="x", pady=(0, 12))
        self._row_label(appearance, t("language_ui")).pack(fill="x", pady=(0, 4))
        lang_var = tk.StringVar(value=settings.get("ui_lang", "es"))
        SegmentedControl(
            appearance,
            self.app,
            options=[(code, name) for code, name in LANGUAGES.items()],
            variable=lang_var,
            command=self._set_ui_lang,
            height=34,
            font_size=9,
        ).pack(fill="x")

        practice = Card(columns, self.app, padding=18)
        practice.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        tk.Label(
            practice,
            text=t("practice"),
            bg=practice["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        self._toggle(practice, t("auto_advance"), "auto_advance").pack(
            fill="x", pady=4
        )
        self._toggle(practice, t("sound"), "sound").pack(fill="x", pady=4)
        if limits.unlocked():
            self._toggle(practice, t("fuzzy"), "fuzzy").pack(fill="x", pady=4)
            self._row_label(practice, t("daily_goal")).pack(fill="x", pady=(10, 4))
            goal_var = tk.StringVar(value=str(settings.get("daily_goal", 20)))
            SegmentedControl(
                practice,
                self.app,
                options=[("10", "10"), ("20", "20"), ("30", "30"), ("50", "50")],
                variable=goal_var,
                command=lambda value: self._set_setting("daily_goal", int(value)),
                height=32,
                font_size=9,
            ).pack(fill="x")

        data_card = Card(columns, self.app, padding=18)
        data_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        tk.Label(
            data_card,
            text=t("data_folder"),
            bg=data_card["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        tk.Label(
            data_card,
            text=str(self.app.storage.base),
            bg=data_card["bg"],
            fg=th.c("muted"),
            font=th.font(8),
            wraplength=300,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))
        row = tk.Frame(data_card, bg=data_card["bg"])
        row.pack(fill="x")
        RoundedButton(
            row,
            self.app,
            text=t("open_folder"),
            icon="↗",
            variant="secondary",
            width=140,
            height=34,
            font_size=9,
            command=self.app.open_data_folder,
        ).pack(side="left", padx=(0, 8))
        RoundedButton(
            row,
            self.app,
            text=t("reset_stats"),
            icon="⌫",
            variant="danger",
            width=140,
            height=34,
            font_size=9,
            command=self._reset,
        ).pack(side="left")

        about = Card(columns, self.app, padding=18)
        about.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        tk.Label(
            about,
            text=t("about"),
            bg=about["bg"],
            fg=th.c("text"),
            font=th.font(13, "bold"),
        ).pack(anchor="w", pady=(0, 6))
        tk.Label(
            about,
            text=f"{t('app_name')} {APP_EDITION} · v{APP_VERSION}",
            bg=about["bg"],
            fg=th.c("text"),
            font=th.font(10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            about,
            text=t("app_about"),
            bg=about["bg"],
            fg=th.c("muted"),
            font=th.font(9),
            wraplength=300,
            justify="left",
        ).pack(anchor="w", pady=(4, 10))
        links = tk.Frame(about, bg=about["bg"])
        links.pack(fill="x")
        RoundedButton(
            links,
            self.app,
            text=t("open_github"),
            icon="↗",
            variant="ghost",
            width=140,
            height=32,
            font_size=9,
            command=lambda: webbrowser.open(GITHUB_URL),
        ).pack(side="left", padx=(0, 8))
        RoundedButton(
            links,
            self.app,
            text=t("support"),
            icon="♥",
            variant="ghost",
            width=130,
            height=32,
            font_size=9,
            command=lambda: webbrowser.open(SUPPORT_URL),
        ).pack(side="left")

        self.saved_label = tk.Label(
            outer,
            text="",
            bg=th.c("bg"),
            fg=th.c("success"),
            font=th.font(9, "bold"),
        )
        self.saved_label.pack(anchor="w", pady=(10, 0))
        self.bind("<Escape>", lambda event: self.app.show_home())

    def _row_label(self, parent, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=parent["bg"],
            fg=self.theme.c("muted"),
            font=self.theme.font(10, "bold"),
            anchor="w",
        )

    def _toggle(self, parent, text: str, key: str) -> ToggleRow:
        variable = tk.BooleanVar(value=bool(self.app.settings.get(key, True)))
        return ToggleRow(
            parent,
            self.app,
            label=text,
            variable=variable,
            command=lambda value: self._set_setting(key, value),
        )

    def _set_setting(self, key: str, value) -> None:
        self.app.settings[key] = value
        self.app.storage.save_settings(self.app.settings)
        self._show_saved()

    def _set_theme(self, value: str) -> None:
        if value == self.app.settings.get("theme"):
            return
        self.app.set_theme(value)
        self.app.show_settings()

    def _set_ui_lang(self, value: str) -> None:
        if value == self.app.settings.get("ui_lang"):
            return
        self.app.set_ui_lang(value)

    def _show_saved(self, message: str | None = None) -> None:
        self.saved_label.config(text=message or self.t("saved"))

        def clear():
            try:
                self.saved_label.config(text="")
            except tk.TclError:
                pass

        self.after(1600, clear)

    def _reset(self) -> None:
        if messagebox.askyesno(self.t("app_name"), self.t("reset_confirm")):
            self.app.storage.reset_progress()
            self._show_saved(self.t("reset_done"))
