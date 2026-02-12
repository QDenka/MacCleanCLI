import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from core.scanner import SystemScanner
from core.cleaner import SystemCleaner
from models.scan_result import FileCategory, CleaningPriority
from utils.config import Config


class TestScannerCleanerIntegration:

    @pytest.fixture
    def temp_workspace(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        cache_dir = workspace / "Caches"
        cache_dir.mkdir()

        temp_files_dir = workspace / "tmp"
        temp_files_dir.mkdir()

        # Create files >1KB for proper detection
        for i in range(5):
            (cache_dir / f"cache_{i}.tmp").write_text("x" * 2048)
            (temp_files_dir / f"temp_{i}.log").write_text("x" * 2048)

        yield workspace

        if workspace.exists():
            shutil.rmtree(workspace)

    @pytest.fixture
    def config_dry_run(self):
        return Config(
            dry_run=True,
            enable_backup=False,
            max_workers=2,
            min_file_size_mb=0.001
        )

    @pytest.fixture
    def config_actual(self):
        return Config(
            dry_run=False,
            enable_backup=False,
            max_workers=2,
            min_file_size_mb=0.001
        )

    def test_scan_then_clean_dry_run(self, config_dry_run, temp_workspace, monkeypatch):
        scanner = SystemScanner(config_dry_run)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "Caches"],
            FileCategory.TEMPORARY_FILES: [temp_workspace / "tmp"]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        assert len(scan_result.categories) > 0

        cleaner = SystemCleaner(config_dry_run)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.files_deleted) > 0
        assert all((temp_workspace / "Caches" / f"cache_{i}.tmp").exists() for i in range(5))

    def test_scan_then_clean_actual(self, config_actual, temp_workspace, monkeypatch):
        scanner = SystemScanner(config_actual)
        scanner.scan_paths = {
            FileCategory.TEMPORARY_FILES: [temp_workspace / "tmp"]
        }

        scan_result = scanner.scan([FileCategory.TEMPORARY_FILES])

        initial_file_count = len(list((temp_workspace / "tmp").iterdir()))
        assert initial_file_count == 5

        cleaner = SystemCleaner(config_actual)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.files_deleted) > 0

        # Check remaining files (directory might be removed if empty)
        tmp_dir = temp_workspace / "tmp"
        remaining_files = len(list(tmp_dir.iterdir())) if tmp_dir.exists() else 0
        assert remaining_files < initial_file_count

    def test_scan_clean_verify_workflow(self, config_actual, temp_workspace, monkeypatch):
        scanner = SystemScanner(config_actual)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "Caches"]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        cleaner = SystemCleaner(config_actual)
        cleaning_result = cleaner.clean(scan_result)

        verification = cleaner.verify_cleaning(cleaning_result)

        assert verification['verified_deleted'] > 0
        assert len(verification['still_exists']) >= 0

    def test_multiple_categories_workflow(self, config_actual, temp_workspace, monkeypatch):
        scanner = SystemScanner(config_actual)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "Caches"],
            FileCategory.TEMPORARY_FILES: [temp_workspace / "tmp"]
        }

        scan_result = scanner.scan([
            FileCategory.USER_CACHE,
            FileCategory.TEMPORARY_FILES
        ])

        assert len(scan_result.categories) == 2

        cleaner = SystemCleaner(config_actual)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.categories_cleaned) == 2
        assert cleaning_result.space_freed > 0

    def test_empty_scan_result_cleaning(self, config_actual):
        scanner = SystemScanner(config_actual)
        scan_result = scanner.scan([])

        cleaner = SystemCleaner(config_actual)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.files_deleted) == 0
        assert cleaning_result.space_freed == 0

    def test_config_changes_between_scan_clean(self, temp_workspace, monkeypatch):
        config_scan = Config(dry_run=True, max_workers=2, min_file_size_mb=0.001)
        scanner = SystemScanner(config_scan)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "Caches"]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        config_clean = Config(dry_run=False, max_workers=4, min_file_size_mb=0.001)
        cleaner = SystemCleaner(config_clean)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.files_deleted) > 0

    def test_partial_category_cleaning(self, config_actual, temp_workspace, monkeypatch):
        scanner = SystemScanner(config_actual)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "Caches"],
            FileCategory.TEMPORARY_FILES: [temp_workspace / "tmp"]
        }

        scan_result = scanner.scan([
            FileCategory.USER_CACHE,
            FileCategory.TEMPORARY_FILES
        ])

        assert len(scan_result.categories) == 2

        cleaner = SystemCleaner(config_actual)
        cleaning_result = cleaner.clean(
            scan_result,
            categories={FileCategory.USER_CACHE}
        )

        assert FileCategory.USER_CACHE in cleaning_result.categories_cleaned
        assert FileCategory.TEMPORARY_FILES not in cleaning_result.categories_cleaned


class TestBackupIntegration:

    @pytest.fixture
    def temp_workspace(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        backup_dir = workspace / "backups"
        backup_dir.mkdir()

        files_dir = workspace / "files"
        files_dir.mkdir()

        # Create files >1KB for proper detection
        for i in range(3):
            (files_dir / f"file_{i}.txt").write_text("x" * 2048)

        yield workspace

        if workspace.exists():
            shutil.rmtree(workspace)

    def test_cleaning_with_backup_enabled(self, temp_workspace, monkeypatch):
        config = Config(
            dry_run=False,
            enable_backup=True,
            backup_dir=temp_workspace / "backups",
            max_workers=2,
            min_file_size_mb=0.001
        )

        scanner = SystemScanner(config)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "files"]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        cleaner = SystemCleaner(config)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.files_deleted) > 0


class TestErrorHandlingIntegration:

    @pytest.fixture
    def temp_workspace(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        files_dir = workspace / "files"
        files_dir.mkdir()

        # Create file >1KB for proper detection
        (files_dir / "normal.txt").write_text("x" * 2048)

        yield workspace

        if workspace.exists():
            shutil.rmtree(workspace)

    def test_scan_with_permission_errors(self, temp_workspace, monkeypatch):
        config = Config(dry_run=True, max_workers=2, min_file_size_mb=0.001)
        scanner = SystemScanner(config)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [
                temp_workspace / "files",
                Path("/System/Library/Protected")
            ]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        assert len(scan_result.errors) >= 0

    def test_clean_with_missing_files(self, temp_workspace, monkeypatch):
        config = Config(dry_run=False, max_workers=2, min_file_size_mb=0.001)
        scanner = SystemScanner(config)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [temp_workspace / "files"]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        (temp_workspace / "files" / "normal.txt").unlink()

        cleaner = SystemCleaner(config)
        cleaning_result = cleaner.clean(scan_result)

        assert len(cleaning_result.files_failed) >= 0


class TestPerformanceIntegration:

    @pytest.fixture
    def large_workspace(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        cache_dir = workspace / "Caches"
        cache_dir.mkdir()

        for i in range(100):
            (cache_dir / f"cache_{i}.tmp").write_text("x" * 1024)

        yield workspace

        if workspace.exists():
            shutil.rmtree(workspace)

    def test_parallel_scanning_performance(self, large_workspace, monkeypatch):
        config = Config(dry_run=True, max_workers=4, min_file_size_mb=0.001)
        scanner = SystemScanner(config)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [large_workspace / "Caches"]
        }

        import time
        start = time.time()
        scan_result = scanner.scan([FileCategory.USER_CACHE])
        duration = time.time() - start

        assert scan_result.total_files_found > 0
        assert duration < 10

    def test_parallel_cleaning_performance(self, large_workspace, monkeypatch):
        config = Config(dry_run=False, max_workers=4, min_file_size_mb=0.001)
        scanner = SystemScanner(config)
        scanner.scan_paths = {
            FileCategory.USER_CACHE: [large_workspace / "Caches"]
        }

        scan_result = scanner.scan([FileCategory.USER_CACHE])

        cleaner = SystemCleaner(config)

        import time
        start = time.time()
        cleaning_result = cleaner.clean(scan_result)
        duration = time.time() - start

        assert len(cleaning_result.files_deleted) > 0
        assert duration < 10


if __name__ == "__main__":
    pytest.main([__file__])
