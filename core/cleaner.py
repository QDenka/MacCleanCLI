"""
System cleaner module for safely removing files
"""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional, Set, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.scan_result import (
    FileInfo, CategoryResult, CleaningResult,
    FileCategory, ScanResult
)
from utils.logger import get_logger
from utils.config import Config
from utils.backup import BackupManager
from utils.exceptions import CleaningError, ProtectedPathError, InsufficientPermissionsError

logger = get_logger(__name__)


class SystemCleaner:
    """Safely cleans macOS system files."""

    def __init__(self, config: Config):
        self.config = config
        self.backup_manager = BackupManager(config) if config.enable_backup else None
        self.dry_run = config.dry_run
        self.max_workers = config.max_workers or 4

        # Files/directories that should never be deleted
        self.protected_paths = {
            Path("/System"),
            Path("/Library/Extensions"),
            Path("/usr"),
            Path("/bin"),
            Path("/sbin"),
            Path("/private/etc"),
            Path("/Applications"),
            Path.home() / "Library" / "Application Support" / "AddressBook",
            Path.home() / "Library" / "Application Support" / "Calendar",
            Path.home() / "Library" / "Application Support" / "Mail",
        }

    def clean(self, scan_result: ScanResult,
              categories: Optional[Set[FileCategory]] = None,
              progress_callback: Optional[Callable[[float, str], None]] = None) -> CleaningResult:
        """
        Clean files based on scan results.

        Args:
            scan_result: Results from system scan
            categories: Specific categories to clean, or None for all
            progress_callback: Callback for progress updates (percentage, message)

        Returns:
            CleaningResult with details of cleaned files
        """
        cleaning_result = CleaningResult()

        if categories is None:
            categories = set(scan_result.categories.keys())

        logger.info(f"Starting cleaning for {len(categories)} categories")

        # Calculate total files to process
        total_files = sum(
            len(result.files)
            for cat, result in scan_result.categories.items()
            if cat in categories
        )

        if total_files == 0:
            logger.info("No files to clean")
            cleaning_result.finish()
            return cleaning_result

        processed_files = 0

        # Clean each category
        for category in categories:
            if category not in scan_result.categories:
                continue

            category_result = scan_result.categories[category]
            cleaning_result.categories_cleaned.add(category)

            logger.info(f"Cleaning {category.name}: {len(category_result.files)} files")

            # Group files by directory for efficient cleaning
            files_by_dir = self._group_files_by_directory(category_result.files)

            # Clean files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                for directory, files in files_by_dir.items():
                    future = executor.submit(
                        self._clean_directory_files,
                        directory,
                        files,
                        cleaning_result
                    )
                    futures.append(future)

                # Process results
                for future in as_completed(futures):
                    try:
                        cleaned_count = future.result()
                        processed_files += cleaned_count

                        if progress_callback:
                            progress = (processed_files / total_files) * 100
                            progress_callback(
                                progress,
                                f"Cleaned {processed_files}/{total_files} files"
                            )

                    except (CleaningError, OSError, IOError) as e:
                        logger.error(f"Error in cleaning task: {e}")
                    except PermissionError as e:
                        logger.warning(f"Permission denied in cleaning task: {e}")

        cleaning_result.finish()

        logger.info(
            f"Cleaning completed: {len(cleaning_result.files_deleted)} files deleted, "
            f"{cleaning_result.space_freed_gb:.2f} GB freed"
        )

        return cleaning_result

    def _group_files_by_directory(self, files: List[FileInfo]) -> dict[Path, List[FileInfo]]:
        """Group files by their parent directory."""
        groups = {}

        for file_info in files:
            directory = file_info.path.parent
            if directory not in groups:
                groups[directory] = []
            groups[directory].append(file_info)

        return groups

    def _clean_directory_files(self, directory: Path, files: List[FileInfo],
                               result: CleaningResult) -> int:
        """Clean files in a specific directory."""
        cleaned_count = 0

        for file_info in files:
            if self._clean_file(file_info, result):
                cleaned_count += 1

        # Try to remove empty directories
        if self.config.remove_empty_dirs:
            self._remove_empty_directory(directory)

        return cleaned_count

    def _clean_file(self, file_info: FileInfo, result: CleaningResult) -> bool:
        """
        Clean a single file.

        Returns:
            True if file was successfully cleaned
        """
        file_path = file_info.path

        # Safety checks
        if not self._is_safe_to_delete(file_path):
            logger.warning(f"Skipping protected file: {file_path}")
            return False

        if not file_path.exists():
            logger.debug(f"File no longer exists: {file_path}")
            return False

        try:
            # Create backup if enabled
            if self.backup_manager and file_info.category != FileCategory.TRASH:
                self.backup_manager.backup_file(file_path)

            # Delete or simulate deletion
            if self.dry_run:
                logger.info(f"[DRY RUN] Would delete: {file_path}")
            else:
                if file_path.is_dir():
                    shutil.rmtree(file_path, ignore_errors=False)
                else:
                    file_path.unlink()

                logger.debug(f"Deleted: {file_path}")

            result.add_deleted_file(file_path, file_info.size)
            return True

        except (PermissionError, InsufficientPermissionsError):
            error_msg = f"Permission denied: {file_path}"
            logger.error(error_msg)
            result.add_failed_file(file_path, error_msg)

        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.debug(error_msg)
            result.add_failed_file(file_path, error_msg)

        except (OSError, IOError) as e:
            error_msg = f"Failed to delete {file_path}: {str(e)}"
            logger.error(error_msg)
            result.add_failed_file(file_path, error_msg)

        return False

    def _is_safe_to_delete(self, path: Path) -> bool:
        """Check if a path is safe to delete."""
        # Check against protected paths
        for protected in self.protected_paths:
            try:
                if path.is_relative_to(protected):
                    return False
            except ValueError:
                # Not relative to this path
                continue

        # Check if path is in protected list
        if path in self.protected_paths:
            return False

        # Additional safety checks
        path_str = str(path).lower()

        # Never delete system files
        if any(danger in path_str for danger in ['/system/', '/library/extensions']):
            return False

        # Check file permissions
        try:
            # Verify we have write permission
            if not os.access(path.parent, os.W_OK):
                return False
        except (OSError, IOError):
            return False

        return True

    def _remove_empty_directory(self, directory: Path) -> bool:
        """Remove directory if empty."""
        if not directory.exists() or not directory.is_dir():
            return False

        # Don't remove protected directories
        if not self._is_safe_to_delete(directory):
            return False

        try:
            # Check if directory is empty
            if not any(directory.iterdir()):
                if not self.dry_run:
                    directory.rmdir()
                logger.debug(f"Removed empty directory: {directory}")
                return True
        except (OSError, IOError) as e:
            logger.debug(f"Could not remove directory {directory}: {e}")
        except PermissionError as e:
            logger.warning(f"Permission denied removing directory {directory}: {e}")

        return False

    def empty_trash(self) -> CleaningResult:
        """Empty the system trash."""
        result = CleaningResult()
        result.categories_cleaned.add(FileCategory.TRASH)

        trash_path = Path.home() / ".Trash"

        if not trash_path.exists():
            result.finish()
            return result

        logger.info("Emptying trash")

        try:
            # Get trash contents
            trash_size = 0
            trash_files = []

            for item in trash_path.iterdir():
                try:
                    if item.is_file():
                        trash_size += item.stat().st_size
                        trash_files.append(item)
                    elif item.is_dir():
                        # Calculate directory size
                        dir_size = sum(
                            f.stat().st_size for f in item.rglob("*") if f.is_file()
                        )
                        trash_size += dir_size
                        trash_files.append(item)
                except (OSError, IOError):
                    logger.debug(f"Could not process trash item {item}")
                    continue

            # Empty trash
            if not self.dry_run:
                for item in trash_path.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except PermissionError as e:
                        logger.warning(f"Permission denied deleting {item}: {e}")
                    except (OSError, IOError) as e:
                        logger.debug(f"Failed to delete {item}: {e}")

            # Record results
            for item in trash_files:
                result.add_deleted_file(item, 0)  # Size already calculated

            result.space_freed = trash_size

        except (OSError, IOError) as e:
            logger.error(f"Failed to empty trash: {e}")
            result.add_failed_file(trash_path, str(e))
        except PermissionError as e:
            logger.error(f"Permission denied emptying trash: {e}")
            result.add_failed_file(trash_path, str(e))

        result.finish()
        return result

    def clean_memory_pressure(self) -> bool:
        """
        Release memory pressure by purging inactive memory.
        Note: Requires sudo privileges.
        """
        try:
            if not self.dry_run:
                import subprocess
                # This command purges disk cache and inactive memory
                subprocess.run(['sudo', 'purge'], check=True, capture_output=True)
                logger.info("Successfully purged inactive memory")
            else:
                logger.info("[DRY RUN] Would purge inactive memory")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to purge memory: {e}")
            return False
        except Exception as e:
            logger.error(f"Error purging memory: {e}")
            return False

    def verify_cleaning(self, cleaning_result: CleaningResult) -> dict:
        """Verify that files were actually deleted."""
        verification = {
            'verified_deleted': 0,
            'still_exists': [],
            'verification_errors': []
        }

        for file_path in cleaning_result.files_deleted:
            try:
                if not file_path.exists():
                    verification['verified_deleted'] += 1
                else:
                    verification['still_exists'].append(str(file_path))
            except (OSError, IOError) as e:
                verification['verification_errors'].append(
                    f"{file_path}: {str(e)}"
                )

        return verification


class SafeCleaningContext:
    """Context manager for safe cleaning operations."""

    def __init__(self, cleaner: SystemCleaner, scan_result: ScanResult):
        self.cleaner = cleaner
        self.scan_result = scan_result
        self.original_dry_run = cleaner.dry_run

    def __enter__(self):
        """Enter cleaning context."""
        logger.info("Starting safe cleaning context")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit cleaning context."""
        # Restore original settings
        self.cleaner.dry_run = self.original_dry_run

        if exc_type is not None:
            logger.error(f"Error in cleaning context: {exc_val}")

        logger.info("Exiting safe cleaning context")
        return False

    def preview_cleaning(self, categories: Optional[Set[FileCategory]] = None) -> CleaningResult:
        """Preview what would be cleaned without actually deleting."""
        self.cleaner.dry_run = True
        return self.cleaner.clean(self.scan_result, categories)

    def execute_cleaning(self, categories: Optional[Set[FileCategory]] = None,
                         progress_callback: Optional[Callable[[float, str], None]] = None) -> CleaningResult:
        """Execute actual cleaning."""
        self.cleaner.dry_run = self.original_dry_run
        return self.cleaner.clean(self.scan_result, categories, progress_callback)