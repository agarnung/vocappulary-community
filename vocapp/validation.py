"""Validación tolerante de respuestas.

Acepta mayúsculas, espacios extra, tildes, artículos, plurales sencillos,
erratas leves y alternativas separadas por ``/``, ``;`` o ``|``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

ARTICLES = (
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "the", "a", "an",
    "le", "les", "l", "une", "des", "du", "de",
)

_PUNCT_RE = re.compile(r"[^\w\s'\-]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+", re.UNICODE)
_ARTICLE_RE = re.compile(
    r"^(?:" + "|".join(sorted(ARTICLES, key=len, reverse=True)) + r")\s+",
    re.UNICODE,
)
_ELISION_RE = re.compile(r"^(?:l|d|j|t|m|n|s|c|qu)'", re.UNICODE)
_PAREN_RE = re.compile(r"\([^)]*\)")
_SPLIT_RE = re.compile(r"\s*[/;|]\s*")


@dataclass
class ValidationResult:
    status: str  # correct | almost | wrong
    expected: str
    reason: str = ""
    distance: int = 0
    matched: str = ""

    @property
    def is_correct(self) -> bool:
        return self.status == "correct"

    @property
    def is_almost(self) -> bool:
        return self.status == "almost"


def strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def normalize(text: str, remove_articles: bool = True) -> str:
    text = unicodedata.normalize("NFKC", str(text or "")).lower().strip()
    text = text.replace("’", "'").replace("`", "'").replace("´", "'")
    text = _PAREN_RE.sub(" ", text)
    text = _PUNCT_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()
    text = re.sub(r"^to\s+", "", text)
    text = re.sub(r"^se\s+", "", text)
    text = _ELISION_RE.sub("", text)
    if remove_articles:
        text = _ARTICLE_RE.sub("", text)
        text = _SPACE_RE.sub(" ", text).strip()
    return text


def split_expected(expected) -> list[str]:
    if expected is None:
        return []
    if isinstance(expected, str):
        expected = [expected]
    items: list[str] = []
    seen: set[str] = set()
    for item in expected:
        for part in _SPLIT_RE.split(str(item)):
            part = part.strip()
            if not part:
                continue
            key = normalize(part)
            if key and key not in seen:
                seen.add(key)
                items.append(part)
    return items


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            insert = previous[j] + 1
            delete = current[j - 1] + 1
            replace = previous[j - 1] + (ca != cb)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]


def _plural_match(a: str, b: str) -> bool:
    pairs = (("s", ""), ("es", ""), ("s", "es"))
    for suffix_a, suffix_b in pairs:
        if a.endswith(suffix_a) and a[: -len(suffix_a)] == b + suffix_b:
            return True
        if b.endswith(suffix_a) and b[: -len(suffix_a)] == a + suffix_b:
            return True
    return False


def compare_answer(
    answer: str, expected, fuzzy: bool = True, tolerant: bool = True
) -> ValidationResult:
    raw = str(answer or "").strip()
    items = split_expected(expected)
    if not raw:
        return ValidationResult("wrong", items[0] if items else "", "empty")
    if not items:
        return ValidationResult("wrong", "", "no_expected")

    ans_norm = normalize(raw, remove_articles=False)
    ans_plain = normalize(raw, remove_articles=True)
    ans_noaccent = strip_accents(ans_plain)

    if not tolerant:
        for item in items:
            if ans_norm == normalize(item, remove_articles=False):
                return ValidationResult("correct", item, "exact", 0, item)
        return ValidationResult("wrong", items[0], "wrong")

    best_item = items[0]
    best_distance = 10**9

    for item in items:
        exp_norm = normalize(item, remove_articles=False)
        exp_plain = normalize(item, remove_articles=True)
        exp_noaccent = strip_accents(exp_plain)

        if ans_norm == exp_norm:
            return ValidationResult("correct", item, "exact", 0, item)

        distance = levenshtein(ans_norm, exp_norm)
        if distance < best_distance:
            best_distance = distance
            best_item = item

        if ans_plain == exp_plain:
            return ValidationResult("almost", item, "article", 0, item)

        if ans_noaccent == exp_noaccent:
            return ValidationResult("almost", item, "accent", 0, item)

        if _plural_match(ans_plain, exp_plain):
            return ValidationResult("almost", item, "plural", 0, item)

        if fuzzy and len(exp_noaccent) >= 4:
            limit = 1 if len(exp_noaccent) <= 7 else 2
            distance_noaccent = levenshtein(ans_noaccent, exp_noaccent)
            if 0 < distance_noaccent <= limit:
                return ValidationResult("almost", item, "typo", distance_noaccent, item)

    return ValidationResult("wrong", best_item, "wrong", best_distance)
