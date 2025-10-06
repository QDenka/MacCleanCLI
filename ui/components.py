"""
UI components for the macOS Cleaner interface
"""

from typing import List, Optional
from datetime import datetime

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.console import Group
from rich.columns import Columns
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

from models.scan_result import (
    FileCategory, CategoryResult, ScanResult, CleaningResult,
    SystemInfo, CleaningPriority
)
from core.optimizer import StartupItem


def create_header() -> Panel:
    """Create application header."""
    header_text = Text()
    header_text.append("🍎 ", style="bold")
    header_text.append("macOS Cleaner", style="bold cyan")
    header_text.append(" v1.0.0\n", style="dim")
    header_text.append("Clean and optimize your Mac with ease", style="italic dim")

    return Panel(
        Align.center(header_text),
        box=box.DOUBLE,
        border_style="bright_blue",
        padding=(1, 0)
    )


def create_system_info_panel(system_info: SystemInfo) -> Panel:
    """Create system information panel."""
    # Create progress bars for disk and memory
    disk_bar = create_usage_bar(
        system_info.disk_usage_percent,
        f"Disk: {format_size(system_info.used_disk_space)} / {format_size(system_info.total_disk_space)}"
    )

    memory_bar = create_usage_bar(
        system_info.memory_usage_percent,
        f"Memory: {format_size(system_info.used_memory)} / {format_size(system_info.total_memory)}"
    )

    # Create info text
    info_text = Text()
    info_text.append(f"macOS {system_info.macos_version}\n", style="dim")
    info_text.append(f"CPU Usage: {system_info.cpu_usage:.1f}%\n", style="dim")
    info_text.append(f"Free Space: {format_size(system_info.free_disk_space)}", style="green")

    # Combine elements
    content = Group(
        disk_bar,
        Text(""),
        memory_bar,
        Text(""),
        info_text
    )

    return Panel(
        content,
        title="[bold]System Information[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )


def create_usage_bar(percentage: float, label: str) -> Panel:
    """Create a usage bar with percentage."""
    # Determine color based on usage
    if percentage >= 90:
        color = "red"
    elif percentage >= 70:
        color = "yellow"
    else:
        color = "green"

    # Create bar
    bar_width = 40
    filled = int(bar_width * percentage / 100)
    empty = bar_width - filled

    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty, style="dim")
    bar.append(f" {percentage:.1f}%", style=f"bold {color}")

    return Panel(
        Group(Text(label, style="dim"), bar),
        box=box.SIMPLE,
        padding=(0, 1)
    )


def create_scan_results_table(scan_result: ScanResult) -> Panel:
    """Create scan results summary table."""
    table = Table(box=box.ROUNDED, expand=True)

    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Files", justify="right", style="yellow")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Priority", justify="center")

    # Sort by priority and size
    sorted_categories = sorted(
        scan_result.categories.items(),
        key=lambda x: (x[1].priority.value, -x[1].total_size),
        reverse=False
    )

    total_files = 0
    total_size = 0
    has_results = False

    for category, result in sorted_categories:
        if result.file_count == 0:
            # Show categories that were scanned but found nothing
            if category == FileCategory.BROWSER_CACHE:
                table.add_row(
                    get_category_display_name(category),
                    "0",
                    "0.0 B",
                    "[dim]No accessible caches[/dim]"
                )
                has_results = True
            continue

        has_results = True
        total_files += result.file_count
        total_size += result.total_size

        # Priority with color
        priority_color = {
            CleaningPriority.HIGH: "red",
            CleaningPriority.MEDIUM: "yellow",
            CleaningPriority.LOW: "green",
            CleaningPriority.OPTIONAL: "dim"
        }[result.priority]

        table.add_row(
            get_category_display_name(category),
            str(result.file_count),
            format_size(result.total_size),
            f"[{priority_color}]{result.priority.value}[/{priority_color}]"
        )

    # Add separator if we have results
    if has_results:
        table.add_section()

    # Add total row
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{total_files}[/bold]",
        f"[bold]{format_size(total_size)}[/bold]",
        ""
    )

    # Create summary text
    summary = Text()
    summary.append(f"Scan completed in {scan_result.scan_duration:.1f} seconds\n", style="dim")

    if scan_result.errors:
        summary.append(f"⚠️  {len(scan_result.errors)} errors occurred", style="yellow")

    return Panel(
        Group(table, Text(""), summary),
        title=f"[bold]Scan Results - {format_time(scan_result.scan_time)}[/bold]",
        border_style="bright_blue",
        padding=(1, 1)
    )


def create_category_panel(category: FileCategory, result: CategoryResult) -> Panel:
    """Create detailed panel for a category."""
    # Create content
    content = Text()
    content.append(f"Description: {result.description}\n", style="dim")
    content.append(f"Files found: {result.file_count}\n")
    content.append(f"Total size: {format_size(result.total_size)}\n")
    content.append(f"Priority: ", style="dim")

    priority_color = {
        CleaningPriority.HIGH: "red",
        CleaningPriority.MEDIUM: "yellow",
        CleaningPriority.LOW: "green",
        CleaningPriority.OPTIONAL: "dim"
    }[result.priority]

    content.append(f"{result.priority.value}\n", style=priority_color)

    # Add file samples
    if result.files:
        content.append("\nSample files:\n", style="dim")
        for file_info in result.files[:5]:
            content.append(f"  • {file_info.path.name} ", style="cyan")
            content.append(f"({format_size(file_info.size)})\n", style="dim")

        if result.file_count > 5:
            content.append(f"  ... and {result.file_count - 5} more files\n", style="dim italic")

    return Panel(
        content,
        title=f"[bold]{get_category_display_name(category)}[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )


def create_cleaning_summary(result: CleaningResult, is_preview: bool = False) -> Panel:
    """Create cleaning summary panel."""
    if is_preview:
        title = "[bold yellow]Cleaning Preview[/bold yellow]"
        border_style = "yellow"
    else:
        title = "[bold green]Cleaning Complete[/bold green]"
        border_style = "green"

    # Create summary table
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    if is_preview:
        table.add_row("Files to delete:", f"{len(result.files_deleted)}")
        table.add_row("Space to free:", format_size(result.space_freed))
    else:
        table.add_row("Files deleted:", f"{len(result.files_deleted)}")
        table.add_row("Failed deletions:", f"{len(result.files_failed)}")
        table.add_row("Space freed:", format_size(result.space_freed))
        table.add_row("Success rate:", f"{result.success_rate:.1f}%")

        if result.duration > 0:
            table.add_row("Duration:", f"{result.duration:.1f}s")

    # Add categories cleaned
    if result.categories_cleaned:
        categories_text = Text("\nCategories cleaned:\n", style="dim")
        for cat in result.categories_cleaned:
            categories_text.append(f"  • {get_category_display_name(cat)}\n", style="cyan")
    else:
        categories_text = Text()

    # Add errors if any
    if result.files_failed and not is_preview:
        error_text = Text(f"\n⚠️  {len(result.files_failed)} files could not be deleted",
                         style="yellow")
    else:
        error_text = Text()

    content = Group(table, categories_text, error_text)

    return Panel(
        content,
        title=title,
        border_style=border_style,
        padding=(1, 2)
    )


def create_startup_items_table(items: List[StartupItem]) -> Panel:
    """Create startup items table."""
    table = Table(box=box.ROUNDED)

    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="yellow")
    table.add_column("Status", justify="center")
    table.add_column("Safe to Disable", justify="center")
    table.add_column("Description", style="dim")

    for i, item in enumerate(items, 1):
        status = "[green]●[/green] Enabled" if item.enabled else "[dim]○[/dim] Disabled"
        safe = "✅" if item.can_disable else "⚠️"

        table.add_row(
            str(i),
            item.name[:40] + "..." if len(item.name) > 40 else item.name,
            item.type,
            status,
            safe,
            item.description[:50] + "..." if len(item.description) > 50 else item.description
        )

    return Panel(
        table,
        title=f"[bold]Startup Items ({len(items)} total)[/bold]",
        border_style="bright_blue",
        padding=(1, 1)
    )


def get_category_display_name(category: FileCategory) -> str:
    """Get display name for a category."""
    display_names = {
        FileCategory.SYSTEM_CACHE: "🗄️  System Cache",
        FileCategory.USER_CACHE: "👤 User Cache",
        FileCategory.BROWSER_CACHE: "🌐 Browser Cache",
        FileCategory.TEMPORARY_FILES: "📄 Temporary Files",
        FileCategory.LOG_FILES: "📝 Log Files",
        FileCategory.DOWNLOADS: "⬇️  Old Downloads",
        FileCategory.TRASH: "🗑️  Trash",
        FileCategory.DUPLICATES: "📑 Duplicate Files",
        FileCategory.LARGE_FILES: "📦 Large Files",
        FileCategory.OLD_FILES: "📅 Old Files",
        FileCategory.APP_LEFTOVERS: "📱 App Leftovers",
        FileCategory.MEMORY: "💾 Memory",
        FileCategory.STARTUP_ITEMS: "🚀 Startup Items",
        FileCategory.XCODE_DERIVED_DATA: "🔨 Xcode Derived Data",
        FileCategory.XCODE_ARCHIVES: "🏗️  Xcode Archives",
        FileCategory.DOCKER_DATA: "🐳 Docker Data",
        FileCategory.HOMEBREW_CACHE: "🍺 Homebrew Cache",
        FileCategory.NODE_MODULES: "🟢 Node Modules",
        FileCategory.PYTHON_CACHE: "🐍 Python Cache",
    }

    return display_names.get(category, category.name)


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_time(dt: datetime) -> str:
    """Format datetime to readable string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def create_progress_panel(title: str, current: int, total: int,
                         message: str = "") -> Panel:
    """Create a progress panel."""
    percentage = (current / total * 100) if total > 0 else 0

    # Create progress bar
    bar_width = 50
    filled = int(bar_width * percentage / 100)
    empty = bar_width - filled

    progress_bar = Text()
    progress_bar.append("█" * filled, style="green")
    progress_bar.append("░" * empty, style="dim")

    # Create content
    content = Group(
        Text(f"{title}", style="bold"),
        Text(""),
        progress_bar,
        Text(f"{percentage:.1f}% ({current}/{total})", justify="center"),
        Text(message, style="dim") if message else Text("")
    )

    return Panel(
        content,
        border_style="cyan",
        padding=(1, 2)
    )


def create_error_panel(title: str, errors: List[str]) -> Panel:
    """Create an error panel."""
    content = Text()

    for error in errors[:10]:  # Limit to 10 errors
        content.append("❌ ", style="red")
        content.append(f"{error}\n")

    if len(errors) > 10:
        content.append(f"\n... and {len(errors) - 10} more errors", style="dim italic")

    return Panel(
        content,
        title=f"[bold red]{title}[/bold red]",
        border_style="red",
        padding=(1, 2)
    )


def create_confirmation_panel(question: str, details: Optional[str] = None) -> Panel:
    """Create a confirmation panel."""
    content = Text()
    content.append(question, style="bold yellow")

    if details:
        content.append(f"\n\n{details}", style="dim")

    content.append("\n\n[Y]es / [N]o", style="cyan")

    return Panel(
        content,
        title="[bold yellow]⚠️  Confirmation Required[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )