# 🍎 macOS Cleaner

<div align="center">

<img width="1737" alt="macOS Cleaner Interface" src="https://github.com/user-attachments/assets/fdeb8a4e-3d95-4408-9e4b-484ee47000a7" />

**A beautiful and powerful console application for cleaning and optimizing macOS systems**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square)](https://www.apple.com/macos/)
[![GitHub Stars](https://img.shields.io/github/stars/QDenka/MacCleanCLI?style=flat-square)](https://github.com/QDenka/MacCleanCLI/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/QDenka/MacCleanCLI?style=flat-square)](https://github.com/QDenka/MacCleanCLI/issues)
[![GitHub Forks](https://img.shields.io/github/forks/QDenka/MacCleanCLI?style=flat-square)](https://github.com/QDenka/MacCleanCLI/network/members)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## ✨ Features

### 🔍 **Smart Scanning**
- Multi-threaded intelligent file scanning across 19+ categories
- Real-time progress tracking with detailed statistics
- **NEW:** Preview detailed file list before cleaning with pagination
- Pattern-based file identification with safety checks
- Configurable minimum file size filters

### 🧹 **Safe Cleaning**
- Priority-based cleaning (HIGH, MEDIUM, LOW, OPTIONAL)
- Built-in protection for system-critical files
- Optional backup system with configurable retention
- **NEW:** Show exactly what will be deleted with file paths and sizes
- Batch operations with parallel processing
- Dry-run mode for safe preview

### ⚡ **System Optimization**
- Memory purging for performance boost
- DNS cache flushing for network optimization
- Startup items management (LaunchAgents/Daemons/LoginItems)
- Spotlight index rebuilding
- Disk verification utilities

### 🎨 **Beautiful UI**
- Rich console interface with colors and animations
- Interactive menu system with keyboard shortcuts
- Real-time progress bars and status updates
- Comprehensive scan results visualization
- User-friendly file detail preview with pagination

### 🛡️ **Safety First**
- Protected system paths and directories
- Confirmation prompts for destructive operations
- Automatic backup before deletion (configurable)
- Post-cleaning verification
- Comprehensive error handling and logging

---

## 📋 Supported Cleaning Categories

### System Categories
- 🗄️ **System Cache** - System-level cache files (HIGH priority)
- 👤 **User Cache** - User application cache files (HIGH priority)
- 📁 **Temporary Files** - System temporary files (HIGH priority)
- 📝 **Log Files** - System and application logs (MEDIUM priority)
- 🗑️ **Trash** - Empty system trash bin (MEDIUM priority)

### Browser Data
- 🌐 **Browser Cache** - Safari, Chrome, Firefox, Brave, Edge, Opera, Vivaldi (MEDIUM priority)

### Developer Tools ⚡ NEW
- 🔨 **Xcode Derived Data** - Build artifacts and indexes (HIGH priority)
- 🏗️ **Xcode Archives** - Old app archives (MEDIUM priority)
- 🐳 **Docker Data** - Containers, images, volumes (MEDIUM priority)
- 🍺 **Homebrew Cache** - Package manager cache (MEDIUM priority)
- 🟢 **Node.js Modules** - node_modules directories (LOW priority)
- 🐍 **Python Cache** - __pycache__ and .pyc files (LOW priority)

### File Management
- 📥 **Downloads** - Old downloads folder files (OPTIONAL)
- 📋 **Duplicate Files** - Identical files detection (OPTIONAL)
- 📊 **Large Files** - Files over 100MB (OPTIONAL)
- 🕰️ **Old Files** - Files not accessed in 6+ months (OPTIONAL)
- 📦 **App Leftovers** - Files from uninstalled apps (MEDIUM priority)

---

## 🚀 Installation

### Prerequisites
- macOS 10.15 (Catalina) or later
- Python 3.10 or higher
- pip package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/QDenka/MacCleanCLI.git
cd MacCleanCLI

# Install with pip (development mode)
pip install -e .
```

### Verify Installation

```bash
# Check if commands are available
macos-cleaner --help
mclean --help
```

### System Permissions

For full functionality, grant Terminal **Full Disk Access**:

1. Open **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Click the **+** button and add your Terminal app
3. Restart Terminal and rerun the application

---

## 📖 Usage

### Interactive Mode (Recommended)

```bash
# Run with full interface
macos-cleaner

# Or use the short alias
mclean
```

**Interactive Workflow:**
1. **Scan System** - Choose categories to scan
2. **Review Results** - See detailed file list with sizes
3. **Clean Files** - Select items to delete
4. **Optimize System** - Run system optimizations

### Command Line Options

```bash
# Scan only (no cleaning)
macos-cleaner --scan-only

# Automatic mode (clean recommended items)
macos-cleaner --auto

# Use custom config file
macos-cleaner --config ~/custom-config.json

# Enable verbose output
macos-cleaner --verbose

# Dry run mode (preview only)
macos-cleaner --dry-run

# Combine options
macos-cleaner --scan-only --verbose
```

### Python Direct Execution

```bash
# Run directly with Python
python main.py

# With options
python main.py --scan-only
python main.py --auto --verbose
```

---

## 🎮 Interactive Menu Guide

### Main Menu
```
[1] 🔍 Scan System      - Scan for cleanable files
[2] 🧹 Clean Files      - Remove scanned files
[3] ⚡ Optimize System  - System optimization tasks
[4] ⚙️  Settings        - Configure application
[q] 🚪 Quit            - Exit application
```

### Scan Menu
```
[a] All Categories     - Scan everything
[1-9] Specific Category - Select individual category
[q] Back              - Return to main menu
```

### New Feature: File Detail Preview ✨

When cleaning, you can now preview exactly what will be deleted:

```
Show detailed file list before cleaning? [Y/n]: y

📁 System Cache Files
┌─────────────────────────────────────────────────────────┐
│ Path: ~/Library/Caches/com.apple.Safari/Cache.db       │
│ Size: 45.2 MB                                          │
│ Safe: ✅ Yes                                            │
├─────────────────────────────────────────────────────────┤
│ ... (showing 1-20 of 156 files)                        │
└─────────────────────────────────────────────────────────┘

Continue to next page? [Y/n]:
```

---

## ⚙️ Configuration

### Config File Location
`~/.macos-cleaner/config.json`

### Default Configuration

```json
{
  "dry_run": false,
  "enable_backup": true,
  "verify_cleaning": true,
  "remove_empty_dirs": true,
  "max_workers": 4,
  "backup_retention_days": 7,
  "min_file_size_mb": 0.001,
  "scan_hidden_files": false,
  "protected_extensions": [".dmg", ".pkg", ".app"],
  "protected_directories": [
    "/System",
    "/Library/System",
    "/private/var/db"
  ]
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `dry_run` | bool | `false` | Preview mode without deletion |
| `enable_backup` | bool | `true` | Backup files before cleaning |
| `verify_cleaning` | bool | `true` | Verify files are deleted |
| `remove_empty_dirs` | bool | `true` | Remove empty directories |
| `max_workers` | int | `4` | Parallel processing threads |
| `backup_retention_days` | int | `7` | Days to keep backups |
| `min_file_size_mb` | float | `0.001` | Minimum file size (1KB) |
| `scan_hidden_files` | bool | `false` | Include hidden files |

---

## 🛡️ Safety Features

### Protected Paths
The following paths are **never** touched:
- `/System/*` - System files
- `/Library/System/*` - System libraries
- `/private/var/db/*` - System databases
- `/usr/bin/*`, `/usr/sbin/*` - System binaries
- User home directory root files

### Safety Mechanisms
- ✅ Pre-flight safety checks
- ✅ User confirmation for all destructive operations
- ✅ Optional automatic backup system
- ✅ Post-cleaning verification
- ✅ Dry-run mode for risk-free preview
- ✅ Comprehensive error handling and logging

### Backup System
```bash
# Backups stored in
~/.macos-cleaner/backups/

# Structure
backups/
├── 2024-10-06_170000/    # Timestamp-based folders
│   ├── Caches/
│   └── manifest.json      # Backup metadata
└── 2024-10-05_120000/
```

---

## 🏗️ Project Architecture

### Directory Structure
```
MacCleanCLI/
├── main.py                 # Application entry point
├── core/                   # Core business logic
│   ├── scanner.py          # Multi-threaded file scanning
│   ├── cleaner.py          # Safe file deletion engine
│   └── optimizer.py        # System optimization utilities
├── models/                 # Data models and types
│   └── scan_result.py      # Result structures and enums
├── ui/                     # User interface layer
│   ├── interface.py        # Interactive menu system
│   └── components.py       # Reusable UI components
├── utils/                  # Utility modules
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging system
│   ├── backup.py           # Backup management
│   └── exceptions.py       # Custom exceptions
└── tests/                  # Test suite (87 tests)
    ├── test_scanner.py
    ├── test_cleaner.py
    ├── test_integration.py
    ├── test_optimizer.py
    └── test_new_categories.py
```

### Design Principles
- **SOLID Principles** - Clean, maintainable code architecture
- **Type Safety** - Full type hints with dataclasses
- **Error Handling** - Comprehensive exception handling
- **Testing** - 87 tests with 41% coverage
- **Performance** - Multi-threaded parallel processing
- **Safety** - Multiple layers of protection

---

## 🔧 Development

### Setup Development Environment

```bash
# Clone and navigate
git clone https://github.com/QDenka/MacCleanCLI.git
cd MacCleanCLI

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_scanner.py

# Run specific test
pytest tests/test_scanner.py::TestSystemScanner::test_scan_user_cache

# Generate coverage report
pytest --cov=. --cov-report=term-missing
```

**Current Test Stats:**
- ✅ 87 tests passing
- 📊 41% overall coverage
- 🎯 Core modules: 52-87% coverage

### Code Quality

```bash
# Format code with Black
black . --line-length 100

# Check linting with flake8
flake8 . --max-line-length=100

# Type checking with mypy
mypy . --ignore-missing-imports

# Run all quality checks
make lint
```

### Project Commands

```bash
# Available make commands
make install        # Install package
make install-dev    # Install with dev dependencies
make test          # Run tests
make coverage      # Generate coverage report
make lint          # Run all linters
make clean         # Clean build artifacts
```

---

## 📊 Performance

### Optimization Strategies
- **Multi-threading** - Parallel file scanning using ThreadPoolExecutor
- **Batch Operations** - Group operations by directory for efficiency
- **Memory Efficiency** - Stream large files instead of loading into RAM
- **Smart Caching** - Cache file metadata to avoid redundant I/O
- **Progress Tracking** - Real-time updates without blocking operations

### Benchmarks (Typical macOS System)
- **Scan Speed**: ~500-1000 files/second
- **Memory Usage**: 50-100 MB during scan
- **Clean Speed**: ~200-400 files/second
- **Thread Count**: Configurable (default: 4 workers)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Contribution Process

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub
   git clone https://github.com/YOUR_USERNAME/MacCleanCLI.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new features
   - Update documentation

4. **Run Tests**
   ```bash
   pytest
   black . --check
   flake8 .
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/amazing-feature
   # Open Pull Request on GitHub
   ```

### Contribution Guidelines

- ✅ Follow PEP 8 style guide
- ✅ Write meaningful commit messages
- ✅ Add tests for new features
- ✅ Update documentation
- ✅ Keep PRs focused and atomic
- ✅ Respond to review feedback

### Areas for Contribution

- 🐛 Bug fixes and error handling
- ✨ New cleaning categories
- 🎨 UI improvements
- 📝 Documentation enhancements
- 🧪 Test coverage expansion
- ⚡ Performance optimizations
- 🌍 Localization/translations

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

**TL;DR**: You can freely use, modify, and distribute this software with attribution.

---

## 🙏 Acknowledgments

### Built With
- **[Rich](https://github.com/Textualize/rich)** - Beautiful terminal formatting and UI components
- **[psutil](https://github.com/giampaolo/psutil)** - Cross-platform system and process utilities
- **[pytest](https://github.com/pytest-dev/pytest)** - Testing framework

### Inspiration
- macOS maintenance utilities
- CleanMyMac concepts
- Unix philosophy of doing one thing well

### Special Thanks
- All contributors and issue reporters
- The Python and open-source community
- macOS power users providing feedback

---

## 📞 Support & Community

### Get Help
- 📖 **Documentation**: [QUICKSTART.md](QUICKSTART.md) • [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/QDenka/MacCleanCLI/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/QDenka/MacCleanCLI/discussions)
- 📧 **Contact**: denis@kaban.dev

### Stay Updated
- ⭐ Star this repo to show support
- 👁️ Watch for updates and releases
- 🔔 Enable notifications for new versions

---

## ⚠️ Disclaimer

**Use at Your Own Risk**

This software is provided "as-is" without warranty of any kind. While extensive safety measures are in place, always:

1. ✅ **Backup Important Data** - Use Time Machine or other backup solutions
2. ✅ **Review Before Cleaning** - Check what will be deleted
3. ✅ **Start with Scan Only** - Test before actual cleaning
4. ✅ **Enable Backup Mode** - Use the built-in backup feature

The authors are not responsible for data loss or system issues. Always maintain regular backups of your system.

---

## 📈 Project Stats

![GitHub last commit](https://img.shields.io/github/last-commit/QDenka/MacCleanCLI?style=flat-square)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/QDenka/MacCleanCLI?style=flat-square)
![GitHub code size](https://img.shields.io/github/languages/code-size/QDenka/MacCleanCLI?style=flat-square)

**Made with ❤️ for macOS users**

---

<div align="center">

**If this project helped you, consider giving it a ⭐!**

</div>
