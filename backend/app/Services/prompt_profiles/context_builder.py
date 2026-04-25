from __future__ import annotations

import json
from typing import Any

from app.Schemas.common import PromptRequestType
from app.Schemas.perspectives import Perspective
from app.Schemas.prompt_context import (
  PromptContextAgentBlock,
  PromptContextMaterialBlock,
  PromptContextPack,
)
from app.Services.project_service import ProjectService
from app.Services.prompt_profiles.context_formatting import focus_block, with_context_budget
from app.Services.prompt_profiles.context_focus import (
  chapter_synopsis_blocks,
  document_chapter_context_blocks,
)


class PromptContextBuilder:
  def __init__(self, project_service: ProjectService) -> None:
    self._project_service = project_service

  async def build(
    self,
    *,
    project_id: str,
    request_type: PromptRequestType,
    runtime_input: dict[str, object],
    materials: list[PromptContextMaterialBlock],
  ) -> PromptContextPack:
    project = await self._project_service.get_manifest(project_id)
    pack = PromptContextPack(
      request_type=request_type,
      project_id=project_id,
      task=_task_for_request(request_type),
      project={
        "title": project.title,
        "subtitle": project.subtitle,
        "genre": project.genre,
        "status": project.status,
        "description": project.description,
      },
      focus=_focus_for_request(request_type, runtime_input),
      materials=materials,
      agents=_agents_for_request(request_type, runtime_input),
      constraints=_constraints_for_request(request_type),
    )
    return with_context_budget(pack)


def _task_for_request(request_type: PromptRequestType) -> str:
  return {
    "perspective_suggestion": (
      "为每个启用视角生成一张简短、具体、可执行的建议卡片；"
      "不要改写或续写正文；没有明显问题也给一个轻量建议。"
    ),
    "polish_selection": (
      "润色用户选中的小说正文，只返回可直接替换选区的文本，"
      "不要改变事实、人物关系、叙事视角、时态和段落边界。"
    ),
    "generate_next_paragraph": (
      "基于正文光标前后的段落边界、写作方式和素材，"
      "生成一段可直接插入光标位置的中文小说文本。"
    ),
    "quick_generate_next_paragraph": (
      "基于正文光标前后的段落边界和素材，"
      "生成一段短而顺滑、可直接插入光标位置的中文小说文本。"
    ),
    "generate_next_section": (
      "基于正文光标前后的段落边界、写作方式和素材，"
      "生成一个可直接插入光标位置的中文小说小节。"
    ),
    "generate_chapter_blueprint": (
      "为当前章节正文光标位置生成基础写作铺设要点；不要续写正文。"
    ),
    "polish_document_selection": (
      "润色用户选中的 Markdown 资料片段，"
      "保留事实边界、资料层级和原有格式。"
    ),
    "generate_document_continuation": (
      "基于当前资料、生成提示和素材，"
      "生成可直接追加到资料末尾的 Markdown 片段。"
    ),
    "chat_about_work": (
      "围绕当前小说项目进行流式自由文本对话，"
      "参考项目、章节和资料上下文回答用户问题。"
    ),
  }.get(request_type, f"执行 {request_type} 请求。")


def _focus_for_request(request_type: PromptRequestType, runtime_input: dict[str, object]):
  if request_type == "perspective_suggestion":
    return [
      focus_block(
        key="chapter_title",
        label="章节标题",
        content=_text(runtime_input.get("chapter_title")),
      ),
      *chapter_synopsis_blocks(runtime_input),
      focus_block(
        key="current_paragraph",
        label="当前段落",
        content=_text(runtime_input.get("current_paragraph")),
      ),
      focus_block(
        key="chapter_excerpt",
        label="当前章节末尾摘录",
        content=_text(runtime_input.get("current_chapter")),
        content_mode="tail",
      ),
    ]

  if request_type == "polish_selection":
    blocks = [
      focus_block(
        key="chapter_title",
        label="章节标题",
        content=_text(runtime_input.get("chapter_title")),
      ),
      *chapter_synopsis_blocks(runtime_input),
      focus_block(
        key="chapter_excerpt",
        label="当前章节末尾摘录",
        content=_text(runtime_input.get("current_chapter")),
        content_mode="tail",
      ),
    ]
    blocks.extend(
      [
        focus_block(
          key="chapter_polish_prompt",
          label="小说润色提示词",
          content=_text(runtime_input.get("polish_prompt")),
        ),
        focus_block(
          key="selected_chapter_text",
          label="选中的小说正文",
          content=_text(runtime_input.get("selected_text")),
        ),
      ]
    )
    return blocks

  if request_type in {
    "quick_generate_next_paragraph",
    "generate_next_paragraph",
    "generate_next_section",
  }:
    blocks = [
      focus_block(
        key="chapter_title",
        label="章节标题",
        content=_text(runtime_input.get("chapter_title")),
      ),
      *chapter_synopsis_blocks(runtime_input),
      focus_block(
        key="insertion_point",
        label="正文生成插入点",
        content=_json(
          {
            "cursor_index": _int_or_none(runtime_input.get("cursor_index")),
            "previous_paragraph_key": "previous_paragraph",
            "next_paragraph_key": "next_paragraph",
            "rule": (
              "本次生成的 text 会插入在 previous_paragraph 之后、"
              "next_paragraph 之前；next_paragraph 为空表示光标后没有正文段落。"
            ),
          }
        ),
        format="json",
      ),
      focus_block(
        key="previous_paragraph",
        label="光标前最近的有文字段落",
        content=_text(runtime_input.get("previous_paragraph")),
      ),
      focus_block(
        key="next_paragraph",
        label="光标后第一段正文",
        content=_text(runtime_input.get("next_paragraph")),
        metadata={"optional": True},
      ),
      focus_block(
        key="chapter_excerpt",
        label="当前章节末尾摘录",
        content=_text(runtime_input.get("current_chapter")),
        content_mode="tail",
      ),
    ]
    if request_type != "quick_generate_next_paragraph":
      blocks.append(
        focus_block(
          key="writing_mode_prompt",
          label="写作方式提示词",
          content=_text(runtime_input.get("writing_prompt")),
        )
      )
    return blocks

  if request_type == "generate_chapter_blueprint":
    return [
      focus_block(
        key="chapter_title",
        label="章节标题",
        content=_text(runtime_input.get("chapter_title")),
      ),
      *chapter_synopsis_blocks(runtime_input),
      focus_block(
        key="insertion_point",
        label="光标插入位置",
        content=_insertion_point_text(runtime_input),
      ),
      focus_block(
        key="previous_paragraph",
        label="光标前最近的有文字段落",
        content=_text(runtime_input.get("previous_paragraph")),
      ),
      focus_block(
        key="next_paragraph",
        label="光标后第一段正文",
        content=_text(runtime_input.get("next_paragraph")),
        metadata={"optional": True},
      ),
      focus_block(
        key="insertion_target",
        label="采纳后处理方式",
        content="采纳后会把要点插入当前章节的光标位置，每条由程序加上外层「」；不要在 points 内自行添加编号、固定前缀或外层括号。",
      ),
      focus_block(
        key="chapter_excerpt",
        label="当前章节已有正文摘录",
        content=_text(runtime_input.get("current_chapter")),
        content_mode="tail",
      ),
      focus_block(
        key="blueprint_mode_prompt",
        label="基础铺设提示词",
        content=_text(runtime_input.get("blueprint_prompt")),
      ),
    ]

  if request_type in {"polish_document_selection", "generate_document_continuation"}:
    blocks = [
      *document_chapter_context_blocks(runtime_input),
      focus_block(
        key="document_title",
        label="资料标题",
        content=_text(runtime_input.get("document_title")),
      ),
      focus_block(
        key="document_excerpt",
        label="当前资料摘录",
        content=_text(runtime_input.get("current_document")),
        format="markdown",
        content_mode="tail",
      ),
    ]
    if request_type == "polish_document_selection":
      blocks.extend(
        [
          focus_block(
            key="document_polish_prompt",
            label="资料润色提示词",
            content=_text(runtime_input.get("polish_prompt")),
          ),
          focus_block(
            key="selected_document_text",
            label="选中的资料片段",
            content=_text(runtime_input.get("selected_text")),
            format="markdown",
          ),
        ]
      )
    else:
      blocks.append(
        focus_block(
          key="document_generation_prompt",
          label="资料生成提示词",
          content=_text(runtime_input.get("generation_prompt")),
        )
      )
    return blocks

  if request_type == "chat_about_work":
    blocks = [
      focus_block(
        key="chapter_title",
        label="当前章节标题",
        content=_text(runtime_input.get("chapter_title")),
        metadata={"optional": True},
      ),
      *chapter_synopsis_blocks(runtime_input, optional=True),
      focus_block(
        key="chapter_excerpt",
        label="当前章节摘录",
        content=_text(runtime_input.get("current_chapter")),
        content_mode="tail",
        metadata={"optional": True},
      ),
    ]
    chat_messages = _text(runtime_input.get("chat_messages"))
    if chat_messages:
      blocks.append(
        focus_block(
          key="chat_messages",
          label="当前对话摘录",
          content=chat_messages,
          metadata={"optional": True},
        )
      )
    return blocks

  return []


def _agents_for_request(
  request_type: PromptRequestType, runtime_input: dict[str, object]
) -> list[PromptContextAgentBlock]:
  if request_type == "perspective_suggestion":
    return [
      PromptContextAgentBlock(
        id=_text(item.get("id")),
        name=_text(item.get("name")),
        description=_text(item.get("description")),
        instructions=_text(item.get("instructions")),
      )
      for item in _dict_items(runtime_input.get("perspectives"))
      if _text(item.get("id"))
    ]

  author_persona = _text(runtime_input.get("author_persona"))
  if (
    request_type
    in {
      "quick_generate_next_paragraph",
      "generate_next_paragraph",
      "generate_next_section",
      "generate_chapter_blueprint",
    }
    and author_persona
  ):
    return [
      PromptContextAgentBlock(
        id=_text(runtime_input.get("author_persona_id")) or "author_persona",
        name=_text(runtime_input.get("author_persona_name")) or "执笔作者人格 / Skill",
        kind="author_persona",
        description="所选执笔作者人格 / Skill",
        instructions=author_persona,
      )
    ]

  editor_persona = _text(runtime_input.get("editor_persona"))
  if (
    request_type in {"polish_document_selection", "generate_document_continuation"}
    and editor_persona
  ):
    return [
      PromptContextAgentBlock(
        id=_text(runtime_input.get("editor_persona_id")) or "editor_persona",
        name=_text(runtime_input.get("editor_persona_name")) or "编辑人格 / Skill",
        kind="editor_persona",
        description="所选资料编辑人格 / Skill",
        instructions=editor_persona,
      )
    ]
  return []


def _constraints_for_request(request_type: PromptRequestType) -> list[str]:
  if request_type == "chat_about_work":
    return [
      "本请求为流式自由文本对话，不要求 JSON object。",
      "回答可以使用自然语言和必要的 Markdown。",
      "只基于用户问题、当前项目上下文和已提供素材回答；无法确定时要说明不确定。",
    ]

  common = ["最终响应必须遵守系统消息中的强制 JSON 输出契约。"]
  if request_type == "perspective_suggestion":
    return [
      *common,
      "每个 perspective 最多一张卡；perspective_id 必须来自 agents 列表。",
      "不要改写或续写正文。",
      "没有明显问题也给一个轻量建议；body 写摘要，detail 写展开原因和具体调整方向。",
    ]
  if request_type in {
    "quick_generate_next_paragraph",
    "generate_next_paragraph",
    "generate_next_section",
  }:
    extra = [
      "text 字段里不要加入标题、解释、项目符号或分析过程。",
      "生成内容会插入正文光标位置；不要改写、复述或包含 previous_paragraph 与 next_paragraph。",
      "如果 next_paragraph 非空，text 的结尾必须能自然接回 next_paragraph，但不要覆盖它。",
    ]
    if request_type == "quick_generate_next_paragraph":
      extra.append("快速生成默认只写一段短正文，不要大幅转场或生成完整小节。")
    return [
      *common,
      *extra,
    ]
  if request_type == "generate_chapter_blueprint":
    return [
      *common,
      "points 字段只能包含当前章节写作要点，不要写正文。",
      "不要给 points 自带编号、固定前缀、外层「」符号、项目符号或 Markdown；程序只会为每条要点加上外层「」。",
      "每条要点必须具体、可执行，能指导从光标位置继续写作时的场面、冲突、信息释放、爽点、伏笔或承接。",
    ]
  if request_type == "polish_selection":
    return [*common, "text 字段必须是可直接替换选区的小说正文。"]
  return [*common, "text 字段必须是可直接使用的 Markdown 片段。"]


def _dict_items(value: object) -> list[dict[str, Any]]:
  return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _insertion_point_text(runtime_input: dict[str, object]) -> str:
  cursor_index = _int_or_none(runtime_input.get("cursor_index"))
  if cursor_index is None:
    return "未指定 cursor_index；真实前端请求会提交正文光标位置，采纳后插入该位置。"
  return f"cursor_index={cursor_index}；采纳后会把生成的要点插入当前章节正文的这个光标位置。"


def _text(value: object) -> str:
  if value is None:
    return ""
  if isinstance(value, str):
    return value
  if isinstance(value, dict):
    return str(value)
  if isinstance(value, Perspective):
    return value.name
  return str(value)


def _json(value: object) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2)


def _int_or_none(value: object) -> int | None:
  return value if isinstance(value, int) and not isinstance(value, bool) else None
