import re
import unittest
from pathlib import Path

from vocapp.i18n import I18n, LANGUAGES, STRINGS
from vocapp.theme import PALETTES


class I18nTests(unittest.TestCase):
    def test_all_languages_share_keys(self):
        base = set(STRINGS["es"])
        for code in LANGUAGES:
            self.assertEqual(set(STRINGS[code]), base)

    def test_used_keys_exist(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path("vocapp").glob("*.py")
            if path.name != "i18n.py"
        )
        keys = set(
            re.findall(r"(?:self\.)?\bt\(\s*['\"]([a-zA-Z0-9_]+)['\"]", source)
        )
        keys -= set(PALETTES["light"])
        keys.discard("feedback_")
        keys |= {
            "feedback_accent",
            "feedback_typo",
            "feedback_plural",
            "feedback_article",
        }
        for code in LANGUAGES:
            missing = sorted(key for key in keys if key not in STRINGS[code])
            self.assertEqual(missing, [], f"Faltan claves en {code}")

    def test_fallback_language(self):
        i18n = I18n("xx")
        self.assertEqual(i18n.lang, "es")
        self.assertEqual(i18n.t("start"), "Comenzar sesión")

    def test_unknown_key(self):
        self.assertEqual(I18n("es").t("__missing__"), "__missing__")

    def test_formatting(self):
        self.assertEqual(I18n("es").t("streak_days", n=3), "3 días")
        self.assertEqual(I18n("en").t("streak_days", n=3), "3 days")

    def test_language_name(self):
        self.assertEqual(I18n("es").language_name("fr"), "Français")


if __name__ == "__main__":
    unittest.main()
