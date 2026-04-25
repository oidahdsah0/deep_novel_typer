from __future__ import annotations

from app.Schemas.common import PromptRequestType
from app.Services.structured_outputs import structured_output_contract


def output_contract(request_type: PromptRequestType) -> str:
  return structured_output_contract(request_type)


def normalize_output_contract(request_type: PromptRequestType, contract: str | None) -> str:
  value = (contract or "").strip()
  if request_type == "chat_about_work" and _looks_like_structured_json_contract(value):
    return output_contract(request_type)
  return value or output_contract(request_type)


def normalize_prompt_template(request_type: PromptRequestType, template: str) -> str:
  replacements = {
    "只返回合法 JSON object，不要返回 Markdown，不要解释工作过程，不要在 JSON 前后添加任何文字。": "输出结构由系统强制契约控制，建议内容要具体、温和、可执行。",
    "只返回合法 JSON object。": "输出结构由系统强制契约控制。",
    "只输出可直接替换选区的中文小说文本。": "润色结果应放入最终 JSON 的 text 字段；text 字段里只保留可直接替换选区的中文小说文本。",
    "只输出可直接粘贴进正文的中文小说文本。": "续写结果应放入最终 JSON 的 text 字段；text 字段里只保留可直接插入正文光标位置的中文小说文本。",
    "不要输出标题、解释、项目符号、分析过程或 JSON。": "不要在 text 字段里加入标题、解释、项目符号或分析过程。",
    "不要输出标题、解释、项目符号、分析过程或 JSON": "不要在 text 字段里加入标题、解释、项目符号或分析过程",
    "不要输出标题、解释、项目符号或分析过程。": "不要在 text 字段里加入标题、解释、项目符号或分析过程。",
    "只输出润色后的文本。": "最终 JSON 的 text 字段只包含润色后的文本。",
    "不要解释修改理由，只输出润色后的文本。": "不要解释修改理由；最终 JSON 的 text 字段只包含润色后的文本。",
  }
  normalized = template
  for old, new in replacements.items():
    normalized = normalized.replace(old, new)

  if request_type == "perspective_suggestion":
    return normalized

  return normalized.replace(
    "不输出分析、不输出标题、不解释创作意图。",
    "text 字段里不包含分析、标题或创作意图解释。",
  )


def _looks_like_structured_json_contract(value: str) -> bool:
  lowered = value.lower()
  return (
    "json object" in lowered
    or "response_format" in lowered
    or "顶层只能包含 text" in value
    or "最终响应必须只返回合法 json" in lowered
  )
