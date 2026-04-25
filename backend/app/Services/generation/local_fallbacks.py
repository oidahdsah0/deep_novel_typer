from __future__ import annotations

from app.Schemas.common import DraftGenerationAction
from app.Utils.errors import LLMResponseFormatError
from app.Utils.text import extract_last_paragraph


def local_draft(
  action: DraftGenerationAction,
  chapter_content: str,
  previous_paragraph: str = "",
  cursor_index: int | None = None,
) -> str:
  last = previous_paragraph.strip()
  if not last and cursor_index is None:
    last = extract_last_paragraph(chapter_content)
  if action == "next_section":
    return (
      "他停在原地，把刚才发生的一切重新在心里排了一遍。线索没有变多，"
      "只是每一个细节都比刚才更沉了一点。"
    )
  if last:
    return f"{last} 这一次，他没有立刻回答，只是顺着那一点异常继续往前。"
  return "他停了片刻，像是在等一个还没有出现的答案。"


def local_polish(selected_text: str) -> str:
  lines = [" ".join(line.strip().split()) for line in selected_text.strip().splitlines()]
  return "\n".join(line for line in lines if line) or selected_text.strip()


def local_blueprint_points(chapter_title: str, prompt: str = "") -> list[str]:
  title = chapter_title.strip() or "本章"
  prompt_hint = f"；铺设要求：{prompt.strip()}" if prompt.strip() else ""
  return [
    f"{title}先明确一个可见的章节目标，让主角行动有具体方向{prompt_hint}。",
    "开场用地点、动作或道具落住画面，再释放第一处冲突。",
    "中段安排一处信息递进或反差，让读者知道本章不会原地踏步。",
    "结尾预留一个能承接后文的钩子，避免把解释一次性说完。",
  ]


def require_blueprint_points(payload: dict[str, object], *, request_type: str) -> list[str]:
  value = payload.get("points")
  if not isinstance(value, list):
    raise LLMResponseFormatError(f"LLM response for {request_type} must contain points")
  points = [" ".join(item.strip().split()) for item in value if isinstance(item, str)]
  points = [item for item in points if item]
  if not points:
    raise LLMResponseFormatError(
      f"LLM response for {request_type} must contain non-empty points"
    )
  return points


def local_document_continuation(document_content: str) -> str:
  if document_content.strip():
    return "## 后续补充\n\n- 这里可以继续补充与当前资料相关的设定、线索或备注。"
  return "# 新资料\n\n- 这里可以记录可复用的设定、线索或备注。"
