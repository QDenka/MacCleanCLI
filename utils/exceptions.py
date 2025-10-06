from pathlib import Path
from typing import Optional


class MacCleanerError(Exception):
    pass


class ScanError(MacCleanerError):
    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.path = path
        super().__init__(f"{message}{f': {path}' if path else ''}")


class CleaningError(MacCleanerError):
    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.path = path
        super().__init__(f"{message}{f': {path}' if path else ''}")


class OptimizationError(MacCleanerError):
    def __init__(self, message: str, operation: Optional[str] = None) -> None:
        self.operation = operation
        super().__init__(f"{message}{f' ({operation})' if operation else ''}")


class BackupError(MacCleanerError):
    def __init__(self, message: str, path: Optional[Path] = None) -> None:
        self.path = path
        super().__init__(f"{message}{f': {path}' if path else ''}")


class ProtectedPathError(CleaningError):
    def __init__(self, path: Path) -> None:
        super().__init__("Cannot delete protected path", path)


class InsufficientPermissionsError(MacCleanerError):
    def __init__(self, path: Path, operation: str) -> None:
        self.path = path
        self.operation = operation
        super().__init__(f"Insufficient permissions for {operation}: {path}")
