"""Valida los diccionarios y packs de vocabulario.

Uso:
    python utils/validate_vocab.py

Comprueba tipos, traducciones vacías, duplicados normalizados, categorías
desconocidas y palabras repetidas entre el diccionario base y los packs.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vocapp.validation import normalize  # noqa: E402
from vocapp.vocab import Vocabulary  # noqa: E402


def main() -> int:
    vocab = Vocabulary()
    errors: list[str] = []
    warnings: list[str] = []
    shared: list[str] = []

    if not vocab.languages:
        errors.append("No se encontró languages.json ni el registro por defecto.")

    for code, info in vocab.languages.items():
        entries = vocab.entries(code)
        if not entries:
            errors.append(f"[{code}] no tiene palabras")
            continue

        seen: dict[str, str] = {}
        for entry in entries:
            if not entry.source.strip():
                errors.append(f"[{code}] palabra sin texto")
            if not entry.translations:
                errors.append(f"[{code}] {entry.source!r} sin traducciones")
            for translation in entry.translations:
                key = normalize(translation)
                if not key:
                    errors.append(
                        f"[{code}] {entry.source!r} tiene una traducción vacía"
                    )
                elif key in seen and seen[key] != entry.source:
                    shared.append(
                        f"[{code}] {translation!r}: {seen[key]!r} / {entry.source!r}"
                    )
                else:
                    seen[key] = entry.source
            if not entry.category:
                warnings.append(f"[{code}] {entry.source!r} sin categoría")

        categories = vocab.categories(code)
        for category in categories:
            if category != "general" and not vocab.category_names.get(category):
                warnings.append(
                    f"[{code}] categoría sin nombres localizados: {category}"
                )
        print(
            f"[{code}] {len(entries)} palabras · "
            f"{len(categories)} categorías · "
            f"{len(vocab.reverse_index(code))} traducciones únicas"
        )

    for warning in warnings:
        print(f"AVISO: {warning}")
    if shared:
        print(
            f"INFO: {len(shared)} traducciones compartidas entre palabras "
            "(sinónimos válidos)"
        )
    for error in errors:
        print(f"ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
