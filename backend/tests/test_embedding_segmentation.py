from app.Services.embeddings import segment_text


def test_word_segmentation_offsets_use_tokenizer_positions_for_repeated_terms() -> None:
  text = "码头，码头？A+A。"

  segments = segment_text(text, "word")

  assert [
    (segment.text, segment.start_offset, segment.end_offset)
    for segment in segments
  ] == [
    ("码头", 0, 2),
    ("码头", 3, 5),
    ("A", 6, 7),
    ("A", 8, 9),
  ]
  assert all(text[segment.start_offset : segment.end_offset] == segment.text for segment in segments)
