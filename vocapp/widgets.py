"""Widgets ligeros con estética moderna sobre Tkinter."""

from __future__ import annotations

import tkinter as tk


def rounded_points(x1: float, y1: float, x2: float, y2: float, radius: float):
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
        x1 + radius, y1,
    ]


def parent_bg(widget: tk.Misc, theme) -> str:
    try:
        return str(widget.cget("bg"))
    except tk.TclError:
        return theme.c("bg")


def bind_tree(widget: tk.Misc, event: str, callback) -> None:
    widget.bind(event, callback)
    for child in widget.winfo_children():
        bind_tree(child, event, callback)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        app,
        text: str = "",
        command=None,
        variant: str = "primary",
        width: int = 160,
        height: int = 44,
        radius: int = 12,
        font_size: int = 12,
        bold: bool = True,
        icon: str = "",
        bg: str | None = None,
        **kwargs,
    ):
        self.app = app
        self.theme = app.theme
        self.variant = variant
        self.command = command
        self.radius = radius
        self.font_size = font_size
        self.bold = bold
        self.icon = icon
        self.text = text
        self._enabled = True
        self._hover = False
        self._pressed = False
        self._bg = bg or parent_bg(parent, self.theme)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            takefocus=1,
            **kwargs,
        )
        self.bind("<Configure>", lambda event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Return>", lambda event: self._invoke())
        self.bind("<space>", lambda event: self._invoke())
        self.bind("<FocusIn>", lambda event: self._draw())
        self.bind("<FocusOut>", lambda event: self._draw())
        self._draw()

    def _colors(self):
        t = self.theme.c
        if not self._enabled:
            return t("surface_alt"), t("subtle"), t("border")
        if self.variant == "primary":
            fill = t("primary_hover") if self._hover or self._pressed else t("primary")
            return fill, t("on_primary"), fill
        if self.variant == "success":
            fill = t("success")
            return fill, t("on_success"), fill
        if self.variant == "danger":
            fill = t("danger")
            return fill, t("on_danger"), fill
        if self.variant == "warning":
            fill = t("warning")
            return fill, t("on_warning"), fill
        if self.variant == "ghost":
            fill = t("surface_alt") if self._hover else self._bg
            return fill, t("text"), fill
        fill = t("surface_hover") if self._hover else t("surface_alt")
        return fill, t("text"), t("border")

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        fill, foreground, outline = self._colors()
        self.create_polygon(
            rounded_points(1, 1, width - 1, height - 1, self.radius),
            smooth=True,
            fill=fill,
            outline=outline,
            width=1,
        )
        label = self.text
        if self.icon:
            label = f"{self.icon}  {label}" if label else self.icon
        if label:
            self.create_text(
                width / 2,
                height / 2,
                text=label,
                fill=foreground,
                font=self.theme.font(
                    self.font_size, "bold" if self.bold else "normal"
                ),
            )
        if self.focus_get() is self:
            self.create_polygon(
                rounded_points(2, 2, width - 2, height - 2, max(1, self.radius - 2)),
                smooth=True,
                fill="",
                outline=self.theme.c("primary"),
                width=1,
            )

    def _on_enter(self, event=None):
        if self._enabled:
            self._hover = True
            self.configure(cursor="hand2")
            self._draw()

    def _on_leave(self, event=None):
        self._hover = False
        self._pressed = False
        self.configure(cursor="")
        self._draw()

    def _on_press(self, event=None):
        if not self._enabled:
            return
        self._pressed = True
        self.focus_set()
        self._draw()

    def _on_release(self, event=None):
        if not self._enabled:
            return
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        if was_pressed and self._hover:
            self._invoke()

    def _invoke(self):
        if self._enabled and self.command:
            self.command()

    def set_text(self, text: str) -> None:
        self.text = text
        self._draw()

    def set_icon(self, icon: str) -> None:
        self.icon = icon
        self._draw()

    def set_variant(self, variant: str) -> None:
        self.variant = variant
        self._draw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self.configure(cursor="hand2" if enabled and self._hover else "")
        self._draw()

    def set_command(self, command) -> None:
        self.command = command


class Card(tk.Frame):
    def __init__(
        self,
        parent,
        app,
        padding: int = 18,
        bg: str | None = None,
        border: bool = True,
        **kwargs,
    ):
        self.theme = app.theme
        super().__init__(
            parent,
            bg=bg or self.theme.c("surface"),
            padx=padding,
            pady=padding,
            highlightthickness=1 if border else 0,
            highlightbackground=self.theme.c("border"),
            highlightcolor=self.theme.c("border"),
            bd=0,
            **kwargs,
        )


class SelectableCard(Card):
    def __init__(self, parent, app, selected=False, command=None, **kwargs):
        super().__init__(parent, app, **kwargs)
        self.command = command
        self.selected = selected
        self._apply()
        bind_tree(self, "<Button-1>", self._click)

    def _click(self, event=None):
        if self.command:
            self.command()

    def set_selected(self, selected: bool) -> None:
        self.selected = bool(selected)
        self._apply()

    def _apply(self) -> None:
        self.configure(
            highlightbackground=self.theme.c("primary")
            if self.selected
            else self.theme.c("border"),
            highlightcolor=self.theme.c("primary")
            if self.selected
            else self.theme.c("border"),
            highlightthickness=2 if self.selected else 1,
        )


class StatTile(Card):
    def __init__(self, parent, app, value: str, label: str, accent: str | None = None, **kwargs):
        super().__init__(parent, app, padding=10, **kwargs)
        self.value_label = tk.Label(
            self,
            text=value,
            bg=self["bg"],
            fg=accent or self.theme.c("text"),
            font=self.theme.font(20, "bold"),
            anchor="w",
        )
        self.value_label.pack(anchor="w")
        self.label = tk.Label(
            self,
            text=label,
            bg=self["bg"],
            fg=self.theme.c("muted"),
            font=self.theme.font(9),
            anchor="w",
        )
        self.label.pack(anchor="w", pady=(2, 0))

    def set_value(self, value: str) -> None:
        self.value_label.config(text=value)


class ProgressBar(tk.Canvas):
    def __init__(self, parent, app, height: int = 10, **kwargs):
        self.theme = app.theme
        super().__init__(
            parent,
            height=height,
            bg=parent_bg(parent, self.theme),
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self.ratio = 0.0
        self.bind("<Configure>", lambda event: self._draw())
        self._draw()

    def set_ratio(self, ratio: float) -> None:
        self.ratio = max(0.0, min(1.0, float(ratio)))
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        radius = height / 2
        self.create_polygon(
            rounded_points(0, 0, width, height, radius),
            smooth=True,
            fill=self.theme.c("surface_alt"),
            outline="",
        )
        if self.ratio > 0:
            filled = max(height, width * self.ratio)
            self.create_polygon(
                rounded_points(0, 0, filled, height, radius),
                smooth=True,
                fill=self.theme.c("primary"),
                outline="",
            )


class Pill(tk.Label):
    def __init__(
        self,
        parent,
        app,
        text: str,
        fg: str | None = None,
        bg: str | None = None,
        height: int = 28,
        padx: int = 12,
        font_size: int = 10,
        **kwargs,
    ):
        self.theme = app.theme
        super().__init__(
            parent,
            text=text,
            bg=bg or self.theme.c("surface_alt"),
            fg=fg or self.theme.c("text"),
            font=self.theme.font(font_size, "bold"),
            padx=padx,
            pady=4,
            **kwargs,
        )

    def set_text(self, text: str, fg: str | None = None, bg: str | None = None) -> None:
        self.config(text=text)
        if fg is not None:
            self.config(fg=fg)
        if bg is not None:
            self.config(bg=bg)


class SegmentedControl(tk.Frame):
    def __init__(
        self,
        parent,
        app,
        options: list[tuple[str, str]],
        variable: tk.StringVar,
        command=None,
        height: int = 38,
        font_size: int = 10,
        **kwargs,
    ):
        self.app = app
        self.theme = app.theme
        self.options = options
        self.variable = variable
        self.command = command
        super().__init__(parent, bg=parent_bg(parent, self.theme), **kwargs)
        self.buttons: dict[str, RoundedButton] = {}
        for value, label in options:
            selected = variable.get() == value
            button = RoundedButton(
                self,
                app,
                text=label,
                variant="primary" if selected else "secondary",
                width=70,
                height=height,
                font_size=font_size,
                command=lambda v=value: self._select(v),
            )
            button.pack(side="left", fill="x", expand=True, padx=(0, 6))
            self.buttons[value] = button

    def _select(self, value: str) -> None:
        self.set_value(value)
        if self.command:
            self.command(value)

    def set_value(self, value: str) -> None:
        self.variable.set(value)
        for option_value, button in self.buttons.items():
            button.set_variant("primary" if option_value == value else "secondary")


class ToggleRow(tk.Frame):
    def __init__(
        self,
        parent,
        app,
        label: str,
        variable: tk.BooleanVar,
        command=None,
        **kwargs,
    ):
        self.app = app
        self.theme = app.theme
        self.bool_var = variable
        self.command = command
        super().__init__(parent, bg=parent_bg(parent, self.theme), **kwargs)
        text = tk.Label(
            self,
            text=label,
            bg=self["bg"],
            fg=self.theme.c("text"),
            font=self.theme.font(11),
            anchor="w",
        )
        text.pack(side="left", fill="x", expand=True)
        self.string_var = tk.StringVar(value="on" if variable.get() else "off")
        self.segmented = SegmentedControl(
            self,
            app,
            options=[("on", app.t("on")), ("off", app.t("off"))],
            variable=self.string_var,
            command=self._changed,
            height=34,
            font_size=9,
        )
        self.segmented.pack(side="right")

    def _changed(self, value: str) -> None:
        enabled = value == "on"
        self.bool_var.set(enabled)
        if self.command:
            self.command(enabled)


class EntryField(tk.Frame):
    def __init__(
        self,
        parent,
        app,
        placeholder: str = "",
        font_size: int = 18,
        **kwargs,
    ):
        self.app = app
        self.theme = app.theme
        self.placeholder = placeholder
        self._placeholder_active = False
        super().__init__(
            parent,
            bg=self.theme.c("border"),
            padx=1,
            pady=1,
            **kwargs,
        )
        self.inner = tk.Frame(self, bg=self.theme.c("surface_alt"))
        self.inner.pack(fill="both", expand=True)
        self.entry = tk.Entry(
            self.inner,
            font=self.theme.font(font_size),
            bg=self.theme.c("surface_alt"),
            fg=self.theme.c("text"),
            insertbackground=self.theme.c("text"),
            readonlybackground=self.theme.c("surface_alt"),
            disabledbackground=self.theme.c("surface_alt"),
            disabledforeground=self.theme.c("muted"),
            selectbackground=self.theme.c("primary_soft"),
            selectforeground=self.theme.c("text"),
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.entry.pack(fill="x", expand=True, padx=14, pady=12)
        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        if not self.entry.get():
            self._placeholder_active = True
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.theme.c("subtle"))

    def _clear_placeholder(self) -> None:
        if self._placeholder_active:
            self.entry.delete(0, "end")
            self._placeholder_active = False
            self.entry.config(fg=self.theme.c("text"))

    def _focus_in(self, event=None) -> None:
        if str(self.entry.cget("state")) == "readonly":
            return
        self.configure(bg=self.theme.c("primary"))
        self._clear_placeholder()

    def _focus_out(self, event=None) -> None:
        if str(self.entry.cget("state")) == "readonly":
            return
        self.configure(bg=self.theme.c("border"))
        if not self.entry.get():
            self._show_placeholder()

    def get(self) -> str:
        if self._placeholder_active:
            return ""
        return self.entry.get()

    def clear(self) -> None:
        self.entry.config(state="normal")
        self._clear_placeholder()
        self.entry.delete(0, "end")
        self.entry.focus_set()

    def focus(self) -> None:
        self.entry.focus_set()

    def set_readonly(self, readonly: bool) -> None:
        self.entry.config(state="readonly" if readonly else "normal")

    def bind_return(self, callback) -> None:
        self.entry.bind("<Return>", lambda event: callback())
