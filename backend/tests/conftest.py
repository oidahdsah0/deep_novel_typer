import pytest

from tests.service_factories import (
  build_generation_services,
  build_services,
  build_suggestion_services,
  build_version_services,
)


@pytest.fixture
def service_factory():
  return build_services


@pytest.fixture
def version_service_factory():
  return build_version_services


@pytest.fixture
def suggestion_service_factory():
  return build_suggestion_services


@pytest.fixture
def generation_service_factory():
  return build_generation_services
