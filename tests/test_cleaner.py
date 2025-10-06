import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from core.cleaner import SystemCleaner
from models.scan_result import FileInfo, CategoryResult, ScanResult, FileCategory, CleaningPriority
from utils.config import Config


class TestSystemCleaner:

    @pytest.fixture
    def config(self):
        return Config(
            dry_run=True,
            enable_backup=False,
            max_workers=2
        )

    @pytest.fixture
    def cleaner(self, config):
        return SystemCleaner(config)

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

    def test_cleaner_initialization(self, cleaner):
        assert cleaner is not None
        assert cleaner.config is not None
        assert cleaner.dry_run is True
        assert len(cleaner.protected_paths) > 0

    def test_is_safe_to_delete_protected_paths(self, cleaner):
        system_file = Path("/System/Library/test.txt")
        assert cleaner._is_safe_to_delete(system_file) is False

        usr_file = Path("/usr/bin/test")
        assert cleaner._is_safe_to_delete(usr_file) is False

    def test_is_safe_to_delete_user_files(self, cleaner, temp_dir):
        user_cache = temp_dir / "cache.tmp"
        user_cache.touch()
        assert cleaner._is_safe_to_delete(user_cache) is True

    def test_clean_file_dry_run(self, cleaner, temp_dir):
        test_file = temp_dir / "test.tmp"
        test_file.write_text("test content")

        file_info = FileInfo(
            path=test_file,
            size=1024,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.TEMPORARY_FILES,
            priority=CleaningPriority.MEDIUM
        )

        from models.scan_result import CleaningResult
        result = CleaningResult()

        success = cleaner._clean_file(file_info, result)

        assert success is True
        assert test_file.exists()
        assert len(result.files_deleted) == 1

    def test_clean_file_actual_deletion(self, temp_dir):
        config = Config(dry_run=False, enable_backup=False)
        cleaner = SystemCleaner(config)

        test_file = temp_dir / "test.tmp"
        test_file.write_text("test content")

        file_info = FileInfo(
            path=test_file,
            size=1024,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.TEMPORARY_FILES,
            priority=CleaningPriority.MEDIUM
        )

        from models.scan_result import CleaningResult
        result = CleaningResult()

        success = cleaner._clean_file(file_info, result)

        assert success is True
        assert not test_file.exists()

    def test_clean_nonexistent_file(self, cleaner, temp_dir):
        nonexistent = temp_dir / "nonexistent.tmp"

        file_info = FileInfo(
            path=nonexistent,
            size=1024,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.TEMPORARY_FILES,
            priority=CleaningPriority.MEDIUM
        )

        from models.scan_result import CleaningResult
        result = CleaningResult()

        success = cleaner._clean_file(file_info, result)
        assert success is False

    def test_clean_directory(self, temp_dir):
        config = Config(dry_run=False, enable_backup=False)
        cleaner = SystemCleaner(config)

        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        file_info = FileInfo(
            path=test_dir,
            size=1024,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.USER_CACHE,
            priority=CleaningPriority.HIGH
        )

        from models.scan_result import CleaningResult
        result = CleaningResult()

        success = cleaner._clean_file(file_info, result)

        assert success is True
        assert not test_dir.exists()

    def test_remove_empty_directory(self, temp_dir):
        config = Config(dry_run=False, remove_empty_dirs=True)
        cleaner = SystemCleaner(config)

        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        success = cleaner._remove_empty_directory(empty_dir)
        assert success is True
        assert not empty_dir.exists()

    def test_remove_nonempty_directory(self, temp_dir):
        config = Config(dry_run=False, remove_empty_dirs=True)
        cleaner = SystemCleaner(config)

        nonempty_dir = temp_dir / "nonempty"
        nonempty_dir.mkdir()
        (nonempty_dir / "file.txt").write_text("content")

        success = cleaner._remove_empty_directory(nonempty_dir)
        assert success is False
        assert nonempty_dir.exists()

    def test_clean_scan_result(self, cleaner, temp_dir):
        test_file1 = temp_dir / "file1.tmp"
        test_file2 = temp_dir / "file2.tmp"
        test_file1.write_text("content1")
        test_file2.write_text("content2")

        category_result = CategoryResult(
            category=FileCategory.TEMPORARY_FILES,
            priority=CleaningPriority.MEDIUM
        )

        file_info1 = FileInfo(
            path=test_file1,
            size=100,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.TEMPORARY_FILES,
            priority=CleaningPriority.MEDIUM
        )

        file_info2 = FileInfo(
            path=test_file2,
            size=200,
            modified_time=datetime.now(),
            accessed_time=datetime.now(),
            category=FileCategory.TEMPORARY_FILES,
            priority=CleaningPriority.MEDIUM
        )

        category_result.add_file(file_info1)
        category_result.add_file(file_info2)

        scan_result = ScanResult()
        scan_result.add_category_result(category_result)

        cleaning_result = cleaner.clean(scan_result)

        assert cleaning_result is not None
        assert len(cleaning_result.files_deleted) == 2
        assert cleaning_result.space_freed == 300

    def test_empty_trash_dry_run(self, cleaner, temp_dir, monkeypatch):
        monkeypatch.setattr(Path, 'home', lambda: temp_dir)

        trash_dir = temp_dir / ".Trash"
        trash_dir.mkdir()
        (trash_dir / "file1.txt").write_text("trash1")
        (trash_dir / "file2.txt").write_text("trash2")

        result = cleaner.empty_trash()

        assert result is not None
        assert trash_dir.exists()
        assert len(list(trash_dir.iterdir())) == 2

    def test_empty_trash_actual(self, temp_dir, monkeypatch):
        config = Config(dry_run=False)
        cleaner = SystemCleaner(config)
        monkeypatch.setattr(Path, 'home', lambda: temp_dir)

        trash_dir = temp_dir / ".Trash"
        trash_dir.mkdir()
        (trash_dir / "file1.txt").write_text("trash1")
        (trash_dir / "file2.txt").write_text("trash2")

        result = cleaner.empty_trash()

        assert result is not None
        assert trash_dir.exists()
        assert len(list(trash_dir.iterdir())) == 0

    def test_verify_cleaning(self, cleaner, temp_dir):
        from models.scan_result import CleaningResult
        result = CleaningResult()

        test_file = temp_dir / "deleted.txt"
        test_file.write_text("content")
        result.add_deleted_file(test_file, 100)

        existing_file = temp_dir / "existing.txt"
        existing_file.write_text("content")
        result.add_deleted_file(existing_file, 100)

        test_file.unlink()

        verification = cleaner.verify_cleaning(result)

        assert verification['verified_deleted'] == 1
        assert len(verification['still_exists']) == 1

    def test_group_files_by_directory(self, cleaner, temp_dir):
        dir1 = temp_dir / "dir1"
        dir2 = temp_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        file1 = dir1 / "file1.txt"
        file2 = dir1 / "file2.txt"
        file3 = dir2 / "file3.txt"

        file1.touch()
        file2.touch()
        file3.touch()

        files = [
            FileInfo(path=file1, size=100, modified_time=datetime.now(),
                    accessed_time=datetime.now(), category=FileCategory.USER_CACHE,
                    priority=CleaningPriority.HIGH),
            FileInfo(path=file2, size=200, modified_time=datetime.now(),
                    accessed_time=datetime.now(), category=FileCategory.USER_CACHE,
                    priority=CleaningPriority.HIGH),
            FileInfo(path=file3, size=300, modified_time=datetime.now(),
                    accessed_time=datetime.now(), category=FileCategory.USER_CACHE,
                    priority=CleaningPriority.HIGH)
        ]

        groups = cleaner._group_files_by_directory(files)

        assert len(groups) == 2
        assert len(groups[dir1]) == 2
        assert len(groups[dir2]) == 1


if __name__ == "__main__":
    pytest.main([__file__])
