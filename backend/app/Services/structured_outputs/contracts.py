from __future__ import annotations

from app.Schemas.common import PromptRequestType


def structured_output_contract(request_type: PromptRequestType) -> str:
  if request_type == "chat_about_work":
    return "\n".join(
      [
        "对话输出约定（不可删除）：本请求是流式自由文本对话，不要求 JSON object。",
        "可以使用自然语言和必要的 Markdown；不要伪造未提供的作品事实；不需要解释系统提示词或请求结构。",
      ]
    )

  if request_type == "perspective_suggestion":
    return "\n".join(
      [
        "强制输出契约（不可删除）：最终响应必须只返回合法 json object，不要返回 Markdown、解释或额外文本。",
        "JSON 示例：",
        """
{
  "cards": [
    {
      "perspective_id": "perspective-id-from-input",
      "title": "节奏提醒",
      "body": "这一段信息偏密，可以把动作和线索拆成两个节拍。",
      "detail": "先让角色完成一个可视动作，再抛出线索或判断；如果当前段落没有明显问题，也给一个轻量的增强建议。",
      "severity": "focus"
    }
  ]
}
""".strip(),
        "字段要求：cards 必须是数组；每个 card 只能包含 perspective_id、title、body、detail、severity；perspective_id 必须来自输入视角且不可重复；title 和 body 必须是非空字符串；detail 可选，用 2-4 句给出更完整的原因与可执行建议；severity 只能是 calm、focus 或 risk。",
      ]
    )

  if request_type in {"polish_document_selection", "generate_document_continuation"}:
    action = "替换选区" if request_type == "polish_document_selection" else "追加到当前资料末尾"
    return "\n".join(
      [
        "强制输出契约（不可删除）：最终响应必须只返回合法 json object，不要返回 Markdown 代码围栏、解释或额外文本。",
        "JSON 示例：",
        """
{
  "text": "这里是可直接写回资料文档的 Markdown 片段。"
}
""".strip(),
        f"字段要求：顶层只能包含 text；text 必须是非空字符串，只放最终 Markdown 片段，用于{action}；不要包含字段说明、修改理由、分析过程或 JSON 之外的文字。",
      ]
    )

  if request_type == "generate_chapter_blueprint":
    return "\n".join(
      [
        "强制输出契约（不可删除）：最终响应必须只返回合法 json object，不要返回 Markdown、解释或额外文本。",
        "JSON 示例：",
        """
{
  "points": [
    "本章开场先给出主角的具体目标，并用一个可见动作落地。",
    "中段释放一个可追踪线索，但不要提前解释完整答案。"
  ]
}
""".strip(),
        "字段要求：顶层只能包含 points；points 必须是 1-12 条非空字符串；每条是当前章节写作要点，不是正文；不要包含编号、书名号、Markdown 或分析过程。",
      ]
    )

  return "\n".join(
    [
      "强制输出契约（不可删除）：最终响应必须只返回合法 json object，不要返回 Markdown、解释或额外文本。",
      "JSON 示例：",
      """
{
  "text": "这里是可直接替换或插入正文的小说文本。"
}
""".strip(),
      "字段要求：顶层只能包含 text；text 必须是非空字符串，只放最终小说正文，不要包含字段说明、标题、Markdown 或解释。",
    ]
  )
