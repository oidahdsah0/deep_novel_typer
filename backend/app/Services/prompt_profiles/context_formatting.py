from __future__ import annotations

import json
import re
from html import escape
from typing import Any

from app.Schemas.prompt_context import (
  PromptContextAgentBlock,
  PromptContextBudgetReport,
  PromptContextFocusBlock,
  PromptContextMaterialBlock,
  PromptContextPack,
)


def estimate_text_tokens(value: str) -> int:
  if not value:
    return 0

  cjk_chars = 0
  ascii_chars = 0
  other_chars = 0
  for char in value:
    codepoint = ord(char)
    if (
      0x4E00 <= codepoint <= 0x9FFF
      or 0x3400 <= codepoint <= 0x4DBF
      or 0x3040 <= codepoint <= 0x30FF
      or 0xAC00 <= codepoint <= 0xD7AF
    ):
      cjk_chars += 1
    elif codepoint < 128:
      ascii_chars += 1
    elif not char.isspace():
      other_chars += 1
  return max(1, round(cjk_chars + ascii_chars / 4 + other_chars / 2))


def with_context_budget(pack: PromptContextPack) -> PromptContextPack:
  task_tokens = estimate_text_tokens(pack.task)
  project_tokens = estimate_text_tokens(_json(pack.project))
  focus_tokens = sum(item.token_estimate for item in pack.focus)
  material_tokens = sum(item.token_estimate for item in pack.materials)
  agent_tokens = estimate_text_tokens(_json([item.model_dump() for item in pack.agents]))
  return pack.model_copy(
    update={
      "budget": PromptContextBudgetReport(
        input_tokens=task_tokens
        + project_tokens
        + focus_tokens
        + material_tokens
        + agent_tokens,
        task_tokens=task_tokens,
        project_tokens=project_tokens,
        focus_tokens=focus_tokens,
        material_tokens=material_tokens,
        agent_tokens=agent_tokens,
        truncated_materials=sum(1 for item in pack.materials if item.truncated),
      )
    }
  )


def focus_block(
  *,
  key: str,
  label: str,
  content: str,
  format: str = "plain",
  content_mode: str = "full",
  metadata: dict[str, Any] | None = None,
) -> PromptContextFocusBlock:
  normalized = content or ""
  empty = not normalized.strip()
  return PromptContextFocusBlock(
    key=key,
    label=label,
    content=normalized,
    format=format,  # type: ignore[arg-type]
    content_mode="empty" if empty else content_mode,  # type: ignore[arg-type]
    chars=len(normalized),
    token_estimate=estimate_text_tokens(normalized),
    empty=empty,
    metadata=metadata or {},
  )


def material_block(
  *,
  id: str,
  title: str,
  kind: str,
  source: str,
  content: str,
  format: str,
  chars: int,
  truncated: bool,
) -> PromptContextMaterialBlock:
  empty = not content.strip()
  return PromptContextMaterialBlock(
    id=id,
    title=title,
    kind=kind,  # type: ignore[arg-type]
    source=source,
    content=content,
    format=format,  # type: ignore[arg-type]
    content_mode="empty" if empty else ("truncated" if truncated else "full"),
    chars=chars,
    token_estimate=estimate_text_tokens(content),
    truncated=truncated,
  )


def render_context_pack(pack: PromptContextPack) -> str:
  sections = [
    f'<context_pack version="{pack.version}" request_type="{_attr(pack.request_type)}">',
    _render_text_section("task", pack.task),
    _render_json_section("project", pack.project),
    _render_focus(pack.focus),
    _render_materials(pack.materials),
    _render_agents(pack.agents),
    _render_constraints(pack.constraints),
    "</context_pack>",
  ]
  return "\n\n".join(section for section in sections if section).strip()


def render_material_blocks(blocks: list[PromptContextMaterialBlock]) -> str:
  if not blocks:
    return ""
  return _render_materials(blocks)


def render_agent_blocks(blocks: list[PromptContextAgentBlock]) -> str:
  if not blocks:
    return ""
  return _render_agents(blocks)


def _render_text_section(name: str, content: str) -> str:
  if not content.strip():
    return f'<{name} empty="true"></{name}>'
  return f"<{name}>\n{content.strip()}\n</{name}>"


def _render_json_section(name: str, payload: Any) -> str:
  return f'<{name} format="json">\n{_fenced("json", _json(payload))}\n</{name}>'


def _render_focus(blocks: list[PromptContextFocusBlock]) -> str:
  if not blocks:
    return '<focus empty="true"></focus>'
  return "\n".join(
    [
      "<focus>",
      *[_render_focus_block(block) for block in blocks],
      "</focus>",
    ]
  )


def _render_focus_block(block: PromptContextFocusBlock) -> str:
  attrs = _attrs(
    key=block.key,
    label=block.label,
    format=block.format,
    content_mode=block.content_mode,
    empty=str(block.empty).lower(),
    chars=str(block.chars),
    token_estimate=str(block.token_estimate),
  )
  if block.empty:
    return f"<field {attrs}></field>"
  return (
    f"<field {attrs}>\n"
    f"{_fenced(_fence_lang(block.format), block.content)}\n"
    "</field>"
  )


def _render_materials(blocks: list[PromptContextMaterialBlock]) -> str:
  if not blocks:
    return '<materials empty="true"></materials>'
  return "\n".join(
    [
      "<materials>",
      *[_render_material_block(block) for block in blocks],
      "</materials>",
    ]
  )


def _render_material_block(block: PromptContextMaterialBlock) -> str:
  attrs = _attrs(
    id=block.id,
    title=block.title,
    kind=block.kind,
    source=block.source,
    format=block.format,
    content_mode=block.content_mode,
    truncated=str(block.truncated).lower(),
    chars=str(block.chars),
    token_estimate=str(block.token_estimate),
  )
  if not block.content.strip():
    return f"<material {attrs}></material>"
  return (
    f"<material {attrs}>\n"
    f"{_fenced(_fence_lang(block.format), block.content)}\n"
    "</material>"
  )


def _render_agents(blocks: list[PromptContextAgentBlock]) -> str:
  if not blocks:
    return '<agents empty="true"></agents>'
  return (
    '<agents format="json">\n'
    f"{_fenced('json', _json([block.model_dump() for block in blocks]))}\n"
    "</agents>"
  )


def _render_constraints(constraints: list[str]) -> str:
  if not constraints:
    return ""
  return "<constraints>\n" + "\n".join(f"- {item}" for item in constraints) + "\n</constraints>"


def _fence_lang(format: str) -> str:
  if format == "markdown":
    return "markdown"
  if format == "json":
    return "json"
  return "text"


def _fenced(lang: str, content: str) -> str:
  fence = "`" * (_longest_backtick_run(content) + 1)
  return f"{fence}{lang}\n{content}\n{fence}"


def _longest_backtick_run(content: str) -> int:
  matches = re.findall(r"`+", content)
  return max([3, *(len(match) for match in matches)])


def _json(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2)


def _attrs(**values: str) -> str:
  return " ".join(f'{key}="{_attr(value)}"' for key, value in values.items())


def _attr(value: str) -> str:
  return escape(value, quote=True)
