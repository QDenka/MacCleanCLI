"""
Data models for scan results and file information
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set
from enum import Enum, auto
from datetime import datetime


class FileCategory(Enum):
    """Categories of files that can be cleaned."""
    SYSTEM_CACHE = auto()
    USER_CACHE = auto()
    BROWSER_CACHE = auto()
    TEMPORARY_FILES = auto()
    LOG_FILES = auto()
    DOWNLOADS = auto()
    TRASH = auto()
    DUPLICATES = auto()
    LARGE_FILES = auto()
    OLD_FILES = auto()
    APP_LEFTOVERS = auto()
    MEMORY = auto()
    STARTUP_ITEMS = auto()
    XCODE_DERIVED_DATA = auto()
    XCODE_ARCHIVES = auto()
    DOCKER_DATA = auto()
    HOMEBREW_CACHE = auto()
    NODE_MODULES = auto()
    PYTHON_CACHE = auto()


class CleaningPriority(Enum):
    """Priority levels for cleaning suggestions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    size: int
    modified_time: datetime
    accessed_time: datetime
    category: FileCategory
    priority: CleaningPriority
    is_safe_to_delete: bool = True
    description: str = ""

    @property
    def size_mb(self) -> float:
        """Get size in megabytes."""
        return self.size / (1024 * 1024)

    @property
    def age_days(self) -> int:
        """Get file age in days."""
        return (datetime.now() - self.modified_time).days


@dataclass
class CategoryResult:
    """Results for a specific category."""
    category: FileCategory
    files: List[FileInfo] = field(default_factory=list)
    total_size: int = 0
    priority: CleaningPriority = CleaningPriority.MEDIUM
    description: str = ""

    def add_file(self, file_info: FileInfo):
        """Add a file to this category."""
        self.files.append(file_info)
        self.total_size += file_info.size

    @property
    def file_count(self) -> int:
        """Get number of files in this category."""
        return len(self.files)

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size / (1024 * 1024)

    @property
    def total_size_gb(self) -> float:
        """Get total size in gigabytes."""
        return self.total_size / (1024 * 1024 * 1024)


@dataclass
class ScanResult:
    """Complete scan results."""
    scan_time: datetime = field(default_factory=datetime.now)
    categories: Dict[FileCategory, CategoryResult] = field(default_factory=dict)
    total_files_found: int = 0
    total_size_found: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)

    def add_category_result(self, result: CategoryResult):
        """Add results for a category."""
        self.categories[result.category] = result
        self.total_files_found += result.file_count
        self.total_size_found += result.total_size

    @property
    def total_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size_found / (1024 * 1024)

    @property
    def total_size_gb(self) -> float:
        """Get total size in gigabytes."""
        return self.total_size_found / (1024 * 1024 * 1024)

    def get_categories_by_priority(self, priority: CleaningPriority) -> List[CategoryResult]:
        """Get all categories with specific priority."""
        return [
            result for result in self.categories.values()
            if result.priority == priority
        ]

    def get_safe_to_clean_size(self) -> int:
        """Get the total size of files safe to clean."""
        total = 0
        for category in self.categories.values():
            for file in category.files:
                if file.is_safe_to_delete:
                    total += file.size
        return total


@dataclass
class CleaningResult:
    """Results of cleaning operation."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    files_deleted: List[Path] = field(default_factory=list)
    files_failed: List[tuple[Path, str]] = field(default_factory=list)
    space_freed: int = 0
    categories_cleaned: Set[FileCategory] = field(default_factory=set)

    def add_deleted_file(self, path: Path, size: int):
        """Record a successfully deleted file."""
        self.files_deleted.append(path)
        self.space_freed += size

    def add_failed_file(self, path: Path, error: str):
        """Record a file that failed to delete."""
        self.files_failed.append((path, error))

    def finish(self):
        """Mark cleaning as finished."""
        self.end_time = datetime.now()

    @property
    def duration(self) -> float:
        """Get cleaning duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def space_freed_mb(self) -> float:
        """Get space freed in megabytes."""
        return self.space_freed / (1024 * 1024)

    @property
    def space_freed_gb(self) -> float:
        """Get space freed in gigabytes."""
        return self.space_freed / (1024 * 1024 * 1024)

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        total = len(self.files_deleted) + len(self.files_failed)
        if total == 0:
            return 100.0
        return (len(self.files_deleted) / total) * 100


@dataclass
class SystemInfo:
    """System information."""
    total_disk_space: int
    used_disk_space: int
    free_disk_space: int
    total_memory: int
    used_memory: int
    free_memory: int
    cpu_usage: float
    macos_version: str

    @property
    def disk_usage_percent(self) -> float:
        """Get disk usage percentage."""
        return (self.used_disk_space / self.total_disk_space) * 100

    @property
    def memory_usage_percent(self) -> float:
        """Get memory usage percentage."""
        return (self.used_memory / self.total_memory) * 100