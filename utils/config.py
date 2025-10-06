"""
Configuration management for macOS Cleaner
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field


class ConfigValidationError(ValueError):
    pass


@dataclass
class Config:
    """Application configuration."""

    # Cleaning settings
    dry_run: bool = False
    enable_backup: bool = True
    verify_cleaning: bool = True
    remove_empty_dirs: bool = True
    max_workers: int = 4

    # Scan settings
    scan_hidden_files: bool = False
    follow_symlinks: bool = False
    max_file_age_days: int = 180
    min_file_size_mb: float = 0.1
    large_file_threshold_mb: float = 100.0

    # Optimization settings
    optimize_memory: bool = True
    flush_dns: bool = True
    rebuild_spotlight: bool = False
    manage_startup_items: bool = True

    # Backup settings
    backup_dir: Path = field(default_factory=lambda: Path.home() / ".macos-cleaner" / "backups")
    backup_retention_days: int = 7
    compress_backups: bool = True

    # UI settings
    confirm_operations: bool = True
    show_file_details: bool = True
    max_files_display: int = 50

    # Safety settings
    protected_extensions: List[str] = field(default_factory=lambda: [
        '.app', '.framework', '.dylib', '.so', '.bundle',
        '.kext', '.plugin', '.prefPane', '.qlgenerator'
    ])

    protected_directories: List[str] = field(default_factory=lambda: [
        '/System', '/Library/Extensions', '/usr/bin', '/usr/sbin',
        '/Applications', '/private/etc'
    ])

    def __post_init__(self) -> None:
        if isinstance(self.backup_dir, str):
            self.backup_dir = Path(self.backup_dir)
        self.validate()

    def validate(self) -> None:
        errors: List[str] = []

        if self.max_workers <= 0:
            errors.append("max_workers must be positive")
        if self.max_workers > 32:
            errors.append("max_workers too high (max 32)")

        if self.backup_retention_days < 0:
            errors.append("backup_retention_days cannot be negative")

        if self.min_file_size_mb < 0:
            errors.append("min_file_size_mb cannot be negative")

        if self.large_file_threshold_mb <= 0:
            errors.append("large_file_threshold_mb must be positive")

        if self.max_file_age_days < 0:
            errors.append("max_file_age_days cannot be negative")

        if self.max_files_display < 1:
            errors.append("max_files_display must be at least 1")

        if not self.backup_dir.parent.exists():
            errors.append(f"backup_dir parent directory does not exist: {self.backup_dir.parent}")

        if errors:
            raise ConfigValidationError("; ".join(errors))

    @classmethod
    def load_from_file(cls, config_file: Path) -> 'Config':
        """Load configuration from JSON file."""
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)

                # Handle Path conversion
                if 'backup_dir' in data:
                    data['backup_dir'] = Path(data['backup_dir'])

                return cls(**data)

            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading config: {e}")

        return cls()

    def save_to_file(self, config_file: Path):
        """Save configuration to JSON file."""
        config_file.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(self)
        # Convert Path to string for JSON serialization
        data['backup_dir'] = str(data['backup_dir'])

        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def update(self, **kwargs):
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_safe_categories(self) -> list:
        """Get categories that are safe to clean automatically."""
        from models.scan_result import FileCategory

        return [
            FileCategory.SYSTEM_CACHE,
            FileCategory.USER_CACHE,
            FileCategory.BROWSER_CACHE,
            FileCategory.TEMPORARY_FILES,
            FileCategory.LOG_FILES,
            FileCategory.TRASH,
        ]

    def is_protected_path(self, path: Path) -> bool:
        """Check if a path is protected."""
        path_str = str(path).lower()

        # Check protected directories
        for protected in self.protected_directories:
            if path_str.startswith(protected.lower()):
                return True

        # Check protected extensions
        if path.suffix.lower() in self.protected_extensions:
            return True

        return False

    def get_scan_filters(self) -> Dict[str, Any]:
        """Get filters for scanning."""
        return {
            'min_size': self.min_file_size_mb * 1024 * 1024,
            'max_age_days': self.max_file_age_days,
            'include_hidden': self.scan_hidden_files,
            'follow_symlinks': self.follow_symlinks,
        }


# Default configuration file location
DEFAULT_CONFIG_FILE = Path.home() / ".macos-cleaner" / "config.json"


def get_default_config() -> Config:
    """Get default configuration."""
    return Config()


def load_config(config_file: Optional[Path] = None) -> Config:
    """Load configuration from file or create default."""
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE

    config = Config.load_from_file(config_file)

    # Save default config if file doesn't exist
    if not config_file.exists():
        config.save_to_file(config_file)

    return config