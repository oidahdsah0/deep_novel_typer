from __future__ import annotations

import os
from pathlib import Path

from app.Utils.config_helpers import _list, _preset_id, _read_yaml
from app.Utils.config_types import GenerationPresetDefault, GenerationSettings


def _load_generation_settings() -> GenerationSettings:
  default_path = Path(__file__).resolve().parents[2] / "config" / "generation.yaml"
  config_path = Path(os.getenv("NOVEL_TYPER_GENERATION_CONFIG", str(default_path))).resolve()
  payload = _read_yaml(config_path)
  presets: list[GenerationPresetDefault] = []

  for item in _list(payload.get("writing_modes")):
    presets.append(
      GenerationPresetDefault(
        kind="writing_mode",
        preset_id=_preset_id(item, fallback="writing-mode"),
        name=str(item.get("name") or "写作方式"),
        content=str(item.get("content") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("quick_generation_modes")):
    presets.append(
      GenerationPresetDefault(
        kind="quick_generation_mode",
        preset_id=_preset_id(item, fallback="quick-generation-mode"),
        name=str(item.get("name") or "快速生成方式"),
        content=str(item.get("content") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("chapter_blueprint_modes")):
    presets.append(
      GenerationPresetDefault(
        kind="chapter_blueprint_mode",
        preset_id=_preset_id(item, fallback="chapter-blueprint-mode"),
        name=str(item.get("name") or "章节铺设方式"),
        content=str(item.get("content") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("author_personas")):
    presets.append(
      GenerationPresetDefault(
        kind="author_persona",
        preset_id=_preset_id(item, fallback="author-persona"),
        name=str(item.get("name") or "执笔作者人格"),
        content=str(item.get("content") or item.get("skill") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("polish_modes")):
    presets.append(
      GenerationPresetDefault(
        kind="polish_mode",
        preset_id=_preset_id(item, fallback="polish-mode"),
        name=str(item.get("name") or "润色方式"),
        content=str(item.get("content") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("document_polish_modes")):
    presets.append(
      GenerationPresetDefault(
        kind="document_polish_mode",
        preset_id=_preset_id(item, fallback="document-polish-mode"),
        name=str(item.get("name") or "资料润色方式"),
        content=str(item.get("content") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("document_generation_modes")):
    presets.append(
      GenerationPresetDefault(
        kind="document_generation_mode",
        preset_id=_preset_id(item, fallback="document-generation-mode"),
        name=str(item.get("name") or "资料续写方式"),
        content=str(item.get("content") or item.get("prompt") or ""),
      )
    )

  for item in _list(payload.get("editor_personas")):
    presets.append(
      GenerationPresetDefault(
        kind="editor_persona",
        preset_id=_preset_id(item, fallback="editor-persona"),
        name=str(item.get("name") or "资料编辑人格"),
        content=str(item.get("content") or item.get("skill") or item.get("prompt") or ""),
      )
    )

  if not presets:
    presets = list(_default_generation_presets())

  return GenerationSettings(presets=tuple(presets), config_path=config_path)


def _default_generation_presets() -> tuple[GenerationPresetDefault, ...]:
  return (
    GenerationPresetDefault(
      kind="writing_mode",
      preset_id="camera",
      name="镜头写作",
      content=(
        "以镜头语言续写：先给出清晰的空间位置和人物动作，再通过可见、可听、"
        "可触的细节推进情绪。避免解释性总结，让读者从动作和画面里理解变化。"
      ),
    ),
    GenerationPresetDefault(
      kind="chapter_blueprint_mode",
      preset_id="basic-blueprint",
      name="基础铺设",
      content=(
        "为当前章节的正文光标位置生成基础写作要点：包括当前位置的承接目标、场面画面、主要冲突、"
        "信息释放顺序、爽点或钩子、伏笔与后续承接。每条都要具体可执行，不要写正文。"
      ),
    ),
    GenerationPresetDefault(
      kind="quick_generation_mode",
      preset_id="quick-next-paragraph",
      name="快速下一段",
      content=(
        "快速生成一段能接住当前光标位置的正文：短、顺滑、低打扰，优先承接动作、"
        "语气和场景，不大幅转场，不主动解释设定。"
      ),
    ),
    GenerationPresetDefault(
      kind="writing_mode",
      preset_id="linear",
      name="线性写作",
      content=(
        "沿着上一段的因果顺序续写：承接当前动作或信息，保持时间线清楚，"
        "每一段只推进一个主要变化，并在末尾留下自然的下一步。"
      ),
    ),
    GenerationPresetDefault(
      kind="writing_mode",
      preset_id="other",
      name="其他写作方式",
      content="",
    ),
    GenerationPresetDefault(
      kind="author_persona",
      preset_id="restrained-suspense",
      name="冷静克制的悬疑作者",
      content=(
        "你是一位冷静克制的悬疑小说作者。你的语言干净、具体，重视动作、"
        "空间和线索的递进；避免夸张抒情，避免替读者解释情绪。"
      ),
    ),
    GenerationPresetDefault(
      kind="author_persona",
      preset_id="skill",
      name="人格设定 Skill",
      content=(
        "保持当前项目的叙事气质和人物边界。优先写可直接放入正文的段落，"
        "最终 JSON 的 text 字段里不包含分析、标题或创作意图解释。"
      ),
    ),
    GenerationPresetDefault(
      kind="polish_mode",
      preset_id="tighten",
      name="凝练润色",
      content=(
        "在不改变事实、人物关系和叙事视角的前提下，压紧句子，删去松散重复，"
        "让选中文本更清楚、更有推进力。最终 JSON 的 text 字段只包含润色后的文本。"
      ),
    ),
    GenerationPresetDefault(
      kind="polish_mode",
      preset_id="sensory-detail",
      name="增强感官细节",
      content=(
        "保留原意和段落结构，补强可见、可听、可触的具体细节，让画面更清晰，"
        "但不要额外推进剧情或新增关键设定。最终 JSON 的 text 字段只包含润色后的文本。"
      ),
    ),
    GenerationPresetDefault(
      kind="polish_mode",
      preset_id="style-match",
      name="贴合既有文风",
      content=(
        "参考当前章节的语气、节奏和用词习惯，润色选中文本，使其更自然地融入前后文。"
        "不要解释修改理由；最终 JSON 的 text 字段只包含润色后的文本。"
      ),
    ),
    GenerationPresetDefault(
      kind="polish_mode",
      preset_id="other-polish",
      name="其他润色方式",
      content="",
    ),
    GenerationPresetDefault(
      kind="document_polish_mode",
      preset_id="document-tighten",
      name="资料凝练润色",
      content=(
        "在保留 Markdown 结构、事实和信息层级的前提下，压紧选中资料文本，"
        "删去重复和含混表达。最终 JSON 的 text 字段只包含可直接替换选区的 Markdown 片段。"
      ),
    ),
    GenerationPresetDefault(
      kind="document_polish_mode",
      preset_id="document-clarify",
      name="资料清晰化",
      content=(
        "让选中资料更适合后续检索和引用：补齐必要上下文，明确术语、人物、地点或线索关系，"
        "但不要编造未给出的事实。最终 JSON 的 text 字段只包含 Markdown 片段。"
      ),
    ),
    GenerationPresetDefault(
      kind="document_polish_mode",
      preset_id="other-document-polish",
      name="其他资料润色方式",
      content="",
    ),
    GenerationPresetDefault(
      kind="document_generation_mode",
      preset_id="document-continue",
      name="延续当前资料",
      content=(
        "根据当前资料已有内容继续补写，保持 Markdown 层级、标题风格和信息密度一致；"
        "优先补充可复用、可检索的设定信息。最终 JSON 的 text 字段只包含要追加的 Markdown 片段。"
      ),
    ),
    GenerationPresetDefault(
      kind="document_generation_mode",
      preset_id="document-expand",
      name="扩展设定细节",
      content=(
        "围绕当前资料主题扩展更具体的设定、清单或关系说明。不要覆盖已有内容，"
        "不要输出分析过程。最终 JSON 的 text 字段只包含要追加的 Markdown 片段。"
      ),
    ),
    GenerationPresetDefault(
      kind="document_generation_mode",
      preset_id="other-document-generation",
      name="其他资料生成方式",
      content="",
    ),
    GenerationPresetDefault(
      kind="editor_persona",
      preset_id="structured-editor",
      name="结构化资料编辑",
      content=(
        "你是一位谨慎的资料编辑，重视事实边界、Markdown 层级、清晰命名和可检索性。"
        "最终 JSON 的 text 字段里不包含解释、标题外壳或创作意图。"
      ),
    ),
    GenerationPresetDefault(
      kind="editor_persona",
      preset_id="editor-skill",
      name="编辑人格 Skill",
      content=(
        "保持当前资料的语气和格式；新增或替换内容应能直接写回 Markdown 文档。"
        "最终 JSON 的 text 字段里不包含分析、修改说明或额外包裹。"
      ),
    ),
  )
