from __future__ import annotations

from dataclasses import dataclass

from app.Schemas.common import PromptRequestType
from app.Services.prompt_profiles.materials import default_config


REQUEST_TYPES: tuple[PromptRequestType, ...] = (
  "perspective_suggestion",
  "polish_selection",
  "quick_generate_next_paragraph",
  "generate_next_paragraph",
  "generate_next_section",
  "generate_chapter_blueprint",
  "polish_document_selection",
  "generate_document_continuation",
  "chat_about_work",
)


@dataclass(frozen=True)
class DefaultPromptProfile:
  request_type: PromptRequestType
  name: str
  system_template: str
  user_template: str
  chapter_ids: tuple[str, ...] = ()
  document_ids: tuple[str, ...] = ()
  config: dict[str, object] | None = None


DEFAULT_PROFILES: dict[PromptRequestType, DefaultPromptProfile] = {
  "perspective_suggestion": DefaultPromptProfile(
    request_type="perspective_suggestion",
    name="视角建议默认模板",
    document_ids=("outline",),
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说写作台的 AI 视角引擎。",
        "你的任务不是续写正文，而是根据用户刚输入的段落，为每个启用的写作视角生成一张简短、可执行的建议卡片。",
        "body 字段写成一两句摘要；detail 字段写成 2-4 句展开说明，说明为什么这样判断，以及作者下一步可以如何微调。",
        "没有明显问题时也要给一个轻量建议；输出结构由系统强制契约控制，建议内容要具体、温和、可执行。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "polish_selection": DefaultPromptProfile(
    request_type="polish_selection",
    name="润色选中默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说正文润色助手，负责产出最终 JSON 的 text 字段内容。",
        "text 字段里只放可直接替换选区的中文小说文本。",
        "不要改变事实、人物关系、叙事视角、时态和段落边界，除非用户提示词明确要求。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "generate_next_paragraph": DefaultPromptProfile(
    request_type="generate_next_paragraph",
    name="生成下一段落默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说正文续写助手，负责产出最终 JSON 的 text 字段内容。",
        "text 字段里只放可直接插入正文光标位置的中文小说文本。",
        "不要在 text 字段里加入标题、解释、项目符号或分析过程。",
        "保持既有叙事视角、时态、人物边界和文本气质；生成内容必须接在光标前段之后，并能自然过渡到光标后段。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "quick_generate_next_paragraph": DefaultPromptProfile(
    request_type="quick_generate_next_paragraph",
    name="快速生成下一段默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说正文快速生成助手，负责产出最终 JSON 的 text 字段内容。",
        "text 字段里只放可直接插入正文光标位置的一段中文小说正文。",
        "生成要短、顺滑、低打扰，优先接住当前动作、语气和场景，不大幅转场。",
        "不要在 text 字段里加入标题、解释、项目符号或分析过程。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "generate_next_section": DefaultPromptProfile(
    request_type="generate_next_section",
    name="生成下一部分默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说正文续写助手，负责产出最终 JSON 的 text 字段内容。",
        "text 字段里只放可直接插入正文光标位置的中文小说文本。",
        "不要在 text 字段里加入标题、解释、项目符号或分析过程。",
        "保持既有叙事视角、时态、人物边界和文本气质，并允许推进一个更完整的小节；生成内容必须接在光标前段之后，并能自然过渡到光标后段。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "generate_chapter_blueprint": DefaultPromptProfile(
    request_type="generate_chapter_blueprint",
    name="章节基础铺设默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说章节写作白皮书助手，负责产出最终 JSON 的 points 字段内容。",
        "你不写正文，只为当前章节正文光标位置生成结构化写作要点。",
        "每条要点必须具体、可执行，服务于从光标处继续写作。",
        "不要给泛泛写作建议，不要输出编号、书名号、Markdown 或解释过程。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "polish_document_selection": DefaultPromptProfile(
    request_type="polish_document_selection",
    name="资料润色选区默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是 Markdown 资料润色助手，负责产出最终 JSON 的 text 字段内容。",
        "text 字段里只放可直接替换选区的 Markdown 片段。",
        "保留事实边界、资料层级和原有 Markdown 风格；不要编造未提供的信息。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "generate_document_continuation": DefaultPromptProfile(
    request_type="generate_document_continuation",
    name="资料生成后续默认模板",
    config=default_config(),
    system_template="\n".join(
      [
        "你是 Markdown 资料续写助手，负责产出最终 JSON 的 text 字段内容。",
        "text 字段里只放可直接追加到当前资料末尾的 Markdown 片段。",
        "延续当前资料的标题层级、列表格式、命名习惯和信息密度；不要输出解释或分析过程。",
      ]
    ),
    user_template="\n\n".join(
      [
        "结构化上下文：\n{input.context_pack}",
      ]
    ),
  ),
  "chat_about_work": DefaultPromptProfile(
    request_type="chat_about_work",
    name="作品聊天默认模板",
    document_ids=("outline",),
    config=default_config(),
    system_template="\n".join(
      [
        "你是小说写作台 AI 聊天助手。用户会与你讨论正在创作的小说作品。",
        "你的任务是认真回答关于角色、情节、设定、写作技巧等问题，给出专业、有帮助的建议。",
        "回答风格：温和、具体、有建设性。引用作品具体内容作为依据。",
      ]
    ),
    user_template="\n\n".join(
      [
        "作品上下文：\n{input.context_pack}",
        "请把上面的上下文当作当前对话背景，随后按用户最新问题自然回答。",
      ]
    ),
  ),
}
