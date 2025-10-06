import pytest
from pathlib import Path
import tempfile
import shutil

from core.scanner import SystemScanner
from models.scan_result import FileCategory, CleaningPriority
from utils.config import Config


class TestNewCategories:

    @pytest.fixture
    def config(self):
        return Config(dry_run=True, max_workers=2)

    @pytest.fixture
    def scanner(self, config):
        return SystemScanner(config)

    def test_xcode_categories_exist(self, scanner):
        assert FileCategory.XCODE_DERIVED_DATA in scanner.scan_paths
        assert FileCategory.XCODE_ARCHIVES in scanner.scan_paths

    def test_docker_category_exists(self, scanner):
        assert FileCategory.DOCKER_DATA in scanner.scan_paths

    def test_homebrew_category_exists(self, scanner):
        assert FileCategory.HOMEBREW_CACHE in scanner.scan_paths

    def test_nodejs_category_exists(self, scanner):
        assert FileCategory.NODE_MODULES in scanner.scan_paths

    def test_python_category_exists(self, scanner):
        assert FileCategory.PYTHON_CACHE in scanner.scan_paths

    def test_xcode_priority(self, scanner):
        priority = scanner._get_category_priority(FileCategory.XCODE_DERIVED_DATA)
        assert priority == CleaningPriority.HIGH

    def test_xcode_description(self, scanner):
        desc = scanner._get_category_description(FileCategory.XCODE_DERIVED_DATA)
        assert "Xcode" in desc
        assert len(desc) > 0

    def test_docker_priority(self, scanner):
        priority = scanner._get_category_priority(FileCategory.DOCKER_DATA)
        assert priority == CleaningPriority.MEDIUM

    def test_homebrew_priority(self, scanner):
        priority = scanner._get_category_priority(FileCategory.HOMEBREW_CACHE)
        assert priority == CleaningPriority.MEDIUM

    def test_node_modules_is_cleanable(self, scanner):
        node_modules_path = Path("/tmp/test/node_modules")
        is_cleanable = scanner._is_cleanable(node_modules_path, FileCategory.NODE_MODULES)
        assert is_cleanable is True

    def test_python_cache_is_cleanable(self, scanner):
        pycache_path = Path("/tmp/test/__pycache__")
        is_cleanable = scanner._is_cleanable(pycache_path, FileCategory.PYTHON_CACHE)
        assert is_cleanable is True

        pyc_file = Path("/tmp/test/module.pyc")
        is_cleanable = scanner._is_cleanable(pyc_file, FileCategory.PYTHON_CACHE)
        assert is_cleanable is True

    def test_all_new_categories_have_priority(self, scanner):
        new_categories = [
            FileCategory.XCODE_DERIVED_DATA,
            FileCategory.XCODE_ARCHIVES,
            FileCategory.DOCKER_DATA,
            FileCategory.HOMEBREW_CACHE,
            FileCategory.NODE_MODULES,
            FileCategory.PYTHON_CACHE,
        ]

        for category in new_categories:
            priority = scanner._get_category_priority(category)
            assert priority is not None
            assert isinstance(priority, CleaningPriority)

    def test_all_new_categories_have_description(self, scanner):
        new_categories = [
            FileCategory.XCODE_DERIVED_DATA,
            FileCategory.XCODE_ARCHIVES,
            FileCategory.DOCKER_DATA,
            FileCategory.HOMEBREW_CACHE,
            FileCategory.NODE_MODULES,
            FileCategory.PYTHON_CACHE,
        ]

        for category in new_categories:
            desc = scanner._get_category_description(category)
            assert desc is not None
            assert len(desc) > 0

    def test_scan_with_new_categories(self, scanner):
        scan_result = scanner.scan([
            FileCategory.XCODE_DERIVED_DATA,
            FileCategory.DOCKER_DATA,
            FileCategory.HOMEBREW_CACHE
        ])

        assert scan_result is not None


if __name__ == "__main__":
    pytest.main([__file__])
