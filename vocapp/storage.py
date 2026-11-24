"""Persistencia de ajustes, estadísticas y repetición espaciada."""

from __future__ import annotations

import copy
import json
import os
from datetime import date, timedelta
from pathlib import Path

from .config import app_data_dir

DEFAULT_SETTINGS = {
    "ui_lang": "es",
    "theme": "light",
    "source_lang": "fr",
    "direction": "to_es",
    "practice_mode": "learn",
    "category": "all",
    "session_length": 10,
    "auto_advance": True,
    "sound": True,
    "fuzzy": True,
    "daily_goal": 20,
}

DEFAULT_STATS = {
    "total_answers": 0,
    "correct": 0,
    "almost": 0,
    "wrong": 0,
    "current_streak": 0,
    "best_streak": 0,
    "sessions": 0,
    "daily": {},
    "per_language": {},
    "words": {},
}

SRS_INTERVALS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 16}


def today() -> str:
    return date.today().isoformat()


class Storage:
    def __init__(self, base_dir: str | Path | None = None):
        self.base = Path(base_dir) if base_dir else app_data_dir()
        self.base.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.base / "settings.json"
        self.stats_path = self.base / "stats.json"
        self.srs_path = self.base / "srs.json"
        self.settings = self._load(self.settings_path, DEFAULT_SETTINGS)
        self.stats = self._load(self.stats_path, DEFAULT_STATS)
        self.srs = self._load(self.srs_path, {})
        self._sanitize()

    # ------------------------------------------------------------------ files
    def _sanitize(self) -> None:
        if not isinstance(self.settings, dict):
            self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        for key in ("auto_advance", "sound", "fuzzy"):
            value = self.settings.get(key, True)
            if not isinstance(value, bool):
                self.settings[key] = str(value).lower() in (
                    "1",
                    "true",
                    "yes",
                    "on",
                )
        if not isinstance(self.stats, dict):
            self.stats = copy.deepcopy(DEFAULT_STATS)
        for key in ("daily", "per_language", "words"):
            if not isinstance(self.stats.get(key), dict):
                self.stats[key] = {}
        for key, value in list(self.stats["daily"].items()):
            if not isinstance(value, dict):
                self.stats["daily"][key] = {
                    "answers": 0,
                    "correct": 0,
                    "almost": 0,
                    "wrong": 0,
                }
        for key, value in list(self.stats["per_language"].items()):
            if not isinstance(value, dict):
                self.stats["per_language"][key] = {
                    "answers": 0,
                    "correct": 0,
                    "almost": 0,
                    "wrong": 0,
                }
        for key, value in list(self.stats["words"].items()):
            if not isinstance(value, dict):
                del self.stats["words"][key]
        if not isinstance(self.srs, dict):
            self.srs = {}
        for key, value in list(self.srs.items()):
            if not isinstance(value, dict):
                del self.srs[key]
        for key in (
            "total_answers",
            "correct",
            "almost",
            "wrong",
            "current_streak",
            "best_streak",
            "sessions",
        ):
            try:
                self.stats[key] = int(self.stats.get(key, 0))
            except (TypeError, ValueError):
                self.stats[key] = 0

    def _load(self, path: Path, default: dict) -> dict:
        if not path.exists():
            return copy.deepcopy(default)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return copy.deepcopy(default)
        merged = copy.deepcopy(default)
        if isinstance(data, dict):
            merged.update(data)
        return merged

    def _save(self, path: Path, data: dict) -> None:
        try:
            tmp = path.with_name(path.name + ".tmp")
            with open(tmp, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except OSError:
            pass

    # --------------------------------------------------------------- settings
    def load_settings(self) -> dict:
        self.settings = self._load(self.settings_path, DEFAULT_SETTINGS)
        return self.settings

    def save_settings(self, settings: dict | None = None) -> None:
        if settings is not None:
            self.settings = settings
        self._save(self.settings_path, self.settings)

    # ------------------------------------------------------------------ stats
    def save_stats(self) -> None:
        self._save(self.stats_path, self.stats)

    def record_answer(
        self, lang: str, direction: str, word: str, status: str, expected: str = ""
    ) -> None:
        stats = self.stats
        stats["total_answers"] = int(stats.get("total_answers", 0)) + 1
        key = status if status in ("correct", "almost", "wrong") else "wrong"
        stats[key] = int(stats.get(key, 0)) + 1

        if key in ("correct", "almost"):
            stats["current_streak"] = int(stats.get("current_streak", 0)) + 1
        else:
            stats["current_streak"] = 0
        stats["best_streak"] = max(
            int(stats.get("best_streak", 0)), int(stats["current_streak"])
        )

        day = today()
        daily = stats.setdefault("daily", {})
        bucket = daily.setdefault(
            day, {"answers": 0, "correct": 0, "almost": 0, "wrong": 0}
        )
        bucket["answers"] = int(bucket.get("answers", 0)) + 1
        bucket[key] = int(bucket.get(key, 0)) + 1

        per_lang = stats.setdefault("per_language", {})
        lang_stats = per_lang.setdefault(
            lang, {"answers": 0, "correct": 0, "almost": 0, "wrong": 0}
        )
        lang_stats["answers"] = int(lang_stats.get("answers", 0)) + 1
        lang_stats[key] = int(lang_stats.get(key, 0)) + 1

        words = stats.setdefault("words", {})
        word_key = f"{lang}::{word}"
        word_stats = words.setdefault(
            word_key,
            {"seen": 0, "correct": 0, "almost": 0, "wrong": 0, "last": day},
        )
        word_stats["seen"] = int(word_stats.get("seen", 0)) + 1
        word_stats[key] = int(word_stats.get(key, 0)) + 1
        word_stats["last"] = day

        self.save_stats()
        self.update_srs(lang, direction, word, key in ("correct", "almost"))

    def record_session(self) -> None:
        self.stats["sessions"] = int(self.stats.get("sessions", 0)) + 1
        self.save_stats()

    def accuracy(self, lang: str | None = None) -> float:
        if lang:
            data = self.stats.get("per_language", {}).get(lang, {})
        else:
            data = self.stats
        if not isinstance(data, dict):
            return 0.0
        total = int(data.get("answers", data.get("total_answers", 0)))
        if not total:
            return 0.0
        good = int(data.get("correct", 0)) + int(data.get("almost", 0)) * 0.5
        return max(0.0, min(100.0, good / total * 100.0))

    def daily_answers(self, day: str | None = None) -> int:
        bucket = self.stats.get("daily", {}).get(day or today(), {})
        if not isinstance(bucket, dict):
            return 0
        return int(bucket.get("answers", 0))

    def activity(self, days: int = 7) -> list[tuple[str, int, int]]:
        result: list[tuple[str, int, int]] = []
        current = date.today()
        for offset in range(days - 1, -1, -1):
            day = (current - timedelta(days=offset)).isoformat()
            bucket = self.stats.get("daily", {}).get(day, {})
            answers = int(bucket.get("answers", 0))
            good = int(bucket.get("correct", 0)) + int(bucket.get("almost", 0))
            result.append((day, answers, good))
        return result

    def hardest_words(self, limit: int = 5) -> list[tuple[str, str, dict]]:
        items: list[tuple[str, str, dict]] = []
        for key, data in self.stats.get("words", {}).items():
            if not isinstance(data, dict) or int(data.get("wrong", 0)) <= 0:
                continue
            if "::" in key:
                lang, word = key.split("::", 1)
            else:
                lang, word = "", key
            items.append((lang, word, data))
        items.sort(
            key=lambda item: (int(item[2].get("wrong", 0)), int(item[2].get("seen", 0))),
            reverse=True,
        )
        return items[:limit]

    def reset_progress(self) -> None:
        self.stats = copy.deepcopy(DEFAULT_STATS)
        self.srs = {}
        self.save_stats()
        self._save(self.srs_path, self.srs)

    # -------------------------------------------------------------------- srs
    @staticmethod
    def srs_key(lang: str, direction: str, word: str) -> str:
        return f"{lang}:{direction}:{word}"

    def save_srs(self) -> None:
        self._save(self.srs_path, self.srs)

    def get_srs(self, lang: str, direction: str, word: str) -> dict | None:
        item = self.srs.get(self.srs_key(lang, direction, word))
        return item if isinstance(item, dict) else None

    def is_due(self, item: dict | None) -> bool:
        if not isinstance(item, dict):
            return True
        due = item.get("due")
        if not due:
            return True
        try:
            return date.fromisoformat(str(due)) <= date.today()
        except ValueError:
            return True

    def update_srs(
        self, lang: str, direction: str, word: str, correct: bool
    ) -> None:
        key = self.srs_key(lang, direction, word)
        item = self.srs.setdefault(
            key,
            {"box": 1, "due": today(), "seen": 0, "correct": 0, "wrong": 0},
        )
        item["seen"] = int(item.get("seen", 0)) + 1
        if correct:
            item["correct"] = int(item.get("correct", 0)) + 1
            item["box"] = min(5, int(item.get("box", 1)) + 1)
        else:
            item["wrong"] = int(item.get("wrong", 0)) + 1
            item["box"] = 1
        box = int(item.get("box", 1))
        interval = SRS_INTERVALS.get(box, 0)
        item["due"] = (date.today() + timedelta(days=interval)).isoformat()
        item["last"] = today()
        self.save_srs()

    def due_count(self, entries, lang: str, direction: str) -> int:
        count = 0
        for entry in entries:
            item = self.get_srs(lang, direction, entry.source)
            if self.is_due(item):
                count += 1
        return count

    def learned_count(self, entries, lang: str, direction: str) -> int:
        count = 0
        for entry in entries:
            item = self.get_srs(lang, direction, entry.source)
            if item and int(item.get("box", 1)) >= 4:
                count += 1
        return count

    def new_count(self, entries, lang: str, direction: str) -> int:
        return sum(
            1
            for entry in entries
            if self.get_srs(lang, direction, entry.source) is None
        )
