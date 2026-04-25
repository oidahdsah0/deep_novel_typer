import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.chapters import CreateChapterRequest
from app.Schemas.projects import CreateProjectRequest
from app.Schemas.prompt_preview import PromptPreviewProfileOverride, PromptPreviewRequest
from app.Schemas.prompt_profiles import UpdatePromptProfileRequest
from tests.fakes import DisabledLLMClient, FakeLLMClient
from tests.service_factories import build_generation_services


@pytest.mark.asyncio
async def test_prompt_preview_warns_when_context_window_is_exceeded(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _generation_service,
    api_config_service,
    prompt_preview_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_preview_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在门口。")
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Tiny Preview Context",
        api_key="preview-secret",
        base_url="https://preview.example.test",
        mode="non_stream",
        model="preview-model",
        thinking_enabled=False,
        reasoning_effort="high",
        max_tokens=900,
        context_window_tokens=1024,
        is_default=True,
      ),
    )

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="generate_next_paragraph",
        chapter_id="chapter-001",
        writing_prompt="继续。",
        author_persona="克制。",
      ),
    )

    item = preview.items[0]
    assert item.token_estimate.context_window_tokens == 1024
    assert item.token_estimate.context_window_exceeded is True
    assert any("上下文超出" in warning for warning in item.warnings)
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_preview_uses_request_profile_api_config(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _generation_service,
    api_config_service,
    prompt_preview_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_preview_service=True,
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在门口。")
    selected_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Preview Model",
        api_key="preview-secret",
        base_url="https://preview.example.test",
        mode="non_stream",
        model="preview-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=False,
      ),
    )
    await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(config={"api_config_id": selected_config.id}),
    )

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="generate_next_paragraph",
        chapter_id="chapter-001",
        writing_prompt="继续。",
        author_persona="克制。",
      ),
    )

    assert preview.items[0].api_config is not None
    assert preview.items[0].api_config.model == "preview-model"
    assert preview.items[0].api_config.id == selected_config.id

    await api_config_service.delete_config(selected_config.id)
    fallback_preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="generate_next_paragraph",
        chapter_id="chapter-001",
        writing_prompt="继续。",
        author_persona="克制。",
      ),
    )

    assert fallback_preview.items[0].api_config is not None
    assert fallback_preview.items[0].api_config.id == "default-api"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_preview_expands_recent_chapters_without_calling_llm(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"不应调用"}')
  (
    store,
    project_service,
    chapter_service,
    _generation_service,
    api_config_service,
    prompt_preview_service,
  ) = await build_generation_services(
    tmp_path,
    llm_client,
    include_prompt_preview_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "第一章固定线索。")
    chapter_two = await chapter_service.create_chapter(
      project.id,
      CreateChapterRequest(title="Second Chapter", content="第二章动态线索。"),
    )
    chapter_three = await chapter_service.create_chapter(
      project.id,
      CreateChapterRequest(title="Third Chapter", content="第三章当前正文。"),
    )
    await chapter_service.update_chapter_writing_synopsis(
      project.id,
      chapter_three.id,
      "本章梗概：第三章要把当前线索推向港口。",
      base_updated_at=chapter_three.writing_synopsis_updated_at,
    )
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Preview Config",
        api_key="preview-secret",
        base_url="https://preview.example.test",
        mode="non_stream",
        model="preview-model",
        thinking_enabled=False,
        reasoning_effort="high",
        top_p=0.8,
        top_k=9,
        is_default=True,
      ),
    )

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="generate_next_paragraph",
        chapter_id=chapter_three.id,
        cursor_index=8,
        previous_paragraph="第三章",
        next_paragraph="当前正文。",
        writing_prompt="继续推进。",
        author_persona_id="skill",
        author_persona_name="冷静克制的悬疑作者",
        author_persona="保持克制。",
        profile_override=PromptPreviewProfileOverride(
          user_template="素材：\n{input.chapters}\n\n写作：{input.writing_prompt}",
          chapter_ids=["chapter-001"],
          config={"recent_chapter_enabled": True, "recent_chapter_count": 10},
        ),
      ),
    )

    assert len(llm_client.calls) == 0
    assert len(preview.items) == 1
    item = preview.items[0]
    assert item.api_config is not None
    assert item.api_config.configured is True
    assert item.api_config.model == "preview-model"
    assert item.request_options["response_format"] == {"type": "json_object"}
    assert item.request_options["stream"] is False
    assert item.request_options["top_p"] == 0.8
    assert item.request_options["top_k"] == 9
    assert item.token_estimate.input_tokens > 0
    assert item.token_estimate.system_tokens > 0
    assert item.token_estimate.user_tokens > 0
    assert item.token_estimate.output_token_budget == 4096
    assert item.token_estimate.total_with_output_budget == (
      item.token_estimate.input_tokens + 4096
    )
    assert item.context_pack is not None
    assert item.context_pack.request_type == "generate_next_paragraph"
    assert [block.key for block in item.context_pack.focus] == [
      "chapter_title",
      "chapter_synopsis",
      "insertion_point",
      "previous_paragraph",
      "next_paragraph",
      "chapter_excerpt",
      "writing_mode_prompt",
    ]
    assert item.context_pack.focus[1].content == "本章梗概：第三章要把当前线索推向港口。"
    assert item.context_pack.focus[2].format == "json"
    assert item.context_pack.focus[3].content == "第三章"
    assert item.context_pack.focus[4].content == "当前正文。"
    assert item.context_pack.agents[0].id == "skill"
    assert item.context_pack.agents[0].name == "冷静克制的悬疑作者"
    assert [material.id for material in item.context_pack.materials] == [
      "chapter-001",
      chapter_two.id,
    ]
    assert [material.id for material in item.chapters] == ["chapter-001", chapter_two.id]
    assert item.chapters[0].source == "recent+fixed"
    assert item.chapters[1].source == "recent"
    assert item.chapters[0].token_estimate > 0
    assert "继续推进。" in item.messages[1].content
    assert "第一章固定线索。" in item.messages[1].content
    assert "第二章动态线索。" in item.messages[1].content
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_preview_can_disable_current_chapter_synopsis(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _generation_service,
    api_config_service,
    prompt_preview_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_preview_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    base_chapter = await chapter_service.get_chapter(project.id, "chapter-001")
    await chapter_service.update_chapter_writing_synopsis(
      project.id,
      "chapter-001",
      "本章梗概：这段不应进入 context focus。",
      base_updated_at=base_chapter.writing_synopsis_updated_at,
    )
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Preview Config",
        api_key="preview-secret",
        base_url="https://preview.example.test",
        mode="non_stream",
        model="preview-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="generate_next_paragraph",
        chapter_id="chapter-001",
        profile_override=PromptPreviewProfileOverride(
          config={"include_chapter_synopsis": False},
        ),
      ),
    )

    item = preview.items[0]
    assert item.context_pack is not None
    assert "chapter_synopsis" not in [block.key for block in item.context_pack.focus]
    assert "这段不应进入 context focus" not in item.messages[1].content
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_preview_supports_document_requests(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    _api_config_service,
    document_service,
    prompt_preview_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_document_service=True,
    include_prompt_preview_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await document_service.update_document(
      project.id,
      "outline",
      "# 主线大纲\n\n- 林澈回到港口。",
    )

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="polish_document_selection",
        document_id="outline",
        selected_text="- 林澈回到港口。",
        polish_prompt="让资料更清晰。",
        editor_persona="保持 Markdown 列表。",
      ),
    )

    item = preview.items[0]
    assert item.context_pack is not None
    assert "document_excerpt" in {
      block.key for block in item.context_pack.focus
    }
    assert item.context_pack.focus[1].format == "markdown"
    assert "让资料更清晰。" in item.messages[1].content
    assert "保持 Markdown 列表。" in item.messages[1].content
    assert "- 林澈回到港口。" in item.messages[1].content
    assert item.documents == []
    assert item.warnings
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_preview_supports_chapter_blueprint_requests(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _generation_service,
    _api_config_service,
    _document_service,
    prompt_preview_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_document_service=True,
    include_prompt_preview_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "少年站在哨塔下。")

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="generate_chapter_blueprint",
        chapter_id="chapter-001",
        cursor_index=7,
        previous_paragraph="少年",
        next_paragraph="站在哨塔下。",
        blueprint_prompt="强调爽点和钩子。",
        author_persona_id="skill",
        author_persona_name="人格设定 Skill",
        author_persona="保持轻快。",
      ),
    )

    item = preview.items[0]
    assert item.context_pack is not None
    assert [block.key for block in item.context_pack.focus] == [
      "chapter_title",
      "chapter_synopsis",
      "insertion_point",
      "previous_paragraph",
      "next_paragraph",
      "insertion_target",
      "chapter_excerpt",
      "blueprint_mode_prompt",
    ]
    assert item.context_pack.request_type == "generate_chapter_blueprint"
    assert item.context_pack.agents[0].id == "skill"
    assert "强调爽点和钩子。" in item.messages[1].content
    assert "光标插入位置" in item.messages[1].content
    assert "cursor_index=7" in item.messages[1].content
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_preview_supports_quick_generation_requests(tmp_path) -> None:
  (
    store,
    project_service,
    chapter_service,
    _generation_service,
    _api_config_service,
    _document_service,
    prompt_preview_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_document_service=True,
    include_prompt_preview_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    await chapter_service.update_chapter(project.id, "chapter-001", "林澈停在门外。")

    preview = await prompt_preview_service.preview(
      project.id,
      PromptPreviewRequest(
        request_type="quick_generate_next_paragraph",
        chapter_id="chapter-001",
        cursor_index=6,
        previous_paragraph="林澈停在门外。",
        next_paragraph="门内忽然传来一声轻响。",
        quick_prompt="快速接一句动作。",
        author_persona_id="skill",
        author_persona_name="人格设定 Skill",
        author_persona="冷静克制。",
      ),
    )

    item = preview.items[0]
    assert item.context_pack is not None
    assert item.context_pack.request_type == "quick_generate_next_paragraph"
    assert "quick_generation_prompt" not in {
      block.key for block in item.context_pack.focus
    }
    assert "快速接一句动作。" not in item.messages[1].content
    assert "门内忽然传来一声轻响。" in item.messages[1].content
    assert item.context_pack.agents[0].id == "skill"
  finally:
    await store.shutdown()
