"""
Main user interface for the macOS Cleaner
"""

import time
from typing import Optional, List, Set
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich import box

from core.scanner import SystemScanner
from core.cleaner import SystemCleaner, SafeCleaningContext
from core.optimizer import SystemOptimizer
from models.scan_result import FileCategory, CleaningPriority, ScanResult
from ui.components import (
    create_header, create_system_info_panel, create_scan_results_table,
    create_category_panel, create_cleaning_summary, create_startup_items_table,
    format_size, format_time
)
from utils.config import Config
from utils.logger import get_logger


console = Console()
logger = get_logger(__name__)


class CleanerInterface:
    """Main interface for the macOS Cleaner application."""

    def __init__(self, scanner: SystemScanner, cleaner: SystemCleaner,
                 optimizer: SystemOptimizer, config: Config,
                 auto_mode: bool = False, scan_only: bool = False):
        self.scanner = scanner
        self.cleaner = cleaner
        self.optimizer = optimizer
        self.config = config
        self.auto_mode = auto_mode
        self.scan_only = scan_only
        self.scan_result: Optional[ScanResult] = None

    def run(self):
        """Run the main interface."""
        try:
            # Show header
            console.print(create_header())

            # Show system info
            self._show_system_info()

            # Main menu loop
            if self.auto_mode:
                self._run_auto_mode()
            else:
                self._run_interactive_mode()

        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            logger.error(f"Interface error: {e}", exc_info=True)

    def _show_system_info(self):
        """Display current system information."""
        with console.status("[cyan]Gathering system information...[/cyan]"):
            system_info = self.scanner.get_system_info()

        console.print(create_system_info_panel(system_info))
        console.print()

    def _run_auto_mode(self):
        """Run in automatic mode."""
        console.print("[yellow]Running in automatic mode...[/yellow]\n")

        # Scan system
        self.scan_result = self._perform_scan()

        if self.scan_only:
            return

        # Clean high priority items
        categories = {
            cat for cat, result in self.scan_result.categories.items()
            if result.priority in [CleaningPriority.HIGH, CleaningPriority.MEDIUM]
        }

        if categories:
            console.print(f"[cyan]Cleaning {len(categories)} categories...[/cyan]")
            self._perform_cleaning(categories)
        else:
            console.print("[green]No high-priority items to clean![/green]")

    def _run_interactive_mode(self):
        """Run in interactive mode."""
        while True:
            # Show main menu
            choice = self._show_main_menu()

            if choice == "1":
                self._scan_menu()
            elif choice == "2":
                self._clean_menu()
            elif choice == "3":
                self._optimize_menu()
            elif choice == "4":
                self._settings_menu()
            elif choice == "q":
                if Confirm.ask("[yellow]Are you sure you want to quit?[/yellow]"):
                    console.print("[green]Thank you for using macOS Cleaner![/green]")
                    break

    def _show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        menu = Panel(
            "[1] 🔍 Scan System\n"
            "[2] 🧹 Clean Files\n"
            "[3] ⚡ Optimize System\n"
            "[4] ⚙️  Settings\n"
            "[q] 🚪 Quit",
            title="[bold cyan]Main Menu[/bold cyan]",
            border_style="bright_blue",
            padding=(1, 2)
        )

        console.print(menu)
        return Prompt.ask(
            "\n[cyan]Select an option[/cyan]",
            choices=["1", "2", "3", "4", "q"],
            default="1"
        )

    def _scan_menu(self):
        """Handle scan menu."""
        console.print("\n[bold cyan]System Scan[/bold cyan]\n")

        # Select categories to scan
        categories = self._select_scan_categories()

        if not categories:
            console.print("[yellow]No categories selected[/yellow]")
            return

        # Perform scan
        self.scan_result = self._perform_scan(categories)

        # Show results
        self._display_scan_results()

        # Ask what to do next
        if not self.scan_only and self.scan_result.total_files_found > 0:
            if Confirm.ask("\n[cyan]Would you like to clean these files?[/cyan]"):
                selected_categories = self._select_categories_to_clean()
                if selected_categories:
                    self._perform_cleaning(selected_categories)

    def _select_scan_categories(self) -> List[FileCategory]:
        """Let user select categories to scan."""
        console.print("[cyan]Select categories to scan:[/cyan]\n")

        categories = [
            (FileCategory.SYSTEM_CACHE, "System Cache", "🗄️"),
            (FileCategory.USER_CACHE, "User Cache", "👤"),
            (FileCategory.BROWSER_CACHE, "Browser Cache", "🌐"),
            (FileCategory.TEMPORARY_FILES, "Temporary Files", "📄"),
            (FileCategory.LOG_FILES, "Log Files", "📝"),
            (FileCategory.DOWNLOADS, "Old Downloads", "⬇️"),
            (FileCategory.TRASH, "Trash", "🗑️"),
            (FileCategory.DUPLICATES, "Duplicate Files", "📑"),
            (FileCategory.LARGE_FILES, "Large Files", "📦"),
            (FileCategory.OLD_FILES, "Old Files", "📅"),
            (FileCategory.APP_LEFTOVERS, "App Leftovers", "📱"),
            (FileCategory.XCODE_DERIVED_DATA, "Xcode Derived Data", "🔨"),
            (FileCategory.XCODE_ARCHIVES, "Xcode Archives", "🏗️"),
            (FileCategory.DOCKER_DATA, "Docker Data", "🐳"),
            (FileCategory.HOMEBREW_CACHE, "Homebrew Cache", "🍺"),
            (FileCategory.NODE_MODULES, "Node Modules", "🟢"),
            (FileCategory.PYTHON_CACHE, "Python Cache", "🐍"),
        ]

        for i, (cat, name, icon) in enumerate(categories, 1):
            console.print(f"[{i}] {icon}  {name}")

        console.print("[a] ✅ All categories")
        console.print("[c] ❌ Cancel")

        choice = Prompt.ask(
            "\n[cyan]Select categories (comma-separated numbers or 'a' for all)[/cyan]"
        )

        if choice.lower() == 'c':
            return []

        if choice.lower() == 'a':
            return [cat for cat, _, _ in categories]

        selected = []
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            for idx in indices:
                if 0 <= idx < len(categories):
                    selected.append(categories[idx][0])
        except ValueError:
            console.print("[red]Invalid selection[/red]")
            return []

        return selected

    def _perform_scan(self, categories: Optional[List[FileCategory]] = None) -> ScanResult:
        """Perform system scan with progress indication."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning system...[/cyan]", total=None)

            # Perform scan
            scan_result = self.scanner.scan(categories)

            progress.update(task, completed=100)

        return scan_result

    def _display_scan_results(self):
        """Display scan results."""
        if not self.scan_result:
            return

        console.print()
        console.print(create_scan_results_table(self.scan_result))

        # Show details for each category
        if Confirm.ask("\n[cyan]Show detailed file list before cleaning?[/cyan]", default=True):
            for category, result in self.scan_result.categories.items():
                if result.file_count > 0:
                    console.print(create_category_panel(category, result))

                    if result.file_count > 0:
                        self._show_file_list(category, result.files)

    def _show_file_list(self, category: FileCategory, files):
        """Show detailed file list with pagination."""
        if not files:
            return

        # Show files in batches
        batch_size = 20
        total = len(files)
        start_idx = 0

        while start_idx < total:
            end_idx = min(start_idx + batch_size, total)
            batch = files[start_idx:end_idx]

            table = Table(
                title=f"Files to Delete ({start_idx + 1}-{end_idx} of {total})",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan"
            )
            table.add_column("Path", style="cyan")
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Age", justify="right", style="blue")
            table.add_column("Safe", justify="center")

            home = str(Path.home())
            for file_info in batch:
                # Shorten path relative to home
                path_str = str(file_info.path)
                if path_str.startswith(home):
                    path_str = "~" + path_str[len(home):]

                table.add_row(
                    path_str,
                    format_size(file_info.size),
                    f"{file_info.age_days}d",
                    "✅" if file_info.is_safe_to_delete else "⚠️"
                )

            console.print(table)

            # Ask to continue if more files
            start_idx = end_idx
            if start_idx < total:
                if not Confirm.ask(
                    f"\n[cyan]Show next {min(batch_size, total - start_idx)} files?[/cyan]",
                    default=True
                ):
                    break
                console.print()

    def _select_categories_to_clean(self) -> Set[FileCategory]:
        """Let user select which categories to clean."""
        if not self.scan_result:
            return set()

        console.print("\n[cyan]Select categories to clean:[/cyan]\n")

        available_categories = [
            (cat, result) for cat, result in self.scan_result.categories.items()
            if result.file_count > 0
        ]

        if not available_categories:
            return set()

        for i, (cat, result) in enumerate(available_categories, 1):
            priority_color = {
                CleaningPriority.HIGH: "red",
                CleaningPriority.MEDIUM: "yellow",
                CleaningPriority.LOW: "green",
                CleaningPriority.OPTIONAL: "dim"
            }[result.priority]

            console.print(
                f"[{i}] {cat.name:<20} "
                f"[{priority_color}]{result.priority.value}[/{priority_color}] "
                f"{result.file_count} files, {format_size(result.total_size)}"
            )

        console.print("[a] All recommended (HIGH and MEDIUM priority)")
        console.print("[c] Cancel")

        choice = Prompt.ask("\n[cyan]Select categories[/cyan]")

        if choice.lower() == 'c':
            return set()

        if choice.lower() == 'a':
            return {
                cat for cat, result in available_categories
                if result.priority in [CleaningPriority.HIGH, CleaningPriority.MEDIUM]
            }

        selected = set()
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            for idx in indices:
                if 0 <= idx < len(available_categories):
                    selected.add(available_categories[idx][0])
        except ValueError:
            console.print("[red]Invalid selection[/red]")

        return selected

    def _perform_cleaning(self, categories: Set[FileCategory]):
        """Perform cleaning with progress indication."""
        if not self.scan_result:
            return

        with SafeCleaningContext(self.cleaner, self.scan_result) as context:
            # Preview what will be cleaned
            console.print("\n[yellow]Previewing cleaning operation...[/yellow]")
            preview_result = context.preview_cleaning(categories)

            console.print(create_cleaning_summary(preview_result, is_preview=True))

            if not Confirm.ask("\n[red]Proceed with cleaning?[/red]", default=False):
                console.print("[yellow]Cleaning cancelled[/yellow]")
                return

            # Perform actual cleaning
            console.print("\n[cyan]Cleaning files...[/cyan]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Cleaning...[/cyan]", total=100)

                def progress_callback(percentage, message):
                    progress.update(task, completed=percentage, description=message)

                cleaning_result = context.execute_cleaning(categories, progress_callback)

            # Show results
            console.print()
            console.print(create_cleaning_summary(cleaning_result, is_preview=False))

            # Verify cleaning
            if self.config.verify_cleaning:
                verification = self.cleaner.verify_cleaning(cleaning_result)
                if verification['still_exists']:
                    console.print(
                        f"\n[yellow]Warning: {len(verification['still_exists'])} "
                        f"files could not be verified as deleted[/yellow]"
                    )

    def _clean_menu(self):
        """Handle clean menu."""
        if not self.scan_result:
            console.print("\n[yellow]Please run a scan first![/yellow]")
            if Confirm.ask("[cyan]Run scan now?[/cyan]"):
                self._scan_menu()
            return

        console.print("\n[bold cyan]Clean System[/bold cyan]\n")

        options = [
            ("1", "🧹 Clean selected categories"),
            ("2", "⚡ Quick clean (recommended items only)"),
            ("3", "🗑️  Empty trash"),
            ("4", "🔙 Back to main menu"),
        ]

        for key, desc in options:
            console.print(f"[{key}] {desc}")

        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["1", "2", "3", "4"])

        if choice == "1":
            categories = self._select_categories_to_clean()
            if categories:
                self._perform_cleaning(categories)

        elif choice == "2":
            # Quick clean - high priority items only
            categories = {
                cat for cat, result in self.scan_result.categories.items()
                if result.priority == CleaningPriority.HIGH
            }
            if categories:
                self._perform_cleaning(categories)
            else:
                console.print("[green]No high-priority items to clean![/green]")

        elif choice == "3":
            self._empty_trash()

    def _empty_trash(self):
        """Empty system trash."""
        console.print("\n[yellow]Emptying trash...[/yellow]")

        result = self.cleaner.empty_trash()

        if result.space_freed > 0:
            console.print(
                f"[green]✅ Trash emptied successfully! "
                f"Freed {format_size(result.space_freed)}[/green]"
            )
        else:
            console.print("[yellow]Trash is already empty[/yellow]")

    def _optimize_menu(self):
        """Handle optimize menu."""
        console.print("\n[bold cyan]System Optimization[/bold cyan]\n")

        options = [
            ("1", "💾 Purge inactive memory"),
            ("2", "🌐 Flush DNS cache"),
            ("3", "🔍 Rebuild Spotlight index"),
            ("4", "🚀 Manage startup items"),
            ("5", "⚡ Run all optimizations"),
            ("6", "🔙 Back to main menu"),
        ]

        for key, desc in options:
            console.print(f"[{key}] {desc}")

        choice = Prompt.ask("\n[cyan]Select option[/cyan]",
                          choices=["1", "2", "3", "4", "5", "6"])

        if choice == "1":
            self._purge_memory()
        elif choice == "2":
            self._flush_dns()
        elif choice == "3":
            self._rebuild_spotlight()
        elif choice == "4":
            self._manage_startup_items()
        elif choice == "5":
            self._run_all_optimizations()

    def _purge_memory(self):
        """Purge inactive memory."""
        console.print("\n[yellow]Purging inactive memory...[/yellow]")
        console.print("[dim]Note: This requires administrator privileges[/dim]\n")

        try:
            memory_freed = self.optimizer.purge_inactive_memory()
            if memory_freed > 0:
                console.print(
                    f"[green]✅ Memory purged! "
                    f"Approximately {format_size(memory_freed)} freed[/green]"
                )
            else:
                console.print("[green]✅ Memory purged successfully![/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to purge memory: {e}[/red]")

    def _flush_dns(self):
        """Flush DNS cache."""
        console.print("\n[yellow]Flushing DNS cache...[/yellow]")

        if self.optimizer.flush_dns_cache():
            console.print("[green]✅ DNS cache flushed successfully![/green]")
        else:
            console.print("[red]❌ Failed to flush DNS cache[/red]")

    def _rebuild_spotlight(self):
        """Rebuild Spotlight index."""
        console.print("\n[yellow]Rebuilding Spotlight index...[/yellow]")
        console.print("[dim]Note: This will take some time to complete[/dim]\n")

        if Confirm.ask("[red]This will temporarily disable search. Continue?[/red]"):
            if self.optimizer.rebuild_spotlight_index():
                console.print(
                    "[green]✅ Spotlight rebuild initiated! "
                    "Search will be unavailable during indexing.[/green]"
                )
            else:
                console.print("[red]❌ Failed to rebuild Spotlight index[/red]")

    def _manage_startup_items(self):
        """Manage startup items."""
        console.print("\n[cyan]Loading startup items...[/cyan]")

        items = self.optimizer.get_startup_items()

        if not items:
            console.print("[yellow]No startup items found[/yellow]")
            return

        while True:
            # Show startup items
            console.print(create_startup_items_table(items))

            console.print("\n[cyan]Options:[/cyan]")
            console.print("[d] Disable an item")
            console.print("[e] Enable an item")
            console.print("[r] Refresh list")
            console.print("[b] Back")

            choice = Prompt.ask("\n[cyan]Select option[/cyan]",
                              choices=["d", "e", "r", "b"])

            if choice == "b":
                break
            elif choice == "r":
                items = self.optimizer.get_startup_items()
            elif choice in ["d", "e"]:
                # Get item index
                idx = Prompt.ask(
                    f"[cyan]Enter item number to {'disable' if choice == 'd' else 'enable'}[/cyan]"
                )

                try:
                    idx = int(idx) - 1
                    if 0 <= idx < len(items):
                        item = items[idx]

                        if choice == "d" and item.enabled:
                            if not item.can_disable:
                                if Confirm.ask(
                                    f"[yellow]Warning: {item.name} is not in the safe-to-disable list. "
                                    f"Force disable anyway?[/yellow]",
                                    default=False
                                ):
                                    # Force disable
                                    item.can_disable = True
                                else:
                                    console.print("[yellow]Skipping protected item[/yellow]")
                                    continue

                            if self.optimizer.disable_startup_item(item):
                                console.print(f"[green]✅ Disabled: {item.name}[/green]")
                                items = self.optimizer.get_startup_items()
                            else:
                                console.print(f"[red]❌ Failed to disable: {item.name}[/red]")

                        elif choice == "e" and not item.enabled:
                            if self.optimizer.enable_startup_item(item):
                                console.print(f"[green]✅ Enabled: {item.name}[/green]")
                                items = self.optimizer.get_startup_items()
                            else:
                                console.print(f"[red]❌ Failed to enable: {item.name}[/red]")

                        else:
                            console.print("[yellow]Item is already in that state[/yellow]")
                    else:
                        console.print("[red]Invalid item number[/red]")

                except ValueError:
                    console.print("[red]Invalid input[/red]")

    def _run_all_optimizations(self):
        """Run all optimization tasks."""
        console.print("\n[yellow]Running all optimizations...[/yellow]")
        console.print("[dim]This may take a few minutes[/dim]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Optimizing system...[/cyan]")

            result = self.optimizer.optimize_system()

        # Show results
        console.print("\n[bold green]Optimization Results:[/bold green]")

        if result.memory_freed > 0:
            console.print(f"✅ Memory freed: {format_size(result.memory_freed)}")

        if result.dns_cache_flushed:
            console.print("✅ DNS cache flushed")

        if result.spotlight_reindexed:
            console.print("✅ Spotlight index rebuild initiated")

        if result.errors:
            console.print("\n[yellow]Some operations failed:[/yellow]")
            for error in result.errors:
                console.print(f"  ❌ {error}")

    def _settings_menu(self):
        """Handle settings menu."""
        console.print("\n[bold cyan]Settings[/bold cyan]\n")

        # Show current settings
        settings_table = Table(box=box.ROUNDED)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Value", style="green")

        settings_table.add_row("Dry Run Mode", "✅" if self.config.dry_run else "❌")
        settings_table.add_row("Enable Backup", "✅" if self.config.enable_backup else "❌")
        settings_table.add_row("Verify Cleaning", "✅" if self.config.verify_cleaning else "❌")
        settings_table.add_row("Remove Empty Dirs", "✅" if self.config.remove_empty_dirs else "❌")
        settings_table.add_row("Max Workers", str(self.config.max_workers))

        console.print(settings_table)

        console.print("\n[cyan]Options:[/cyan]")
        console.print("[1] Modify settings")
        console.print("[2] Check permissions")
        console.print("[3] View troubleshooting guide")
        console.print("[b] Back to main menu")

        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["1", "2", "3", "b"])

        if choice == "1":
            # Toggle settings
            self.config.dry_run = Confirm.ask(
                "Enable dry run mode?",
                default=self.config.dry_run
            )

            self.config.enable_backup = Confirm.ask(
                "Enable file backup before deletion?",
                default=self.config.enable_backup
            )

            self.config.verify_cleaning = Confirm.ask(
                "Verify files after cleaning?",
                default=self.config.verify_cleaning
            )

            console.print("[green]Settings updated![/green]")

        elif choice == "2":
            self._check_permissions()

        elif choice == "3":
            console.print("\n[cyan]See TROUBLESHOOTING.md for common issues and solutions[/cyan]")
            console.print("Common issues:")
            console.print("  • Browser cache not found: Check Full Disk Access permissions")
            console.print("  • Cannot disable services: Some are protected by macOS")
            console.print("  • Permission denied: Grant Terminal full disk access")

    def _check_permissions(self):
        """Check and display permissions."""
        console.print("\n[yellow]Checking permissions...[/yellow]")

        permissions = self.scanner.check_permissions()

        # Create permissions table
        table = Table(title="[bold]Directory Permissions[/bold]", box=box.ROUNDED)
        table.add_column("Directory", style="cyan")
        table.add_column("Access", justify="center")

        for name, has_access in permissions.items():
            access_icon = "[green]✅[/green]" if has_access else "[red]❌[/red]"
            table.add_row(name, access_icon)

        console.print(table)

        # Show advice if permissions are missing
        if not all(permissions.values()):
            console.print("\n[yellow]⚠️  Some directories are not accessible[/yellow]")
            console.print("\nTo fix permissions:")
            console.print("1. Open System Preferences > Security & Privacy > Privacy")
            console.print("2. Select 'Full Disk Access' from the left sidebar")
            console.print("3. Add Terminal.app (or your terminal emulator)")
            console.print("4. Restart the terminal and try again")
        else:
            console.print("\n[green]✅ All permissions look good![/green]")