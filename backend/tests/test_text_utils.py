from app.Utils.ids import slugify
from app.Utils.text import count_words, extract_last_paragraph, tail_text


def test_count_words_handles_cjk_and_latin_text() -> None:
  assert count_words("林澈 found 2 clues") == 5


def test_extract_last_paragraph_skips_blank_lines() -> None:
  assert extract_last_paragraph("第一段\n\n第二段\n") == "第二段"


def test_tail_text_keeps_recent_content() -> None:
  assert tail_text("abcdef", 3) == "def"
  assert tail_text("abcdef", 6) == "abcdef"


def test_tail_text_can_strip_before_truncating() -> None:
  assert tail_text("  abcdef  ", 4, strip=True) == "cdef"


def test_slugify_falls_back_for_non_latin_titles() -> None:
  assert slugify("沉默港湾", fallback_prefix="book").startswith("book-")
