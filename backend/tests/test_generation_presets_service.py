import pytest

from app.Schemas.generation import (
  CreateGenerationPresetRequest,
  UpdateGenerationPresetRequest,
)
from app.Schemas.projects import CreateProjectRequest
from tests.fakes import DisabledLLMClient
from tests.service_factories import build_generation_services


@pytest.mark.asyncio
async def test_generation_presets_merge_yaml_defaults_with_project_overrides(tmp_path) -> None:
  store, project_service, _chapter_service, generation_service, _api_config_service = (
    await build_generation_services(tmp_path, DisabledLLMClient())
  )
  try:
    project = await project_service.create_project(CreateProjectRequest(title="Test Book"))

    defaults = await generation_service.list_presets(project.id)
    updated = await generation_service.update_preset(
      project.id,
      "writing_mode",
      "camera",
      UpdateGenerationPresetRequest(content="项目覆盖后的镜头提示词"),
    )
    custom = await generation_service.create_preset(
      project.id,
      CreateGenerationPresetRequest(
        kind="writing_mode",
        name="Flashback",
        content="倒叙写作提示词",
      ),
    )
    after_update = await generation_service.list_presets(project.id)

    await generation_service.delete_preset(project.id, "writing_mode", "camera")
    after_hidden = await generation_service.list_presets(project.id)
    await generation_service.delete_preset(project.id, "writing_mode", custom.id)
    after_delete = await generation_service.list_presets(project.id)

    assert [preset.id for preset in defaults.writing_modes] == ["camera", "linear"]
    assert [preset.id for preset in defaults.quick_generation_modes] == [
      "quick-next-paragraph"
    ]
    assert [preset.id for preset in defaults.chapter_blueprint_modes] == ["basic-blueprint"]
    assert [preset.id for preset in defaults.author_personas] == ["skill"]
    assert [preset.id for preset in defaults.polish_modes] == ["tighten"]
    assert [preset.id for preset in defaults.document_polish_modes] == ["document-tighten"]
    assert [preset.id for preset in defaults.document_generation_modes] == ["document-continue"]
    assert [preset.id for preset in defaults.editor_personas] == ["structured-editor"]
    assert updated.is_system is True
    assert updated.content == "项目覆盖后的镜头提示词"
    assert custom.is_system is False
    assert custom.id == "flashback"
    assert {
      preset.id: preset.content for preset in after_update.writing_modes
    }["camera"] == "项目覆盖后的镜头提示词"
    assert "camera" not in {preset.id for preset in after_hidden.writing_modes}
    assert "flashback" not in {preset.id for preset in after_delete.writing_modes}
  finally:
    await store.shutdown()
