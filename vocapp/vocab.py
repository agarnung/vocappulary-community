"""Carga y normalización de vocabularios y packs de idiomas."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from .config import find_data_file
from .validation import normalize


@dataclass
class WordEntry:
    source: str
    translations: list[str]
    category: str = "general"
    language: str = ""

    @property
    def display_translations(self) -> str:
        return " · ".join(self.translations)


@dataclass
class LanguageInfo:
    code: str
    names: dict[str, str]
    label: str
    color: str
    files: list[str] = field(default_factory=list)
    categories_file: str | None = None

    def name(self, ui_lang: str = "es") -> str:
        return self.names.get(ui_lang) or self.names.get("es") or self.code.upper()


class Vocabulary:
    def __init__(self, search_dirs: list[str | Path] | None = None):
        self.search_dirs = [Path(d) for d in search_dirs] if search_dirs else None
        self.languages: dict[str, LanguageInfo] = {}
        self.category_names: dict[str, dict[str, str]] = {}
        self._entries: dict[str, list[WordEntry]] = {}
        self._reverse: dict[str, dict[str, list[str]]] = {}
        self._categories: dict[str, dict[str, int]] = {}
        self._load_registry()

    # ------------------------------------------------------------------ paths
    def _find(self, relative: str | None) -> Path | None:
        if not relative:
            return None
        rel = Path(relative)
        if rel.is_absolute():
            return rel if rel.is_file() else None
        if self.search_dirs:
            for directory in self.search_dirs:
                for candidate in (directory / rel, directory / "data" / rel):
                    if candidate.is_file():
                        return candidate
        return find_data_file(relative)

    def _load_json(self, relative: str | None):
        path = self._find(relative)
        if not path:
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None

    # --------------------------------------------------------------- registry
    def _load_registry(self) -> None:
        names = self._load_json("data/category_names.json") or self._load_json(
            "category_names.json"
        )
        if isinstance(names, dict):
            for category, values in names.items():
                if isinstance(values, dict):
                    self.category_names.setdefault(str(category), {}).update(
                        {str(k): str(v) for k, v in values.items()}
                    )
        registry = self._load_json("data/languages.json") or self._load_json("languages.json")
        if not isinstance(registry, dict) or not registry:
            self.languages = {
                "en": LanguageInfo(
                    "en",
                    {"es": "Inglés", "en": "English", "fr": "Anglais"},
                    "EN",
                    "#2563EB",
                    ["palabras_en.json"],
                ),
                "fr": LanguageInfo(
                    "fr",
                    {"es": "Francés", "en": "French", "fr": "Français"},
                    "FR",
                    "#E11D48",
                    ["palabras_fr.json"],
                ),
            }
            return
        for code, info in registry.items():
            if not isinstance(info, dict):
                continue
            names = info.get("name", {})
            if not isinstance(names, dict):
                names = {}
            files = info.get("files", [])
            if isinstance(files, str):
                files = [files]
            elif not isinstance(files, list):
                files = []
            categories_file = info.get("categories")
            self.languages[str(code)] = LanguageInfo(
                code=str(code),
                names={str(k): str(v) for k, v in names.items()},
                label=str(info.get("label", str(code).upper())),
                color=str(info.get("color", "#4F46E5")),
                files=[str(f) for f in files],
                categories_file=str(categories_file)
                if categories_file
                else None,
            )

    # ------------------------------------------------------------------ loading
    def _read_words(self, path: Path) -> tuple[dict, str, dict[str, str]]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}, "general", {}
        if not isinstance(data, dict):
            return {}, "general", {}
        if "words" in data and isinstance(data["words"], dict):
            meta = data.get("meta", {})
            if not isinstance(meta, dict):
                meta = {}
            category = str(meta.get("category", "general"))
            names = meta.get("name")
            if isinstance(names, dict):
                self.category_names.setdefault(category, {}).update(
                    {str(k): str(v) for k, v in names.items()}
                )
            raw_names = data.get("category_names")
            if isinstance(raw_names, dict):
                for name_category, name_values in raw_names.items():
                    if isinstance(name_values, dict):
                        self.category_names.setdefault(
                            str(name_category), {}
                        ).update(
                            {str(k): str(v) for k, v in name_values.items()}
                        )
            pack_categories: dict[str, str] = {}
            raw_categories = data.get("categories")
            if isinstance(raw_categories, dict):
                for word, value in raw_categories.items():
                    if isinstance(value, str):
                        pack_categories[str(word)] = value
                    elif isinstance(value, dict):
                        value_category = value.get("category")
                        if value_category:
                            pack_categories[str(word)] = str(value_category)
                        value_names = value.get("name")
                        if value_category and isinstance(value_names, dict):
                            self.category_names.setdefault(
                                str(value_category), {}
                            ).update(
                                {str(k): str(v) for k, v in value_names.items()}
                            )
            return data["words"], category, pack_categories
        return data, "general", {}

    def _load_category_map(self, info: LanguageInfo) -> dict[str, str]:
        data = self._load_json(info.categories_file)
        mapping: dict[str, str] = {}
        if not isinstance(data, dict):
            return mapping
        for word, value in data.items():
            if isinstance(value, str):
                mapping[str(word)] = value
            elif isinstance(value, dict):
                category = value.get("category")
                if category:
                    mapping[str(word)] = str(category)
                names = value.get("name")
                if category and isinstance(names, dict):
                    self.category_names.setdefault(str(category), {}).update(
                        {str(k): str(v) for k, v in names.items()}
                    )
        return mapping

    def entries(self, code: str) -> list[WordEntry]:
        if code in self._entries:
            return self._entries[code]
        info = self.languages.get(code)
        if not info:
            self._entries[code] = []
            return []

        category_map = self._load_category_map(info)
        merged: dict[str, WordEntry] = {}

        for relative in info.files:
            path = self._find(relative)
            if not path:
                continue
            words, default_category, pack_categories = self._read_words(path)
            for raw_source, raw_values in words.items():
                source = str(raw_source).strip()
                if not source:
                    continue
                if isinstance(raw_values, str):
                    values = [raw_values]
                elif isinstance(raw_values, list):
                    values = raw_values
                else:
                    continue
                translations: list[str] = []
                seen: set[str] = set()
                for value in values:
                    text = str(value).strip()
                    key = normalize(text)
                    if text and key and key not in seen:
                        seen.add(key)
                        translations.append(text)
                if not translations:
                    continue

                category = (
                    pack_categories.get(source)
                    or category_map.get(source)
                    or default_category
                )
                existing = merged.get(source)
                if existing:
                    known = {normalize(t) for t in existing.translations}
                    for text in translations:
                        if normalize(text) not in known:
                            existing.translations.append(text)
                            known.add(normalize(text))
                    if existing.category == "general" and category != "general":
                        existing.category = category
                else:
                    merged[source] = WordEntry(
                        source=source,
                        translations=translations,
                        category=category,
                        language=code,
                    )

        self._entries[code] = list(merged.values())
        return self._entries[code]

    def language(self, code: str) -> LanguageInfo:
        info = self.languages.get(code)
        if info is not None:
            return info
        return LanguageInfo(
            code=code,
            names={"es": code.upper(), "en": code.upper(), "fr": code.upper()},
            label=code.upper(),
            color="#4F46E5",
            files=[],
        )

    # ----------------------------------------------------------------- indexes
    def reverse_index(self, code: str) -> dict[str, list[str]]:
        if code in self._reverse:
            return self._reverse[code]
        index: dict[str, list[str]] = {}
        for entry in self.entries(code):
            for translation in entry.translations:
                key = normalize(translation)
                if not key:
                    continue
                bucket = index.setdefault(key, [])
                if entry.source not in bucket:
                    bucket.append(entry.source)
        self._reverse[code] = index
        return index

    def reverse_lookup(self, code: str, translation: str) -> list[str]:
        return list(self.reverse_index(code).get(normalize(translation), []))

    def find_entry(self, code: str, source: str) -> WordEntry | None:
        for entry in self.entries(code):
            if entry.source == source:
                return entry
        return None

    # -------------------------------------------------------------- categories
    def categories(self, code: str) -> dict[str, int]:
        if code in self._categories:
            return self._categories[code]
        counts: dict[str, int] = {}
        for entry in self.entries(code):
            counts[entry.category] = counts.get(entry.category, 0) + 1
        self._categories[code] = counts
        return counts

    def category_label(self, category: str, ui_lang: str = "es") -> str:
        names = self.category_names.get(category, {})
        return names.get(ui_lang) or names.get("es") or category.replace("_", " ").title()

    def category_options(
        self, code: str, ui_lang: str, all_label: str, general_label: str
    ) -> list[tuple[str, str]]:
        counts = self.categories(code)
        options: list[tuple[str, str]] = [("all", all_label)]
        for category, count in sorted(
            counts.items(), key=lambda item: (item[0] != "general", item[0])
        ):
            if category == "general":
                label = general_label
            else:
                label = self.category_label(category, ui_lang)
            options.append((category, f"{label} ({count})"))
        return options

    def total(self, code: str) -> int:
        return len(self.entries(code))

    def random_entry(self, code: str) -> WordEntry | None:
        entries = self.entries(code)
        return random.choice(entries) if entries else None
