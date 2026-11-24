"""Lógica de una sesión de práctica."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from . import limits
from .validation import ValidationResult, compare_answer, normalize


@dataclass
class Question:
    entry: object
    prompt: str
    expected: list[str]
    direction: str


@dataclass
class AnswerRecord:
    entry: object
    prompt: str
    answer: str
    status: str
    expected: str
    reason: str = ""
    hint_used: bool = False


class Session:
    def __init__(self, vocab, storage, settings: dict, lang: str, entries=None):
        self.vocab = vocab
        self.storage = storage
        self.settings = settings
        self.lang = lang
        self.direction = settings.get("direction", "to_es")
        self.entries = list(entries) if entries is not None else self._build_pool()
        self.questions = [self._make_question(entry) for entry in self.entries]
        self.index = 0
        self.records: list[AnswerRecord] = []
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.hints = 0
        self.hint_used = False
        self.started_at = time.time()

    # ------------------------------------------------------------------ pool
    def _build_pool(self):
        entries = self.vocab.entries(self.lang)
        category = self.settings.get("category", "all")
        if category and category != "all":
            entries = [entry for entry in entries if entry.category == category]
        if not entries:
            return []

        due: list = []
        unseen: list = []
        seen: list = []
        for entry in entries:
            item = self.storage.get_srs(self.lang, self.direction, entry.source)
            if item is None or int(item.get("seen", 0)) == 0:
                unseen.append(entry)
            elif self.storage.is_due(item):
                due.append(entry)
            else:
                seen.append(entry)

        random.shuffle(due)
        random.shuffle(unseen)
        random.shuffle(seen)

        mode = self.settings.get("practice_mode", "learn")
        if mode == "review":
            pool = due + seen + unseen
        elif mode == "quick":
            pool = entries[:]
            random.shuffle(pool)
        else:
            pool = due + unseen + seen

        length = self.settings.get("session_length", 10)
        if length != "all":
            try:
                pool = pool[: max(1, int(length))]
            except (TypeError, ValueError):
                pool = pool[:10]
        return pool

    # -------------------------------------------------------------- questions
    def _make_question(self, entry) -> Question:
        if self.direction == "to_es":
            prompt = entry.source
            expected = list(entry.translations)
        else:
            prompt = random.choice(entry.translations)
            expected = self.vocab.reverse_lookup(self.lang, prompt)
            if entry.source not in expected:
                expected = [entry.source] + expected
            deduped: list[str] = []
            seen: set[str] = set()
            for item in expected:
                key = normalize(item)
                if key and key not in seen:
                    seen.add(key)
                    deduped.append(item)
            expected = deduped
        return Question(entry=entry, prompt=prompt, expected=expected, direction=self.direction)

    def current(self) -> Question | None:
        if 0 <= self.index < len(self.questions):
            return self.questions[self.index]
        return None

    def advance(self) -> None:
        self.index += 1
        self.hint_used = False

    def mark_hint(self) -> None:
        self.hints += 1
        self.hint_used = True

    def is_finished(self) -> bool:
        return self.index >= len(self.questions)

    # ----------------------------------------------------------------- answers
    def submit(self, answer: str) -> ValidationResult | None:
        question = self.current()
        if question is None:
            return None
        result = compare_answer(
            answer,
            question.expected,
            fuzzy=bool(self.settings.get("fuzzy", True)),
            tolerant=limits.tolerant(),
        )
        self._record(question, answer, result)
        return result

    def skip(self) -> ValidationResult | None:
        question = self.current()
        if question is None:
            return None
        expected = question.expected[0] if question.expected else ""
        result = ValidationResult("wrong", expected, "skipped")
        self._record(question, "", result)
        return result

    def _record(self, question: Question, answer: str, result: ValidationResult) -> None:
        self.records.append(
            AnswerRecord(
                entry=question.entry,
                prompt=question.prompt,
                answer=answer,
                status=result.status,
                expected=result.expected,
                reason=result.reason,
                hint_used=self.hint_used,
            )
        )
        self.storage.record_answer(
            self.lang,
            self.direction,
            question.entry.source,
            result.status,
            result.expected,
        )
        if result.status == "correct":
            self.score += 10
            self.streak += 1
        elif result.status == "almost":
            self.score += 5
            self.streak += 1
        else:
            self.streak = 0
        self.best_streak = max(self.best_streak, self.streak)

    # ---------------------------------------------------------------- summary
    def summary(self) -> dict:
        total = len(self.records)
        correct = sum(1 for record in self.records if record.status == "correct")
        almost = sum(1 for record in self.records if record.status == "almost")
        wrong = sum(1 for record in self.records if record.status == "wrong")
        if total:
            accuracy = (correct + almost * 0.5) / total * 100
        else:
            accuracy = 0.0
        return {
            "lang": self.lang,
            "direction": self.direction,
            "score": self.score,
            "total": total,
            "correct": correct,
            "almost": almost,
            "wrong": wrong,
            "accuracy": accuracy,
            "best_streak": self.best_streak,
            "elapsed": time.time() - self.started_at,
            "records": self.records,
            "missed": [record for record in self.records if record.status == "wrong"],
            "settings": dict(self.settings),
        }
