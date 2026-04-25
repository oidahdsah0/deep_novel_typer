import pytest

from app.Services.structured_outputs import StructuredOutputContext, validate_structured_output
from app.Utils.errors import LLMResponseFormatError


def test_text_output_requires_non_empty_text() -> None:
  assert validate_structured_output(
    "generate_next_paragraph", {"text": "  码头灯亮了。  "}
  ) == {"text": "码头灯亮了。"}
  assert validate_structured_output(
    "quick_generate_next_paragraph", {"text": "  他停了一下。  "}
  ) == {"text": "他停了一下。"}

  for payload in ({}, {"text": ""}, {"text": "   "}, {"text": 123}, {"text": "ok", "x": 1}):
    with pytest.raises(LLMResponseFormatError):
      validate_structured_output("generate_next_paragraph", payload)


def test_chapter_blueprint_output_requires_points() -> None:
  assert validate_structured_output(
    "generate_chapter_blueprint",
    {"points": ["  开场先给出目标。  ", "中段释放线索。\n"]},
  ) == {"points": ["开场先给出目标。", "中段释放线索。"]}

  for payload in ({}, {"points": ""}, {"points": []}, {"points": ["   "]}, {"points": ["ok"], "x": 1}):
    with pytest.raises(LLMResponseFormatError):
      validate_structured_output("generate_chapter_blueprint", payload)


def test_perspective_output_validates_card_schema_and_ids() -> None:
  context = StructuredOutputContext(valid_perspective_ids=frozenset({"pace-editor"}))
  assert validate_structured_output(
    "perspective_suggestion",
    {
      "cards": [
        {
          "perspective_id": "pace-editor",
          "title": "  节奏清楚  ",
          "body": "  可以补一个动作。 ",
          "severity": "focus",
        }
      ]
    },
    context,
  ) == {
    "cards": [
      {
        "perspective_id": "pace-editor",
        "title": "节奏清楚",
        "body": "可以补一个动作。",
        "severity": "focus",
      }
    ]
  }

  invalid_payloads = [
    {},
    {"cards": "bad"},
    {"cards": [{"perspective_id": "unknown", "title": "t", "body": "b", "severity": "focus"}]},
    {"cards": [{"perspective_id": "pace-editor", "title": "t", "body": "b", "severity": "bad"}]},
    {"cards": [{"perspective_id": "pace-editor", "title": "", "body": "b", "severity": "focus"}]},
    {
      "cards": [
        {"perspective_id": "pace-editor", "title": "t", "body": "b", "severity": "focus"},
        {"perspective_id": "pace-editor", "title": "t2", "body": "b2", "severity": "calm"},
      ]
    },
    {
      "cards": [
        {
          "perspective_id": "pace-editor",
          "title": "t",
          "body": "b",
          "severity": "focus",
          "extra": "no",
        }
      ]
    },
  ]
  for payload in invalid_payloads:
    with pytest.raises(LLMResponseFormatError):
      validate_structured_output("perspective_suggestion", payload, context)
