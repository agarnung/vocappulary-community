import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from vocapp.storage import Storage
from vocapp.vocab import WordEntry


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.storage = Storage(base_dir=self.base)
        self.entries = [
            WordEntry("gato", ["gato"], "animals", "xx"),
            WordEntry("perro", ["perro", "can"], "animals", "xx"),
            WordEntry("casa", ["casa"], "home", "xx"),
        ]

    def tearDown(self):
        self.temp.cleanup()

    def test_defaults_and_roundtrip(self):
        self.assertEqual(self.storage.settings["ui_lang"], "es")
        self.storage.settings["ui_lang"] = "en"
        self.storage.save_settings()
        reloaded = Storage(base_dir=self.base)
        self.assertEqual(reloaded.settings["ui_lang"], "en")

    def test_record_answer_updates_stats(self):
        self.storage.record_answer("xx", "to_es", "gato", "correct", "gato")
        self.assertEqual(self.storage.stats["total_answers"], 1)
        self.assertEqual(self.storage.stats["correct"], 1)
        self.assertEqual(self.storage.stats["current_streak"], 1)
        self.assertEqual(self.storage.daily_answers(), 1)
        self.assertEqual(self.storage.accuracy(), 100.0)
        item = self.storage.get_srs("xx", "to_es", "gato")
        self.assertEqual(item["box"], 2)

    def test_wrong_resets_streak_and_box(self):
        self.storage.record_answer("xx", "to_es", "gato", "correct")
        self.storage.record_answer("xx", "to_es", "gato", "wrong")
        self.assertEqual(self.storage.stats["current_streak"], 0)
        self.assertEqual(self.storage.stats["best_streak"], 1)
        item = self.storage.get_srs("xx", "to_es", "gato")
        self.assertEqual(item["box"], 1)

    def test_due_and_learned_counts(self):
        self.assertEqual(
            self.storage.due_count(self.entries, "xx", "to_es"), 3
        )
        self.assertEqual(
            self.storage.learned_count(self.entries, "xx", "to_es"), 0
        )
        self.assertEqual(
            self.storage.new_count(self.entries, "xx", "to_es"), 3
        )
        for _ in range(3):
            self.storage.record_answer(
                "xx", "to_es", "gato", "correct", "gato"
            )
        self.assertEqual(
            self.storage.learned_count(self.entries, "xx", "to_es"), 1
        )
        self.assertEqual(
            self.storage.new_count(self.entries, "xx", "to_es"), 2
        )

    def test_activity_and_hardest(self):
        self.storage.record_answer("xx", "to_es", "gato", "wrong", "gato")
        self.storage.record_answer("xx", "to_es", "perro", "wrong", "perro")
        self.storage.record_answer("xx", "to_es", "perro", "wrong", "perro")
        activity = self.storage.activity(7)
        self.assertEqual(len(activity), 7)
        self.assertEqual(activity[-1][0], date.today().isoformat())
        self.assertEqual(activity[-1][1], 3)
        hardest = self.storage.hardest_words(5)
        self.assertEqual(hardest[0][1], "perro")
        self.assertEqual(hardest[0][2]["wrong"], 2)

    def test_reset_progress(self):
        self.storage.record_answer("xx", "to_es", "gato", "correct", "gato")
        self.storage.reset_progress()
        self.assertEqual(self.storage.stats["total_answers"], 0)
        self.assertEqual(self.storage.srs, {})

    def test_corrupted_files_fall_back_to_defaults(self):
        (self.base / "stats.json").write_text("{bad json", encoding="utf-8")
        (self.base / "srs.json").write_text("[]", encoding="utf-8")
        (self.base / "settings.json").write_text("[]", encoding="utf-8")
        storage = Storage(base_dir=self.base)
        self.assertEqual(storage.stats["total_answers"], 0)
        self.assertEqual(storage.srs, {})
        self.assertEqual(storage.settings["ui_lang"], "es")

    def test_invalid_nested_types_are_sanitized(self):
        (self.base / "stats.json").write_text(
            json.dumps(
                {
                    "daily": [],
                    "per_language": {"xx": "bad"},
                    "words": {"xx::gato": "bad"},
                    "total_answers": "many",
                }
            ),
            encoding="utf-8",
        )
        (self.base / "srs.json").write_text(
            json.dumps({"xx:to_es:gato": "bad"}), encoding="utf-8"
        )
        storage = Storage(base_dir=self.base)
        self.assertEqual(storage.stats["daily"], {})
        self.assertEqual(storage.stats["per_language"]["xx"]["answers"], 0)
        self.assertEqual(storage.stats["words"], {})
        self.assertEqual(storage.stats["total_answers"], 0)
        self.assertEqual(storage.srs, {})


if __name__ == "__main__":
    unittest.main()
