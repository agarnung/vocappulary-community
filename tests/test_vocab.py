import json
import tempfile
import unittest
from pathlib import Path

from vocapp.vocab import Vocabulary


class VocabularyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        data = self.root / "data"
        (data / "packs").mkdir(parents=True)

        registry = {
            "xx": {
                "name": {"es": "Test", "en": "Test", "fr": "Test"},
                "label": "XX",
                "color": "#123456",
                "files": ["palabras_xx.json", "packs/xx_pack.json"],
                "categories": "categories_xx.json",
            }
        }
        (data / "languages.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        (data / "palabras_xx.json").write_text(
            json.dumps({"gato": "gato", "perro": ["perro", "can"]}),
            encoding="utf-8",
        )
        (data / "categories_xx.json").write_text(
            json.dumps({"gato": "animals"}), encoding="utf-8"
        )
        pack = {
            "meta": {"name": {"es": "Pack", "en": "Pack"}},
            "category_names": {"food": {"es": "Comida", "en": "Food"}},
            "categories": {"pan": "food", "gato": "animals"},
            "words": {"pan": ["pan"], "gato": ["minino"]},
        }
        (data / "packs" / "xx_pack.json").write_text(
            json.dumps(pack), encoding="utf-8"
        )
        self.vocab = Vocabulary(search_dirs=[self.root])

    def tearDown(self):
        self.temp.cleanup()

    def test_registry(self):
        self.assertIn("xx", self.vocab.languages)
        self.assertEqual(self.vocab.languages["xx"].name("es"), "Test")

    def test_string_values_become_lists(self):
        entries = {entry.source: entry for entry in self.vocab.entries("xx")}
        self.assertEqual(entries["gato"].translations, ["gato", "minino"])
        self.assertEqual(entries["perro"].translations, ["perro", "can"])

    def test_categories(self):
        categories = self.vocab.categories("xx")
        self.assertEqual(categories["animals"], 1)
        self.assertEqual(categories["food"], 1)

    def test_pack_category_names(self):
        self.vocab.entries("xx")
        self.assertEqual(self.vocab.category_label("food", "es"), "Comida")

    def test_reverse_lookup(self):
        self.assertIn("gato", self.vocab.reverse_lookup("xx", "gato"))

    def test_total(self):
        self.assertEqual(self.vocab.total("xx"), 3)

    def test_category_options(self):
        options = self.vocab.category_options("xx", "es", "Todas", "General")
        self.assertEqual(options[0], ("all", "Todas"))
        self.assertIn(("animals", "Animales (1)"), options)
        self.assertIn(("food", "Comida (1)"), options)

    def test_reverse_index_multiple_sources(self):
        self.vocab.entries("xx")
        index = self.vocab.reverse_index("xx")
        self.assertIn("gato", index)
        self.assertIn("gato", index["minino"])


if __name__ == "__main__":
    unittest.main()
