#!/usr/bin/env python3
"""
macOS Cleaner - A beautiful console application for cleaning macOS
Main entry point
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ui.interface import CleanerInterface
from core.scanner import SystemScanner
from core.cleaner import SystemCleaner
from core.optimizer import SystemOptimizer
from models.scan_result import FileCategory, CleaningPriority
from utils.logger import setup_logger, configure_logging
from utils.config import load_config

console = Console()
logger = setup_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="macOS Cleaner - Clean and optimize your Mac",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--scan-only", action="store_true", help="Only scan system without cleaning")
    parser.add_argument("--auto", action="store_true", help="Automatically clean recommended items")
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Preview cleaning without deleting files")
    parser.add_argument("--yes", "-y", action="store_true", help="Non-interactive confirmation mode")
    parser.add_argument("--categories", type=str, help="Comma-separated categories (example: user_cache,log_files,trash)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    return parser.parse_args()


def parse_categories(raw_categories: Optional[str]) -> Optional[List[FileCategory]]:
    if not raw_categories:
        return None

    categories: List[FileCategory] = []
    unknown: List[str] = []

    for raw in raw_categories.split(","):
        normalized = raw.strip().upper()
        if not normalized:
            continue
        try:
            categories.append(FileCategory[normalized])
        except KeyError:
            unknown.append(raw.strip())

    if unknown:
        valid = ", ".join([c.name.lower() for c in FileCategory])
        raise ValueError(f"Unknown categories: {', '.join(unknown)}. Valid categories: {valid}")

    return categories


def scan_result_to_dict(scan_result) -> dict:
    return {
        "total_files_found": scan_result.total_files_found,
        "total_size_found": scan_result.total_size_found,
        "total_size_mb": round(scan_result.total_size_mb, 2),
        "total_size_gb": round(scan_result.total_size_gb, 2),
        "scan_duration": round(scan_result.scan_duration, 3),
        "errors": scan_result.errors,
        "categories": {
            category.name.lower(): {
                "priority": result.priority.value,
                "file_count": result.file_count,
                "total_size": result.total_size,
                "total_size_mb": round(result.total_size_mb, 2),
                "description": result.description,
            }
            for category, result in scan_result.categories.items()
        },
    }


def cleaning_result_to_dict(cleaning_result) -> dict:
    return {
        "files_deleted": len(cleaning_result.files_deleted),
        "files_failed": len(cleaning_result.files_failed),
        "space_freed": cleaning_result.space_freed,
        "space_freed_mb": round(cleaning_result.space_freed_mb, 2),
        "space_freed_gb": round(cleaning_result.space_freed_gb, 2),
        "success_rate": round(cleaning_result.success_rate, 2),
        "categories_cleaned": [c.name.lower() for c in cleaning_result.categories_cleaned],
    }


def display_welcome():
    welcome_text = Text.from_markup(
        "[bold cyan]macOS Cleaner[/bold cyan]\n"
        "[dim]Clean and optimize your Mac with ease[/dim]"
    )
    panel = Panel(welcome_text, border_style="bright_blue", padding=(1, 2))
    console.print(panel)
    console.print()


def run_non_interactive_json(scanner: SystemScanner, cleaner: SystemCleaner,
                             categories: Optional[List[FileCategory]],
                             scan_only: bool,
                             auto_mode: bool) -> None:
    scan_result = scanner.scan(categories)
    payload = {"scan": scan_result_to_dict(scan_result)}

    if auto_mode and not scan_only:
        auto_categories = {
            cat for cat, result in scan_result.categories.items()
            if result.priority in [CleaningPriority.HIGH, CleaningPriority.MEDIUM]
        }
        cleaning_result = cleaner.clean(scan_result, auto_categories)
        payload["clean"] = cleaning_result_to_dict(cleaning_result)

    print(json.dumps(payload, indent=2))


def main():
    try:
        args = parse_arguments()
        configure_logging(verbose=args.verbose)

        config = load_config(args.config)
        if args.dry_run:
            config.dry_run = True
        if args.yes:
            config.confirm_operations = False

        selected_categories = parse_categories(args.categories)

        scanner = SystemScanner(config)
        cleaner = SystemCleaner(config)
        optimizer = SystemOptimizer(config)

        if args.json:
            run_non_interactive_json(
                scanner=scanner,
                cleaner=cleaner,
                categories=selected_categories,
                scan_only=args.scan_only,
                auto_mode=args.auto,
            )
            return

        if not args.auto:
            display_welcome()

        interface = CleanerInterface(
            scanner=scanner,
            cleaner=cleaner,
            optimizer=optimizer,
            config=config,
            auto_mode=args.auto,
            scan_only=args.scan_only
        )
        interface.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
