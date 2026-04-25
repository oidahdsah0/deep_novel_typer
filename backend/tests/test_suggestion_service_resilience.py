import pytest

from app.Schemas.suggestions import SuggestionCard, SuggestionSeverity
from app.Services.suggestion_service import SuggestionService


@pytest.mark.asyncio
async def test_suggest_for_paragraph_keeps_successful_perspective_when_one_fails() -> None:
  service = SuggestionService.__new__(SuggestionService)

  async def list_enabled_perspective_ids(_project_id: str) -> list[str]:
    return ["ok", "fail"]

  async def suggest_for_perspective(
    _project_id: str,
    _chapter_id: str,
    _paragraph: str,
    perspective_id: str,
  ) -> list[SuggestionCard]:
    if perspective_id == "fail":
      raise RuntimeError("provider unavailable")
    return [
      SuggestionCard(
        id="suggestion-ok",
        perspective_id="ok",
        perspective_name="OK",
        title="保留成功结果",
        body="失败视角不应丢掉这条建议。",
        severity=SuggestionSeverity.calm,
      )
    ]

  service.list_enabled_perspective_ids = list_enabled_perspective_ids  # type: ignore[method-assign]
  service.suggest_for_perspective = suggest_for_perspective  # type: ignore[method-assign]

  suggestions = await service.suggest_for_paragraph(
    "project-1",
    "chapter-1",
    "有内容的段落。",
  )

  assert [suggestion.id for suggestion in suggestions] == ["suggestion-ok"]
