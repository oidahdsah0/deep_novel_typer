import pytest

from app.Schemas.api_configs import CreateAPIConfigRequest
from app.Schemas.chapters import CreateChapterRequest
from app.Schemas.generation import GenerateDraftRequest
from app.Schemas.projects import CreateProjectRequest
from app.Schemas.prompt_profiles import UpdatePromptProfileRequest
from app.Utils.errors import DomainError, EntityNotFoundError
from tests.fakes import DisabledLLMClient, FakeLLMClient
from tests.service_factories import build_generation_services

@pytest.mark.asyncio
async def test_prompt_profile_recent_chapters_follow_current_chapter(tmp_path) -> None:
  llm_client = FakeLLMClient('{"text":"下一段。"}')
  (
    store,
    project_service,
    chapter_service,
    generation_service,
    api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    llm_client,
    include_prompt_profile_service=True,
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
    await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Draft Config",
        api_key="draft-secret",
        base_url="https://draft.example.test",
        mode="non_stream",
        model="draft-model",
        thinking_enabled=False,
        reasoning_effort="high",
        is_default=True,
      ),
    )
    await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        chapter_ids=["chapter-001"],
        config={"recent_chapter_enabled": True, "recent_chapter_count": 2},
      ),
    )

    await generation_service.generate_draft(
      project.id,
      GenerateDraftRequest(
        chapter_id=chapter_three.id,
        action="next_paragraph",
        writing_preset_id="camera",
        writing_prompt="继续。",
        author_preset_id="skill",
        author_skill="克制。",
      ),
    )

    user_prompt = llm_client.calls[0][0][1].content
    assert user_prompt.count('id="chapter-001"') == 1
    assert f'id="{chapter_two.id}"' in user_prompt
    assert "第二章动态线索。" in user_prompt
    assert "<context_pack" in user_prompt
    assert '"id": "skill"' in user_prompt
    assert '"name": "人格设定 Skill"' in user_prompt

    await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        chapter_ids=["chapter-001"],
        config={"recent_chapter_enabled": False, "recent_chapter_count": 2},
      ),
    )
    llm_client.calls.clear()
    await generation_service.generate_draft(
      project.id,
      GenerateDraftRequest(
        chapter_id=chapter_three.id,
        action="next_paragraph",
        writing_preset_id="camera",
        writing_prompt="继续。",
        author_preset_id="skill",
        author_skill="克制。",
      ),
    )

    fixed_only_prompt = llm_client.calls[0][0][1].content
    assert fixed_only_prompt.count('id="chapter-001"') == 1
    assert f'id="{chapter_two.id}"' not in fixed_only_prompt
    assert "第二章动态线索。" not in fixed_only_prompt
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_profile_api_config_reference_is_cleared_when_config_is_deleted(
  tmp_path,
) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    custom_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Request Config",
        provider="deepseek",
        kind="llm",
        api_key_required=True,
        api_key="request-secret",
        base_url="https://api.deepseek.com",
        mode="non_stream",
        model="deepseek-chat",
        thinking_enabled=False,
        max_tokens=1024,
        temperature=None,
        top_p=None,
        top_k=None,
      )
    )
    await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        config={
          "api_config_id": custom_config.id,
          "recent_chapter_enabled": True,
          "recent_chapter_count": 2,
        },
      ),
    )

    assert (
      await prompt_profile_service.request_api_config_id(
        project.id,
        "generate_next_paragraph",
      )
    ) == custom_config.id

    await api_config_service.delete_config(custom_config.id)

    profile = await prompt_profile_service.get_profile(
      project.id,
      "generate_next_paragraph",
    )
    config_id = await prompt_profile_service.request_api_config_id(
      project.id,
      "generate_next_paragraph",
    )
    effective_config = await api_config_service.get_effective_config(config_id, kind="llm")

    assert "api_config_id" not in profile.config
    assert profile.config["recent_chapter_enabled"] is True
    assert profile.config["recent_chapter_count"] == 2
    assert config_id is None
    assert effective_config is not None
    assert effective_config.config.id == "default-api"
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_profile_rejects_invalid_api_config_references(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))
    embedding_config = await api_config_service.create_config(
      CreateAPIConfigRequest(
        name="Embedding Config",
        provider="openai",
        kind="embedding",
        api_key_required=True,
        api_key="embedding-secret",
        base_url="https://api.openai.com/v1",
        mode="non_stream",
        model="text-embedding-3-small",
        thinking_enabled=False,
        max_tokens=1024,
        temperature=None,
        top_p=None,
        top_k=None,
        dimensions=1536,
      )
    )

    with pytest.raises(EntityNotFoundError, match="LLM API config not found"):
      await prompt_profile_service.update_profile(
        project.id,
        "generate_next_paragraph",
        UpdatePromptProfileRequest(config={"api_config_id": "missing-config"}),
      )

    with pytest.raises(EntityNotFoundError, match="LLM API config not found"):
      await prompt_profile_service.update_profile(
        project.id,
        "generate_next_paragraph",
        UpdatePromptProfileRequest(config={"api_config_id": embedding_config.id}),
      )

    profile = await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        config={"api_config_id": "  ", "recent_chapter_enabled": False},
      ),
    )

    assert "api_config_id" not in profile.config
    assert profile.config["recent_chapter_enabled"] is False
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_profile_temperature_is_normalized_and_stored_in_config(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    _api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    profile = await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(config={"temperature": "0.75"}),
    )

    assert profile.config["temperature"] == 0.75
    assert (
      await prompt_profile_service.request_temperature(
        project.id,
        "generate_next_paragraph",
      )
    ) == 0.75

    profile = await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(config={"temperature": ""}),
    )

    assert "temperature" not in profile.config
    assert (
      await prompt_profile_service.request_temperature(
        project.id,
        "generate_next_paragraph",
      )
      is None
    )

    with pytest.raises(DomainError, match="Temperature"):
      await prompt_profile_service.update_profile(
        project.id,
        "generate_next_paragraph",
        UpdatePromptProfileRequest(config={"temperature": 2.5}),
      )
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_profile_versions_capture_initial_manual_and_restore(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    _api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_profile_service=True,
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    first = await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        name="第一版",
        system_template="系统提示第一版",
        user_template="用户提示第一版 {input.chapters}",
        chapter_ids=["chapter-001"],
        config={"recent_chapter_enabled": False, "recent_chapter_count": 2},
      ),
    )
    assert first.name == "第一版"

    initial_versions = await prompt_profile_service.list_versions(
      project.id, "generate_next_paragraph"
    )
    assert [version.version_type for version in initial_versions] == ["manual", "initial"]
    first_manual = next(version for version in initial_versions if version.version_type == "manual")
    first_detail = await prompt_profile_service.get_version(
      project.id, "generate_next_paragraph", first_manual.id
    )
    assert first_detail.snapshot.system_template == "系统提示第一版"
    assert first_detail.snapshot.chapter_ids == ["chapter-001"]

    await prompt_profile_service.update_profile(
      project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(
        name="第二版",
        system_template="系统提示第二版",
        user_template="用户提示第二版",
        document_ids=["outline"],
        config={"recent_chapter_enabled": True, "recent_chapter_count": 4},
      ),
    )

    restored = await prompt_profile_service.restore_version(
      project.id,
      "generate_next_paragraph",
      first_manual.id,
    )
    assert restored.profile.name == "第一版"
    assert restored.profile.system_template == "系统提示第一版"
    assert restored.profile.user_template == "用户提示第一版 {input.chapters}"
    assert restored.profile.chapter_ids == ["chapter-001"]
    assert restored.profile.document_ids == []
    assert restored.profile.config["recent_chapter_enabled"] is False

    versions_after_restore = await prompt_profile_service.list_versions(
      project.id, "generate_next_paragraph"
    )
    assert versions_after_restore[0].version_type == "pre_restore"
    pre_restore_detail = await prompt_profile_service.get_version(
      project.id,
      "generate_next_paragraph",
      versions_after_restore[0].id,
    )
    assert pre_restore_detail.snapshot.name == "第二版"
    assert pre_restore_detail.snapshot.document_ids == ["outline"]
  finally:
    await store.shutdown()


@pytest.mark.asyncio
async def test_prompt_profile_versions_are_project_and_request_type_scoped(tmp_path) -> None:
  (
    store,
    project_service,
    _chapter_service,
    _generation_service,
    _api_config_service,
    prompt_profile_service,
  ) = await build_generation_services(
    tmp_path,
    DisabledLLMClient(),
    include_prompt_profile_service=True,
  )
  try:
    first_project = await project_service.create_project(CreateProjectRequest(title="First Book"))
    second_project = await project_service.create_project(CreateProjectRequest(title="Second Book"))

    await prompt_profile_service.update_profile(
      first_project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(name="第一本正文续写", user_template="第一本正文续写"),
    )
    await prompt_profile_service.update_profile(
      first_project.id,
      "polish_selection",
      UpdatePromptProfileRequest(name="第一本润色", user_template="第一本润色"),
    )
    await prompt_profile_service.update_profile(
      second_project.id,
      "generate_next_paragraph",
      UpdatePromptProfileRequest(name="第二本正文续写", user_template="第二本正文续写"),
    )

    first_draft_versions = await prompt_profile_service.list_versions(
      first_project.id,
      "generate_next_paragraph",
    )
    first_polish_versions = await prompt_profile_service.list_versions(
      first_project.id,
      "polish_selection",
    )
    second_draft_versions = await prompt_profile_service.list_versions(
      second_project.id,
      "generate_next_paragraph",
    )

    assert {version.project_id for version in first_draft_versions} == {first_project.id}
    assert {version.request_type for version in first_draft_versions} == {
      "generate_next_paragraph"
    }
    assert {version.request_type for version in first_polish_versions} == {"polish_selection"}
    assert {version.project_id for version in second_draft_versions} == {second_project.id}
    assert len(first_draft_versions) == 2
    assert len(first_polish_versions) == 2
    assert len(second_draft_versions) == 2
  finally:
    await store.shutdown()
