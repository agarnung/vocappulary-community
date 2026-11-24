import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from vocapp.app import App
from vocapp.screens import GameScreen, HomeScreen, ResultsScreen, SettingsScreen, StatsScreen
from vocapp.storage import Storage
from vocapp.widgets import RoundedButton


DISPLAY = os.environ.get("DISPLAY")
HAS_DISPLAY = bool(DISPLAY) or sys.platform in ("win32", "darwin")


@unittest.skipUnless(HAS_DISPLAY, "requiere un entorno gráfico")
class UISmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = App(storage=Storage(base_dir=Path(self.temp.name)))
        self.app.root.withdraw()
        self.app.settings["auto_advance"] = False
        self.app.settings["session_length"] = 3
        self.app.settings["category"] = "all"
        self.app.settings["direction"] = "to_es"
        self.app.settings["theme"] = "light"
        self.app.settings["ui_lang"] = "es"
        self.app.storage.save_settings(self.app.settings)
        self.pump(3)

    def tearDown(self):
        try:
            self.app.root.destroy()
        except Exception:
            pass
        self.temp.cleanup()

    def pump(self, count=3):
        for _ in range(count):
            self.app.root.update()
            time.sleep(0.01)

    def answer_current(self, correct=True):
        screen = self.app.current
        question = screen.session.current()
        self.assertIsNotNone(question)
        answer = question.expected[0] if correct else "zzzzzzzz"
        screen.entry.entry.delete(0, "end")
        screen.entry.entry.insert(0, answer)
        screen.entry._placeholder_active = False
        screen.submit()
        self.pump()

    def test_invalid_settings_are_sanitized(self):
        self.app.storage.settings.update(
            {
                "source_lang": "zz",
                "direction": "bad",
                "practice_mode": "bad",
                "session_length": 999,
                "category": "bad",
                "ui_lang": "de",
                "theme": "neon",
                "daily_goal": 999,
            }
        )
        self.app.storage.save_settings()
        self.app.root.destroy()
        self.app = App(storage=Storage(base_dir=Path(self.temp.name)))
        self.app.root.withdraw()
        self.pump()
        self.assertEqual(self.app.settings["source_lang"], "en")
        self.assertEqual(self.app.settings["direction"], "to_es")
        self.assertEqual(self.app.settings["practice_mode"], "learn")
        self.assertEqual(self.app.settings["session_length"], 10)
        self.assertEqual(self.app.settings["category"], "all")
        self.assertEqual(self.app.settings["ui_lang"], "es")
        self.assertEqual(self.app.settings["theme"], "light")
        self.assertEqual(self.app.settings["daily_goal"], 20)

    def test_pro_cta_visible_in_header(self):
        self.app.show_home()
        self.pump()
        buttons = []

        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child, RoundedButton):
                    buttons.append(child)
                walk(child)

        walk(self.app.current)
        self.assertIn(self.app.t("go_pro"), [button.text for button in buttons])

    def test_hint_and_skip(self):
        self.app.settings["session_length"] = 2
        self.app.start_session(entries=self.app.vocab.entries("en")[:2])
        self.pump()
        screen = self.app.current
        screen.hint()
        self.assertTrue(screen.hint_label.cget("text"))
        self.assertEqual(screen.session.hints, 1)
        screen.skip()
        self.pump()
        self.assertEqual(screen.session.records[-1].status, "wrong")
        self.assertEqual(screen.session.records[-1].reason, "skipped")
        self.assertTrue(screen.session.records[-1].hint_used)
        screen.continue_()
        self.pump()
        self.answer_current(True)
        self.app.current.continue_()
        self.pump()
        self.assertIsInstance(self.app.current, ResultsScreen)
        self.assertEqual(self.app.last_summary["wrong"], 1)
        self.assertEqual(self.app.last_summary["correct"], 1)

    def test_navigation_and_session(self):
        self.assertIsInstance(self.app.current, HomeScreen)

        self.app.show_settings()
        self.pump()
        self.assertIsInstance(self.app.current, SettingsScreen)

        self.app.show_stats()
        self.pump()
        self.assertIsInstance(self.app.current, StatsScreen)

        self.app.show_home()
        self.pump()
        self.app.start_session(entries=self.app.vocab.entries("en")[:3])
        self.pump()
        self.assertIsInstance(self.app.current, GameScreen)

        self.answer_current(True)
        self.app.current.continue_()
        self.pump()
        self.answer_current(False)
        self.app.current.continue_()
        self.pump()
        self.answer_current(True)
        self.app.current.continue_()
        self.pump()

        self.assertIsInstance(self.app.current, ResultsScreen)
        self.assertIsNotNone(self.app.last_summary)
        self.assertEqual(self.app.last_summary["total"], 3)
        self.assertEqual(self.app.last_summary["correct"], 2)
        self.assertEqual(self.app.last_summary["wrong"], 1)
        self.assertEqual(len(self.app.last_summary["missed"]), 1)

        self.app.current._repeat_missed()
        self.pump()
        self.assertIsInstance(self.app.current, GameScreen)
        self.assertEqual(len(self.app.current.session.questions), 1)
        self.answer_current(True)
        self.app.current.continue_()
        self.pump()
        self.assertIsInstance(self.app.current, ResultsScreen)

        self.app.show_home()
        self.pump()
        self.app.toggle_theme()
        self.pump()
        self.assertIsInstance(self.app.current, HomeScreen)
        self.assertEqual(self.app.settings["theme"], "light")

        self.app.set_ui_lang("en")
        self.pump()
        self.assertIsInstance(self.app.current, SettingsScreen)
        self.assertEqual(self.app.settings["ui_lang"], "en")

        self.app.set_ui_lang("fr")
        self.pump()
        self.assertEqual(self.app.settings["ui_lang"], "fr")

        self.app.set_ui_lang("es")
        self.pump()
        self.assertEqual(self.app.settings["ui_lang"], "es")

        self.app.show_home()
        self.pump()
        self.assertIsInstance(self.app.current, HomeScreen)


if __name__ == "__main__":
    unittest.main()
