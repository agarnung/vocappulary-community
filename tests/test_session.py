import json
import tempfile
import unittest
from pathlib import Path

from vocapp.session import Session
from vocapp.storage import Storage
from vocapp.vocab import Vocabulary


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        data = self.root / "data"
        data.mkdir()
        registry = {
            "xx": {
                "name": {"es": "Test"},
                "label": "XX",
                "color": "#123456",
                "files": ["palabras_xx.json"],
                "categories": "categories_xx.json",
            }
        }
        (data / "languages.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        (data / "palabras_xx.json").write_text(
            json.dumps(
                {
                    "gato": ["gato"],
                    "perro": ["perro", "can"],
                    "can": ["perro"],
                    "casa": ["casa", "hogar"],
                }
            ),
            encoding="utf-8",
        )
        (data / "categories_xx.json").write_text(
            json.dumps(
                {
                    "gato": "animals",
                    "perro": "animals",
                    "can": "animals",
                    "casa": "home",
                }
            ),
            encoding="utf-8",
        )
        self.vocab = Vocabulary(search_dirs=[self.root])
        self.storage = Storage(base_dir=self.root / "user")
        self.settings = {
            "direction": "to_es",
            "category": "all",
            "practice_mode": "quick",
            "session_length": "all",
            "fuzzy": True,
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_session_flow(self):
        session = Session(
            self.vocab,
            self.storage,
            self.settings,
            "xx",
            entries=self.vocab.entries("xx"),
        )
        self.assertEqual(len(session.questions), 4)

        first = session.current()
        self.assertIsNotNone(first)
        result = session.submit(first.expected[0])
        self.assertEqual(result.status, "correct")
        session.advance()

        second = session.current()
        session.skip()
        session.advance()

        third = session.current()
        session.submit("respuesta incorrecta")
        session.advance()

        summary = session.summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["correct"], 1)
        self.assertEqual(summary["wrong"], 2)
        self.assertEqual(len(summary["missed"]), 2)
        self.assertEqual(self.storage.stats["total_answers"], 3)

    def test_srs_and_stats(self):
        session = Session(
            self.vocab,
            self.storage,
            self.settings,
            "xx",
            entries=self.vocab.entries("xx"),
        )
        question = session.current()
        session.submit(question.expected[0])
        item = self.storage.get_srs("xx", "to_es", question.entry.source)
        self.assertIsNotNone(item)
        self.assertEqual(item["box"], 2)
        self.assertEqual(self.storage.accuracy(), 100.0)

    def test_category_filter_and_length(self):
        settings = dict(self.settings, category="animals", session_length=2)
        session = Session(self.vocab, self.storage, settings, "xx")
        self.assertEqual(len(session.questions), 2)
        self.assertTrue(
            all(q.entry.category == "animals" for q in session.questions)
        )

    def test_session_length(self):
        settings = dict(self.settings, session_length=2)
        session = Session(self.vocab, self.storage, settings, "xx")
        self.assertEqual(len(session.questions), 2)

    def test_hint_usage_is_per_question(self):
        session = Session(
            self.vocab,
            self.storage,
            self.settings,
            "xx",
            entries=[
                self.vocab.find_entry("xx", "gato"),
                self.vocab.find_entry("xx", "casa"),
            ],
        )
        session.mark_hint()
        session.submit("gato")
        session.advance()
        session.submit("casa")
        self.assertTrue(session.records[0].hint_used)
        self.assertFalse(session.records[1].hint_used)

    def test_exact_keeps_streak_and_counts(self):
        session = Session(
            self.vocab,
            self.storage,
            self.settings,
            "xx",
            entries=[self.vocab.find_entry("xx", "gato")],
        )
        question = session.current()
        session.submit(question.expected[0])
        self.assertEqual(session.streak, 1)
        self.assertEqual(self.storage.stats["almost"], 0)
        self.assertEqual(self.storage.accuracy(), 100.0)

    def test_reverse_mode_accepts_any_source_for_translation(self):
        settings = dict(self.settings, direction="to_source")
        session = Session(
            self.vocab,
            self.storage,
            settings,
            "xx",
            entries=[self.vocab.find_entry("xx", "can")],
        )
        question = session.current()
        self.assertEqual(question.prompt, "perro")
        self.assertIn("perro", question.expected)
        self.assertIn("can", question.expected)


if __name__ == "__main__":
    unittest.main()
