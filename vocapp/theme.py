"""Paletas y tipografía de la aplicación."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#F4F6FB",
        "surface": "#FFFFFF",
        "surface_alt": "#EEF2F9",
        "surface_hover": "#E4EAF4",
        "text": "#172033",
        "muted": "#6B7280",
        "subtle": "#9AA4B2",
        "primary": "#4F46E5",
        "primary_hover": "#4338CA",
        "primary_soft": "#EEF0FF",
        "on_primary": "#FFFFFF",
        "success": "#16A34A",
        "success_soft": "#E9F8EF",
        "on_success": "#FFFFFF",
        "warning": "#C2740B",
        "warning_soft": "#FFF5E6",
        "on_warning": "#FFFFFF",
        "danger": "#DC2626",
        "danger_soft": "#FDECEC",
        "on_danger": "#FFFFFF",
        "border": "#E2E8F0",
        "shadow": "#0F172A",
        "overlay": "#0F172A",
        "white": "#FFFFFF",
    },
    "dark": {
        "bg": "#0B1220",
        "surface": "#151F32",
        "surface_alt": "#1D2A40",
        "surface_hover": "#263550",
        "text": "#F1F5F9",
        "muted": "#94A3B8",
        "subtle": "#64748B",
        "primary": "#6366F1",
        "primary_hover": "#818CF8",
        "primary_soft": "#1E2A55",
        "on_primary": "#FFFFFF",
        "success": "#22C55E",
        "success_soft": "#123524",
        "on_success": "#FFFFFF",
        "warning": "#FBBF24",
        "warning_soft": "#3A2A0A",
        "on_warning": "#1A1203",
        "danger": "#F87171",
        "danger_soft": "#3A1414",
        "on_danger": "#1A0B0B",
        "border": "#2A3A55",
        "shadow": "#000000",
        "overlay": "#000000",
        "white": "#FFFFFF",
    },
}

FONT_CANDIDATES = [
    "Inter",
    "Segoe UI Variable",
    "Segoe UI",
    "SF Pro Display",
    "Helvetica Neue",
    "DejaVu Sans",
    "Arial",
    "Helvetica",
]


def detect_font(root: tk.Misc | None = None) -> str:
    try:
        families = set(tkfont.families(root))
    except tk.TclError:
        families = set()
    for family in FONT_CANDIDATES:
        if family in families:
            return family
    return "TkDefaultFont"


class Theme:
    def __init__(self, mode: str = "light", root: tk.Misc | None = None):
        self.mode = mode if mode in PALETTES else "light"
        self.colors = dict(PALETTES[self.mode])
        self.family = detect_font(root)

    def c(self, name: str, fallback: str | None = None) -> str:
        return self.colors.get(name, fallback or name)

    def font(self, size: int = 12, weight: str = "normal"):
        return (self.family, size, weight)

    def font_obj(self, size: int = 12, weight: str = "normal") -> tkfont.Font:
        return tkfont.Font(family=self.family, size=size, weight=weight)
