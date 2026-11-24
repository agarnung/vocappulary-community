import unittest

from vocapp.validation import normalize
from vocapp.vocab import Vocabulary


class DataIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vocab = Vocabulary()

    def test_languages_present(self):
        self.assertEqual(set(self.vocab.languages), {"en"})

    def test_minimum_vocabulary(self):
        for code in self.vocab.languages:
            self.assertGreater(self.vocab.total(code), 100)

    def test_single_word_entries(self):
        for code in self.vocab.languages:
            for entry in self.vocab.entries(code):
                self.assertNotIn(" ", entry.source)
                for translation in entry.translations:
                    self.assertNotIn(" ", translation)

    def test_translations_are_clean(self):
        for code in self.vocab.languages:
            for entry in self.vocab.entries(code):
                self.assertTrue(entry.source.strip())
                self.assertTrue(entry.translations)
                seen = set()
                for translation in entry.translations:
                    key = normalize(translation)
                    self.assertTrue(key)
                    self.assertNotIn(key, seen)
                    seen.add(key)

    def test_categories_present(self):
        for code in self.vocab.languages:
            self.assertGreaterEqual(len(self.vocab.categories(code)), 5)

    def test_reverse_index(self):
        for code in self.vocab.languages:
            self.assertTrue(self.vocab.reverse_lookup(code, "gato"))

    def test_category_names(self):
        for code in self.vocab.languages:
            for category in self.vocab.categories(code):
                if category == "general":
                    continue
                names = self.vocab.category_names.get(category, {})
                self.assertTrue(names, f"[{code}] categoría sin nombre: {category}")
                self.assertTrue(names.get("es"), f"[{code}] categoría sin nombre en español: {category}")

    def test_category_counts_match(self):
        for code in self.vocab.languages:
            categories = self.vocab.categories(code)
            self.assertEqual(sum(categories.values()), self.vocab.total(code))

    def test_unique_sources(self):
        for code in self.vocab.languages:
            sources = [entry.source for entry in self.vocab.entries(code)]
            self.assertEqual(len(sources), len(set(sources)))

    def test_reverse_index_has_no_duplicates(self):
        for code in self.vocab.languages:
            for sources in self.vocab.reverse_index(code).values():
                self.assertEqual(len(sources), len(set(sources)))

    def test_packs_add_words(self):
        for code in self.vocab.languages:
            self.assertTrue(
                any(
                    entry.category != "general"
                    for entry in self.vocab.entries(code)
                )
            )


if __name__ == "__main__":
    unittest.main()
