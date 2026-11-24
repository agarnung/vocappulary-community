"""Capacidades disponibles."""

from __future__ import annotations

ENABLED = False


def unlocked() -> bool:
    return ENABLED


def tolerant() -> bool:
    return False


def languages(codes) -> list[str]:
    return list(codes)[:1]


def modes() -> tuple:
    return ("learn",)


def session_lengths() -> tuple:
    return (10,)


def themes() -> tuple:
    return ("light",)
