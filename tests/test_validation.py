import unittest

from vocapp.validation import compare_answer, normalize, split_expected


class ValidationTests(unittest.TestCase):
    def test_exact(self):
        result = compare_answer("gato", ["gato"])
        self.assertEqual(result.status, "correct")

    def test_case_and_spaces(self):
        result = compare_answer("  GATO  ", ["gato"])
        self.assertEqual(result.status, "correct")

    def test_accent(self):
        result = compare_answer("cancion", ["canción"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "accent")

    def test_strict_mode_rejects_accent(self):
        result = compare_answer("cancion", ["canción"], tolerant=False)
        self.assertEqual(result.status, "wrong")

    def test_article(self):
        result = compare_answer("el gato", ["gato"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "article")

    def test_plural(self):
        result = compare_answer("gatos", ["gato"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "plural")

    def test_typo(self):
        result = compare_answer("gata", ["gato"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "typo")

    def test_synonyms(self):
        result = compare_answer("hogar", ["casa", "hogar", "vivienda"])
        self.assertEqual(result.status, "correct")
        self.assertEqual(result.expected, "hogar")

    def test_alternatives(self):
        result = compare_answer("automóvil", ["coche/automóvil"])
        self.assertEqual(result.status, "correct")

    def test_english_to(self):
        result = compare_answer("run", ["to run"])
        self.assertEqual(result.status, "correct")

    def test_wrong(self):
        result = compare_answer("perro", ["gato"])
        self.assertEqual(result.status, "wrong")

    def test_short_words_are_not_fuzzy(self):
        result = compare_answer("pen", ["pan"])
        self.assertEqual(result.status, "wrong")

    def test_empty(self):
        result = compare_answer("", ["gato"])
        self.assertEqual(result.status, "wrong")
        self.assertEqual(result.reason, "empty")

    def test_split_expected(self):
        self.assertEqual(
            split_expected(["casa/hogar", "vivienda; morada"]),
            ["casa", "hogar", "vivienda", "morada"],
        )

    def test_normalize(self):
        self.assertEqual(normalize("  El   Gato!  "), "gato")

    def test_parentheses(self):
        result = compare_answer("coche", ["coche (automóvil)"])
        self.assertEqual(result.status, "correct")

    def test_multiword_typo(self):
        result = compare_answer("primer ministra", ["primer ministro"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "typo")

    def test_elision(self):
        result = compare_answer("eau", ["l'eau"])
        self.assertEqual(result.status, "correct")

    def test_punctuation(self):
        result = compare_answer("gato", ["gato,"])
        self.assertEqual(result.status, "correct")

    def test_plural_es(self):
        result = compare_answer("casas", ["casa"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "plural")

    def test_leading_article_both_sides(self):
        result = compare_answer("casa", ["la casa"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "article")

    def test_pipe_alternatives(self):
        result = compare_answer("perro", ["gato|perro"])
        self.assertEqual(result.status, "correct")

    def test_short_accent(self):
        result = compare_answer("pan", ["pán"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "accent")

    def test_long_typo(self):
        result = compare_answer("extraordinari", ["extraordinario"])
        self.assertEqual(result.status, "almost")
        self.assertEqual(result.reason, "typo")

    def test_no_expected(self):
        result = compare_answer("gato", [])
        self.assertEqual(result.status, "wrong")
        self.assertEqual(result.reason, "no_expected")


if __name__ == "__main__":
    unittest.main()
