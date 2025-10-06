#!/usr/bin/env python3
"""
macOS Cleaner - A beautiful console application for cleaning macOS
Main entry point
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ui.interface import CleanerInterface
from core.scanner import SystemScanner
from core.cleaner import SystemCleaner
from core.optimizer import SystemOptimizer
from utils.logger import setup_logger
from utils.config import load_config

console = Console()
logger = setup_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="macOS Cleaner - Clean and optimize your Mac",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan system without cleaning"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically clean recommended items"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    return parser.parse_args()


def display_welcome():
    """Display welcome message."""
    welcome_text = Text.from_markup(
        "[bold cyan]macOS Cleaner[/bold cyan]\n"
        "[dim]Clean and optimize your Mac with ease[/dim]"
    )

    panel = Panel(
        welcome_text,
        border_style="bright_blue",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()


def main():
    """Main application entry point."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Load configuration
        config = load_config(args.config)

        # Display welcome message
        if not args.auto:
            display_welcome()

        # Initialize components
        scanner = SystemScanner(config)
        cleaner = SystemCleaner(config)
        optimizer = SystemOptimizer(config)

        # Create and run interface
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