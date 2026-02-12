"""
System scanner module for identifying files to clean
"""

import os
import time
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from models.scan_result import (
    FileInfo, CategoryResult, ScanResult,
    FileCategory, CleaningPriority, SystemInfo
)
from utils.logger import get_logger
from utils.config import Config
from utils.exceptions import ScanError, InsufficientPermissionsError


logger = get_logger(__name__)


class SystemScanner:
    """Scans macOS system for cleanable files."""

    def __init__(self, config: Config):
        self.config = config
        self.home_path = Path.home()
        self.library_path = self.home_path / "Library"
        self._stat_cache: Dict[Path, os.stat_result] = {}
        self._result_lock = Lock()

        # Define scan paths for each category
        self.scan_paths = {
            FileCategory.SYSTEM_CACHE: [
                Path("/Library/Caches"),
                Path("/System/Library/Caches"),
                self.library_path / "Caches",
            ],
            FileCategory.USER_CACHE: [
                self.library_path / "Caches",
                self.home_path / ".cache",
            ],
            FileCategory.BROWSER_CACHE: [
                self.library_path / "Caches" / "com.apple.Safari",
                self.library_path / "Caches" / "com.apple.Safari.SafeBrowsing",
                self.library_path / "Caches" / "com.apple.SafariServices",
                self.library_path / "Caches" / "Google" / "Chrome",
                self.library_path / "Caches" / "Google" / "Chrome" / "Default" / "Cache",
                self.library_path / "Caches" / "Google" / "Chrome Canary",
                self.library_path / "Caches" / "Firefox" / "Profiles",
                self.library_path / "Caches" / "com.brave.Browser",
                self.library_path / "Caches" / "com.brave.Browser.nightly",
                self.library_path / "Caches" / "com.microsoft.edgemac",
                self.library_path / "Caches" / "com.operasoftware.Opera",
                self.library_path / "Caches" / "com.vivaldi.Vivaldi",
                # Alternative Chrome paths
                self.home_path / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Cache",
                self.home_path / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Code Cache",
                # Firefox alternative paths
                self.home_path / "Library" / "Application Support" / "Firefox" / "Profiles",
                # Brave alternative paths
                self.home_path / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "Default" / "Cache",
                # Edge alternative paths
                self.home_path / "Library" / "Application Support" / "Microsoft Edge" / "Default" / "Cache",
            ],
            FileCategory.TEMPORARY_FILES: [
                Path("/tmp"),
                Path("/var/tmp"),
                self.home_path / "Downloads" / "*.tmp",
            ],
            FileCategory.LOG_FILES: [
                Path("/var/log"),
                self.library_path / "Logs",
                self.home_path / ".local" / "share" / "logs",
            ],
            FileCategory.DOWNLOADS: [
                self.home_path / "Downloads",
            ],
            FileCategory.TRASH: [
                self.home_path / ".Trash",
            ],
            FileCategory.APP_LEFTOVERS: [
                self.library_path / "Application Support",
                self.library_path / "Preferences",
                self.library_path / "Saved Application State",
            ],
            FileCategory.XCODE_DERIVED_DATA: [
                self.library_path / "Developer" / "Xcode" / "DerivedData",
            ],
            FileCategory.XCODE_ARCHIVES: [
                self.library_path / "Developer" / "Xcode" / "Archives",
                self.library_path / "Developer" / "Xcode" / "iOS DeviceSupport",
            ],
            FileCategory.DOCKER_DATA: [
                self.home_path / ".docker",
                self.library_path / "Containers" / "com.docker.docker",
            ],
            FileCategory.HOMEBREW_CACHE: [
                self.library_path / "Caches" / "Homebrew",
                Path("/usr/local/Homebrew/Library/Homebrew/vendor/cache"),
            ],
            FileCategory.NODE_MODULES: [
                self.home_path / "node_modules",
            ],
            FileCategory.PYTHON_CACHE: [
                self.home_path / ".cache" / "pip",
                self.library_path / "Caches" / "pip",
            ],
        }

        # File extensions to consider for cleaning
        self.cleanable_extensions = {
            ".tmp", ".temp", ".cache", ".log", ".old",
            ".bak", ".backup", ".crash", ".dump"
        }

    def _get_installed_browsers(self) -> Dict[str, Path]:
        """Get installed browsers and their app paths."""
        browsers = {
            'Safari': Path('/Applications/Safari.app'),
            'Google Chrome': Path('/Applications/Google Chrome.app'),
            'Firefox': Path('/Applications/Firefox.app'),
            'Brave Browser': Path('/Applications/Brave Browser.app'),
            'Microsoft Edge': Path('/Applications/Microsoft Edge.app'),
            'Opera': Path('/Applications/Opera.app'),
            'Vivaldi': Path('/Applications/Vivaldi.app'),
        }

        # Check user Applications folder too
        user_apps = Path.home() / 'Applications'
        if user_apps.exists():
            for browser, system_path in list(browsers.items()):
                if not system_path.exists():
                    user_path = user_apps / system_path.name
                    if user_path.exists():
                        browsers[browser] = user_path

        # Return only installed browsers
        return {name: path for name, path in browsers.items() if path.exists()}

    def _get_stat(self, path: Path) -> os.stat_result:
        if path not in self._stat_cache:
            self._stat_cache[path] = path.stat()
        return self._stat_cache[path]

    def scan(self, categories: Optional[List[FileCategory]] = None) -> ScanResult:
        """
        Scan system for cleanable files.

        Args:
            categories: Specific categories to scan, or None for all

        Returns:
            ScanResult with found files
        """
        start_time = time.time()
        result = ScanResult()

        if categories is None:
            categories = list(FileCategory)

        logger.info(f"Starting system scan for {len(categories)} categories")
        self._stat_cache.clear()

        # Scan each category
        for category in categories:
            if category in self.scan_paths:
                try:
                    category_result = self._scan_category(category)
                    result.add_category_result(category_result)
                except (ScanError, OSError, IOError) as e:
                    logger.error(f"Error scanning {category.name}: {e}")
                    result.errors.append(f"Failed to scan {category.name}: {str(e)}")

        # Scan for duplicates if requested
        if FileCategory.DUPLICATES in categories:
            try:
                duplicates_result = self._scan_duplicates()
                result.add_category_result(duplicates_result)
            except (ScanError, OSError, IOError) as e:
                logger.error(f"Error scanning duplicates: {e}")
                result.errors.append(f"Failed to scan duplicates: {str(e)}")

        # Scan for large files if requested
        if FileCategory.LARGE_FILES in categories:
            try:
                large_files_result = self._scan_large_files()
                result.add_category_result(large_files_result)
            except (ScanError, OSError, IOError) as e:
                logger.error(f"Error scanning large files: {e}")
                result.errors.append(f"Failed to scan large files: {str(e)}")

        # Scan for old files if requested
        if FileCategory.OLD_FILES in categories:
            try:
                old_files_result = self._scan_old_files()
                result.add_category_result(old_files_result)
            except (ScanError, OSError, IOError) as e:
                logger.error(f"Error scanning old files: {e}")
                result.errors.append(f"Failed to scan old files: {str(e)}")

        result.scan_duration = time.time() - start_time
        logger.info(f"Scan completed in {result.scan_duration:.2f} seconds")

        return result

    def _scan_category(self, category: FileCategory) -> CategoryResult:
        """Scan a specific category."""
        result = CategoryResult(
            category=category,
            priority=self._get_category_priority(category),
            description=self._get_category_description(category)
        )

        paths = self.scan_paths.get(category, [])
        scanned_paths = []

        for scan_path in paths:
            if not scan_path.exists():
                logger.debug(f"Path does not exist: {scan_path}")
                continue

            try:
                if scan_path.is_dir():
                    # Check if we have read permission
                    if not os.access(scan_path, os.R_OK):
                        logger.warning(f"No read permission for: {scan_path}")
                        continue

                    self._scan_directory(scan_path, category, result)
                    scanned_paths.append(scan_path.name)
                else:
                    # Handle glob patterns
                    for path in scan_path.parent.glob(scan_path.name):
                        if path.is_file():
                            file_info = self._analyze_file(path, category)
                            if file_info:
                                self._add_file_safe(result, file_info)
                                scanned_paths.append(path.name)
            except (PermissionError, InsufficientPermissionsError) as e:
                logger.warning(f"Permission denied: {scan_path}")
            except (OSError, IOError) as e:
                logger.error(f"Error scanning {scan_path}: {e}")
            except FileNotFoundError:
                logger.debug(f"File not found during scan: {scan_path}")

        # Update description with scanned browsers for browser cache
        if category == FileCategory.BROWSER_CACHE and scanned_paths:
            browsers = set()
            for path in scanned_paths:
                if 'safari' in path.lower():
                    browsers.add('Safari')
                elif 'chrome' in path.lower():
                    browsers.add('Chrome')
                elif 'firefox' in path.lower():
                    browsers.add('Firefox')
                elif 'brave' in path.lower():
                    browsers.add('Brave')
                elif 'edge' in path.lower():
                    browsers.add('Edge')
                elif 'opera' in path.lower():
                    browsers.add('Opera')
                elif 'vivaldi' in path.lower():
                    browsers.add('Vivaldi')

            if browsers:
                result.description = f"Browser cache files from: {', '.join(sorted(browsers))}"
            else:
                result.description = "No browser caches found (check permissions)"

        return result

    def _scan_directory(self, directory: Path, category: FileCategory,
                       result: CategoryResult, max_depth: int = 3):
        """Recursively scan a directory."""
        if max_depth <= 0:
            return

        try:
            # Special handling for Firefox profiles
            if 'Firefox' in str(directory) and directory.name == 'Profiles':
                # Scan each profile directory
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if entry.is_dir() and not entry.name.startswith('.'):
                            # Look for cache directories in Firefox profiles
                            cache_dirs = ['cache2', 'startupCache', 'shader-cache']
                            for cache_name in cache_dirs:
                                cache_path = Path(entry.path) / cache_name
                                if cache_path.exists() and cache_path.is_dir():
                                    self._scan_directory(cache_path, category, result, max_depth - 1)
                return

            subdirs = []
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            # Skip certain system directories
                            if entry.name.startswith('.') and category != FileCategory.USER_CACHE:
                                continue
                            subdirs.append(Path(entry.path))

                        elif entry.is_file():
                            file_info = self._analyze_file(Path(entry.path), category)
                            if file_info:
                                self._add_file_safe(result, file_info)

                    except (PermissionError, OSError):
                        continue

            # Parallel scanning of subdirectories
            if subdirs and max_depth > 1:
                with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                    futures = [
                        executor.submit(self._scan_directory, subdir, category, result, max_depth - 1)
                        for subdir in subdirs
                    ]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except (ScanError, OSError, IOError):
                            continue

        except (PermissionError, OSError):
            logger.warning(f"Cannot access directory: {directory}")

    def _add_file_safe(self, result: CategoryResult, file_info: FileInfo) -> None:
        """Thread-safe add to category result."""
        with self._result_lock:
            self._add_file_safe(result, file_info)

    def _analyze_file(self, file_path: Path, category: FileCategory) -> Optional[FileInfo]:
        """Analyze a file and determine if it should be cleaned."""
        try:
            stat = self._get_stat(file_path)

            # Skip very small files using config threshold
            min_size_bytes = int(self.config.min_file_size_mb * 1024 * 1024)
            if stat.st_size < min_size_bytes:
                return None

            # Check if file matches cleanable criteria
            if not self._is_cleanable(file_path, category):
                return None

            return FileInfo(
                path=file_path,
                size=stat.st_size,
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                accessed_time=datetime.fromtimestamp(stat.st_atime),
                category=category,
                priority=self._get_file_priority(file_path, category),
                is_safe_to_delete=self._is_safe_to_delete(file_path, category),
                description=self._get_file_description(file_path)
            )

        except (OSError, PermissionError):
            return None

    def _is_cleanable(self, file_path: Path, category: FileCategory) -> bool:
        """Check if a file is cleanable based on category and rules."""
        # Category-specific rules
        if category in [FileCategory.SYSTEM_CACHE, FileCategory.USER_CACHE,
                       FileCategory.BROWSER_CACHE]:
            return True

        if category == FileCategory.TEMPORARY_FILES:
            return file_path.suffix.lower() in self.cleanable_extensions

        if category == FileCategory.LOG_FILES:
            return file_path.suffix.lower() in ['.log', '.txt']

        if category == FileCategory.DOWNLOADS:
            # Only old downloads
            stat = self._get_stat(file_path)
            age = datetime.now() - datetime.fromtimestamp(stat.st_mtime)
            return age > timedelta(days=30)

        if category == FileCategory.TRASH:
            return True

        if category == FileCategory.APP_LEFTOVERS:
            # Check if app still exists
            return not self._is_app_installed(file_path)

        if category in [FileCategory.XCODE_DERIVED_DATA, FileCategory.XCODE_ARCHIVES]:
            return True

        if category == FileCategory.DOCKER_DATA:
            return True

        if category == FileCategory.HOMEBREW_CACHE:
            return True

        if category == FileCategory.NODE_MODULES:
            return file_path.name == "node_modules"

        if category == FileCategory.PYTHON_CACHE:
            return file_path.name in ["__pycache__", "pip"] or file_path.suffix == ".pyc"

        return False

    def _is_safe_to_delete(self, file_path: Path, category: FileCategory) -> bool:
        """Determine if a file is safe to delete."""
        # Never delete system-critical files
        critical_paths = [
            "/System", "/Library/Extensions", "/usr/bin", "/usr/sbin"
        ]

        for critical in critical_paths:
            if str(file_path).startswith(critical):
                return False

        # Category-specific safety rules
        if category == FileCategory.SYSTEM_CACHE:
            # Only caches older than 7 days
            stat = self._get_stat(file_path)
            age = datetime.now() - datetime.fromtimestamp(stat.st_atime)
            return age > timedelta(days=7)

        return True

    def _scan_duplicates(self) -> CategoryResult:
        """Scan for duplicate files."""
        result = CategoryResult(
            category=FileCategory.DUPLICATES,
            priority=CleaningPriority.LOW,
            description="Duplicate files taking up extra space"
        )

        # Common directories to check for duplicates
        scan_dirs = [
            self.home_path / "Downloads",
            self.home_path / "Documents",
            self.home_path / "Pictures",
            self.home_path / "Desktop",
        ]

        # Group files by size first (fast)
        files_by_size: Dict[int, List[Path]] = {}
        for directory in scan_dirs:
            if not directory.exists():
                continue
            self._group_files_by_size(directory, files_by_size)

        # Hash only files with same size
        file_hashes: Dict[str, List[Path]] = {}
        for size, paths in files_by_size.items():
            if len(paths) > 1:
                for path in paths:
                    file_hash = self._get_file_hash(path)
                    if file_hash:
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(path)

        # Process duplicates
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                # Keep the oldest file, mark others as duplicates
                paths.sort(key=lambda p: self._get_stat(p).st_mtime)

                for path in paths[1:]:
                    try:
                        stat = self._get_stat(path)
                        file_info = FileInfo(
                            path=path,
                            size=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime),
                            accessed_time=datetime.fromtimestamp(stat.st_atime),
                            category=FileCategory.DUPLICATES,
                            priority=CleaningPriority.LOW,
                            is_safe_to_delete=True,
                            description=f"Duplicate of {paths[0].name}"
                        )
                        self._add_file_safe(result, file_info)
                    except (OSError, PermissionError):
                        continue

        return result

    def _group_files_by_size(self, directory: Path, files_by_size: Dict[int, List[Path]]):
        """Group files by size for faster duplicate detection."""
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    try:
                        size = self._get_stat(item).st_size
                        if size > 1024 * 100:  # > 100KB
                            if size not in files_by_size:
                                files_by_size[size] = []
                            files_by_size[size].append(item)
                    except (OSError, PermissionError):
                        continue
        except (PermissionError, OSError):
            pass

    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate file hash using partial hashing for large files."""
        try:
            file_size = self._get_stat(file_path).st_size
            hasher = hashlib.md5()

            with open(file_path, 'rb') as f:
                # For small files (< 1MB), hash entire file
                if file_size < 1024 * 1024:
                    hasher.update(f.read())
                else:
                    # For large files, hash first 8KB + last 8KB + size
                    chunk_size = 8192
                    hasher.update(f.read(chunk_size))

                    # Seek to end - chunk_size
                    f.seek(max(0, file_size - chunk_size))
                    hasher.update(f.read(chunk_size))

                    # Add size to hash to differentiate files
                    hasher.update(str(file_size).encode())

            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None

    def _scan_large_files(self) -> CategoryResult:
        """Scan for large files."""
        result = CategoryResult(
            category=FileCategory.LARGE_FILES,
            priority=CleaningPriority.OPTIONAL,
            description="Large files that might be unnecessary"
        )

        # Directories to scan for large files
        scan_dirs = [
            self.home_path / "Downloads",
            self.home_path / "Documents",
            self.home_path / "Desktop",
            self.home_path / "Movies",
        ]

        min_size = int(self.config.large_file_threshold_mb * 1024 * 1024)

        for directory in scan_dirs:
            if not directory.exists():
                continue

            try:
                for item in directory.rglob("*"):
                    if item.is_file():
                        try:
                            stat = self._get_stat(item)
                            if stat.st_size >= min_size:
                                file_info = FileInfo(
                                    path=item,
                                    size=stat.st_size,
                                    modified_time=datetime.fromtimestamp(stat.st_mtime),
                                    accessed_time=datetime.fromtimestamp(stat.st_atime),
                                    category=FileCategory.LARGE_FILES,
                                    priority=CleaningPriority.OPTIONAL,
                                    is_safe_to_delete=True,
                                    description=f"Large file ({stat.st_size / (1024**3):.1f} GB)"
                                )
                                self._add_file_safe(result, file_info)
                        except (OSError, PermissionError):
                            continue
            except (PermissionError, OSError):
                continue

        return result

    def _scan_old_files(self) -> CategoryResult:
        """Scan for old files."""
        result = CategoryResult(
            category=FileCategory.OLD_FILES,
            priority=CleaningPriority.OPTIONAL,
            description="Files not accessed in a long time"
        )

        # Directories to scan
        scan_dirs = [
            self.home_path / "Downloads",
            self.home_path / "Desktop",
        ]

        max_age = timedelta(days=180)  # 6 months

        for directory in scan_dirs:
            if not directory.exists():
                continue

            try:
                for item in directory.rglob("*"):
                    if item.is_file():
                        try:
                            stat = self._get_stat(item)
                            age = datetime.now() - datetime.fromtimestamp(stat.st_atime)

                            if age > max_age:
                                file_info = FileInfo(
                                    path=item,
                                    size=stat.st_size,
                                    modified_time=datetime.fromtimestamp(stat.st_mtime),
                                    accessed_time=datetime.fromtimestamp(stat.st_atime),
                                    category=FileCategory.OLD_FILES,
                                    priority=CleaningPriority.OPTIONAL,
                                    is_safe_to_delete=True,
                                    description=f"Not accessed for {age.days} days"
                                )
                                self._add_file_safe(result, file_info)
                        except (OSError, PermissionError):
                            continue
            except (PermissionError, OSError):
                continue

        return result

    def _is_app_installed(self, file_path: Path) -> bool:
        """Check if an application is still installed."""
        # Extract app name from path
        app_name = None

        if "Application Support" in str(file_path):
            # Get the app folder name
            parts = file_path.parts
            idx = parts.index("Application Support")
            if idx + 1 < len(parts):
                app_name = parts[idx + 1]

        if not app_name:
            return True  # Assume installed if can't determine

        # Check common app locations
        app_locations = [
            Path("/Applications"),
            Path.home() / "Applications",
        ]

        for location in app_locations:
            if (location / f"{app_name}.app").exists():
                return True

        return False

    def _get_category_priority(self, category: FileCategory) -> CleaningPriority:
        """Get priority for a category."""
        priority_map = {
            FileCategory.SYSTEM_CACHE: CleaningPriority.HIGH,
            FileCategory.USER_CACHE: CleaningPriority.HIGH,
            FileCategory.BROWSER_CACHE: CleaningPriority.HIGH,
            FileCategory.TEMPORARY_FILES: CleaningPriority.HIGH,
            FileCategory.LOG_FILES: CleaningPriority.MEDIUM,
            FileCategory.TRASH: CleaningPriority.MEDIUM,
            FileCategory.DOWNLOADS: CleaningPriority.LOW,
            FileCategory.APP_LEFTOVERS: CleaningPriority.MEDIUM,
            FileCategory.DUPLICATES: CleaningPriority.LOW,
            FileCategory.LARGE_FILES: CleaningPriority.OPTIONAL,
            FileCategory.OLD_FILES: CleaningPriority.OPTIONAL,
            FileCategory.XCODE_DERIVED_DATA: CleaningPriority.HIGH,
            FileCategory.XCODE_ARCHIVES: CleaningPriority.LOW,
            FileCategory.DOCKER_DATA: CleaningPriority.MEDIUM,
            FileCategory.HOMEBREW_CACHE: CleaningPriority.MEDIUM,
            FileCategory.NODE_MODULES: CleaningPriority.LOW,
            FileCategory.PYTHON_CACHE: CleaningPriority.MEDIUM,
        }
        return priority_map.get(category, CleaningPriority.MEDIUM)

    def _get_category_description(self, category: FileCategory) -> str:
        """Get description for a category."""
        descriptions = {
            FileCategory.SYSTEM_CACHE: "System cache files that can be safely removed",
            FileCategory.USER_CACHE: "User application caches",
            FileCategory.BROWSER_CACHE: "Web browser cache files",
            FileCategory.TEMPORARY_FILES: "Temporary files no longer needed",
            FileCategory.LOG_FILES: "Old log files taking up space",
            FileCategory.TRASH: "Files in trash waiting to be deleted",
            FileCategory.DOWNLOADS: "Old files in Downloads folder",
            FileCategory.APP_LEFTOVERS: "Files from uninstalled applications",
            FileCategory.DUPLICATES: "Duplicate files taking up extra space",
            FileCategory.LARGE_FILES: "Large files that might be unnecessary",
            FileCategory.OLD_FILES: "Files not accessed in a long time",
            FileCategory.XCODE_DERIVED_DATA: "Xcode build artifacts and derived data",
            FileCategory.XCODE_ARCHIVES: "Xcode archives and device support files",
            FileCategory.DOCKER_DATA: "Docker images, containers, and volumes",
            FileCategory.HOMEBREW_CACHE: "Homebrew package manager cache",
            FileCategory.NODE_MODULES: "Node.js dependencies in node_modules",
            FileCategory.PYTHON_CACHE: "Python package cache and compiled bytecode",
        }
        return descriptions.get(category, "")

    def _get_file_priority(self, file_path: Path, category: FileCategory) -> CleaningPriority:
        """Get priority for a specific file."""
        # Use category priority by default
        return self._get_category_priority(category)

    def _get_file_description(self, file_path: Path) -> str:
        """Get description for a specific file."""
        return f"File: {file_path.name}"

    def check_permissions(self) -> Dict[str, bool]:
        """Check permissions for common directories."""
        permissions = {}

        important_paths = [
            ("User Library", self.library_path),
            ("User Caches", self.library_path / "Caches"),
            ("System Caches", Path("/Library/Caches")),
            ("Temporary Files", Path("/tmp")),
            ("User Downloads", self.home_path / "Downloads"),
            ("Application Support", self.library_path / "Application Support"),
        ]

        for name, path in important_paths:
            if path.exists():
                permissions[name] = os.access(path, os.R_OK)
            else:
                permissions[name] = False

        # Check specific browser caches
        browsers = self._get_installed_browsers()
        for browser_name in browsers:
            if 'Safari' in browser_name:
                cache_path = self.library_path / "Caches" / "com.apple.Safari"
            elif 'Chrome' in browser_name:
                cache_path = self.library_path / "Caches" / "Google" / "Chrome"
            elif 'Firefox' in browser_name:
                cache_path = self.home_path / "Library" / "Application Support" / "Firefox"
            else:
                continue

            if cache_path.exists():
                permissions[f"{browser_name} Cache"] = os.access(cache_path, os.R_OK)
            else:
                permissions[f"{browser_name} Cache"] = False

        return permissions

    def get_system_info(self):
        """Get current system information."""
        import psutil
        import platform

        disk_usage = psutil.disk_usage('/')
        memory = psutil.virtual_memory()

        return SystemInfo(
            total_disk_space=disk_usage.total,
            used_disk_space=disk_usage.used,
            free_disk_space=disk_usage.free,
            total_memory=memory.total,
            used_memory=memory.used,
            free_memory=memory.available,
            cpu_usage=psutil.cpu_percent(interval=1),
            macos_version=platform.mac_ver()[0]
        )