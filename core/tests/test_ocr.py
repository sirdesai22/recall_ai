import unittest
from ocr import clean_text, chunk_text


class TestCleanText(unittest.TestCase):
    def test_filters_short_lines(self):
        assert clean_text("ab\nlong enough line") == "long enough line"

    def test_keeps_lines_of_exactly_four(self):
        assert clean_text("abcd") == "abcd"

    def test_filters_digit_only_lines(self):
        assert clean_text("12345\nreal content here") == "real content here"

    def test_filters_symbol_only_lines(self):
        assert clean_text("!@#$%\nreal content here") == "real content here"

    def test_dedupes_repeated_lines(self):
        assert clean_text("same line here\nsame line here") == "same line here"

    def test_strips_whitespace(self):
        assert clean_text("   padded line of text   ") == "padded line of text"

    def test_empty_input(self):
        assert clean_text("") == ""


class TestChunkText(unittest.TestCase):
    def test_short_text_single_chunk(self):
        assert chunk_text("one two three") == ["one two three"]

    def test_empty_text_returns_one_empty_chunk(self):
        # documented behaviour: caller is responsible for skipping empty text
        assert chunk_text("") == [""]

    def test_exact_window_single_chunk(self):
        words = [f"w{i}" for i in range(150)]
        chunks = chunk_text(" ".join(words))
        assert len(chunks) == 1

    def test_long_text_chunks_overlap(self):
        words = [f"w{i}" for i in range(400)]
        chunks = chunk_text(" ".join(words), window=150, overlap=30)
        # step = window - overlap
        self.assertGreater(len(chunks), 1)
        first = chunks[0].split()
        second = chunks[1].split()
        overlap_words = first[-30:]
        self.assertEqual(overlap_words, second[:30])

    def test_chunks_cover_all_words(self):
        words = [f"w{i}" for i in range(400)]
        chunks = chunk_text(" ".join(words))
        self.assertEqual(chunks[0].split()[0], "w0")
        self.assertEqual(chunks[-1].split()[-1], "w399")


if __name__ == "__main__":
    unittest.main()
