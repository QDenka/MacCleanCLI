# 🚀 macOS Cleaner - Quick Start Guide

Get up and running with macOS Cleaner in under 5 minutes!

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/QDenka/MacCleanCLI.git
cd MacCleanCLI
```

### Step 2: Install the Application

```bash
# Install with pip (development mode)
pip install -e .
```

**Why `-e` flag?** This installs the package in "editable" mode, meaning any code changes are immediately available without reinstalling.

### Step 3: Verify Installation

```bash
# Test both commands
macos-cleaner --help
mclean --help
```

**Expected output:** Usage information and available options

### Troubleshooting Installation

**If you get `ModuleNotFoundError`:**
```bash
# Ensure setup.py is properly configured
pip uninstall MacCleanCLI
pip install -e .
```

**If commands not found:**
```bash
# Check Python scripts directory is in PATH
echo $PATH | grep -q "Python" && echo "✓ Python in PATH" || echo "✗ Add Python to PATH"

# Find where scripts are installed
which macos-cleaner
```

---

## 🎬 First Run

### Launch the Application

```bash
macos-cleaner
```

**Alternative commands:**
```bash
mclean                    # Short alias
python main.py            # Direct Python execution
macos-cleaner --scan-only # Scan without cleaning (safe preview)
```

### Grant Permissions (Important!)

For full functionality, grant **Full Disk Access**:

1. **macOS Ventura/Sonoma:**
   - Open **System Settings** → **Privacy & Security** → **Full Disk Access**

2. **macOS Big Sur/Monterey:**
   - Open **System Preferences** → **Security & Privacy** → **Privacy** → **Full Disk Access**

3. Click **🔒** to unlock, then click **+** and add your Terminal app
4. Restart Terminal
5. Re-run `macos-cleaner`

---

## 🎯 Basic Workflow

### 1️⃣ Scan Your System

**Interactive Mode:**
1. Launch: `macos-cleaner`
2. Select: `[1] 🔍 Scan System`
3. Choose option:
   - `[a]` - Scan **ALL** categories (recommended for first run)
   - `[1-9]` - Select **specific** category
   - `[q]` - Go back

**Command Line Mode:**
```bash
# Scan everything (no deletion)
macos-cleaner --scan-only

# Scan with verbose output
macos-cleaner --scan-only --verbose
```

**What gets scanned?**
- ✅ System & User Caches
- ✅ Browser Data (Safari, Chrome, Firefox, etc.)
- ✅ Developer Tools (Xcode, Docker, Homebrew, Node.js, Python)
- ✅ Temporary Files & Logs
- ✅ Large Files & Duplicates
- ✅ Old Downloads
- ✅ App Leftovers

### 2️⃣ Review Scan Results

The scan shows:
```
╭─────────────── Scan Results ───────────────╮
│                                            │
│ 📊 System Cache:     1,234 files (2.5 GB) │
│    Priority: HIGH                          │
│                                            │
│ 🌐 Browser Cache:     856 files (1.2 GB)  │
│    Priority: MEDIUM                        │
│                                            │
│ 🔨 Xcode Data:        92 files (3.8 GB)   │
│    Priority: HIGH                          │
│                                            │
│ Total: 15.7 GB can be freed                │
╰────────────────────────────────────────────╯
```

**Priority Levels:**
- 🔴 **HIGH** - Safe to delete, significant space savings
- 🟡 **MEDIUM** - Generally safe, moderate savings
- 🔵 **LOW** - Safe but minimal impact
- ⚪ **OPTIONAL** - Review before cleaning

### 3️⃣ Preview Files (NEW Feature!)

**Before cleaning, see exactly what will be deleted:**

```bash
Show detailed file list before cleaning? [Y/n]: y

📁 System Cache Files (showing 1-20 of 156)
┌──────────────────────────────────────────────────┐
│ ~/Library/Caches/com.apple.Safari/Cache.db      │
│ Size: 45.2 MB | Safe: ✅ Yes                     │
├──────────────────────────────────────────────────┤
│ ~/Library/Caches/com.spotify.client/Data/       │
│ Size: 128.5 MB | Safe: ✅ Yes                    │
├──────────────────────────────────────────────────┤
│ ... (16 more files)                              │
└──────────────────────────────────────────────────┘

Continue to next page? [Y/n]:
```

**File preview features:**
- ✅ Pagination (20 files per page)
- ✅ Shortened paths (`~` for home directory)
- ✅ File sizes in human-readable format
- ✅ Safety indicators
- ✅ Interactive navigation

### 4️⃣ Clean Files

**Option A: Quick Clean (Recommended)**
1. Select `[2] 🧹 Clean Files`
2. Choose `[2] Quick Clean` (HIGH priority items only)
3. Review preview
4. Confirm cleaning

**Option B: Custom Clean**
1. Select `[2] 🧹 Clean Files`
2. Choose `[1] Select Categories`
3. Select specific categories to clean
4. Review preview
5. Confirm cleaning

**Command Line:**
```bash
# Automatic clean (HIGH priority only)
macos-cleaner --auto

# Dry run (preview without deletion)
macos-cleaner --dry-run
```

### 5️⃣ Optimize System (Optional)

Select `[3] ⚡ Optimize System` and choose:

**Memory Optimization:**
- Purge inactive memory
- Free up RAM

**Network Optimization:**
- Flush DNS cache
- Reset network connections

**Startup Management:**
- View startup items
- Disable unnecessary apps
- Manage LaunchAgents/Daemons

**Spotlight:**
- Rebuild search index
- Fix slow search

---

## 💡 Common Use Cases

### Daily Quick Cleanup

```bash
# One command, automatic cleaning
macos-cleaner --auto
```

**What it does:**
- Scans HIGH priority categories
- Shows preview
- Cleans confirmed items
- ~2-3 minutes

### Weekly Deep Clean

**Step-by-step:**
1. `macos-cleaner`
2. Scan ALL categories `[a]`
3. Review results carefully
4. Clean by priority:
   - First: HIGH priority items
   - Then: MEDIUM priority items
   - Optional: Review LOW priority
5. Empty trash
6. Optimize system

**Time needed:** ~10-15 minutes

### Before System Update

```bash
# Free maximum space
macos-cleaner --scan-only --verbose
```

**Then clean:**
1. All caches (System + User + Browser)
2. Temporary files
3. Old downloads
4. Trash
5. Xcode data (if applicable)
6. Docker data (if applicable)

**Expected gain:** 5-20 GB

### Developer Workflow

**For developers working with:**

**Xcode:**
```bash
# Scan developer categories only
macos-cleaner
# Select [1] → Choose Xcode categories
```
**Expected savings:** 5-15 GB (DerivedData + Archives)

**Docker:**
```bash
# Clean Docker data through app
macos-cleaner
# OR use Docker directly:
docker system prune -a
```
**Expected savings:** 2-10 GB

**Node.js:**
```bash
# Find all node_modules
macos-cleaner
# Select Node.js category
```
**Warning:** ⚠️ Only delete from old/unused projects!

### Monthly Maintenance

**Complete system refresh:**

1. **Week 1:** Scan and clean HIGH priority
2. **Week 2:** Review MEDIUM priority
3. **Week 3:** Check large files and duplicates
4. **Week 4:** Optimize system and startup

---

## ⚙️ Configuration

### Settings Menu

Access via `[4] ⚙️ Settings`:

1. **Dry Run Mode** - Preview without deletion
2. **Backup System** - Auto-backup before cleaning
3. **Verification** - Verify files are deleted
4. **Worker Threads** - Parallel processing (default: 4)
5. **Retention** - Backup retention days (default: 7)

### Config File

Located at: `~/.macos-cleaner/config.json`

**Quick edits:**
```bash
# Open config in editor
nano ~/.macos-cleaner/config.json

# Or reset to defaults
rm ~/.macos-cleaner/config.json
macos-cleaner  # Will create new config
```

**Example config:**
```json
{
  "dry_run": false,
  "enable_backup": true,
  "verify_cleaning": true,
  "max_workers": 4,
  "backup_retention_days": 7,
  "min_file_size_mb": 0.001,
  "scan_hidden_files": false
}
```

---

## ⌨️ Keyboard Shortcuts

### Main Menu
- `1-4` - Quick select menu option
- `q` - Quit / Go back
- `Enter` - Confirm selection

### Scan Menu
- `a` - Select all categories
- `1-9` - Select specific category
- `q` - Back to main menu

### Clean Menu
- `1` - Custom clean (select categories)
- `2` - Quick clean (HIGH priority)
- `q` - Back to main menu

### File Preview
- `y` / `Enter` - Continue to next page
- `n` - Skip to cleaning
- `q` - Cancel operation

---

## 🛡️ Safety Tips

### For First-Time Users

1. **Always start with scan-only:**
   ```bash
   macos-cleaner --scan-only
   ```

2. **Enable backup mode** (Settings menu)

3. **Review file preview** before confirming

4. **Start with HIGH priority only**

5. **Keep Time Machine backups** current

### Best Practices

✅ **DO:**
- Review scan results carefully
- Enable file preview
- Use backup mode for first clean
- Clean HIGH priority items first
- Keep system backups

❌ **DON'T:**
- Skip file preview on first run
- Clean OPTIONAL items without review
- Disable all safety features
- Delete without backup
- Run during important work

### Red Flags 🚩

**Stop and review if you see:**
- Unexpected file paths
- System directories in results
- App files you're actively using
- Configuration files
- Important documents

---

## 🔧 Troubleshooting Quick Fixes

### "Permission Denied"
```bash
# Grant Full Disk Access (see Installation section)
# Or run specific scan with sudo (not recommended)
sudo macos-cleaner --scan-only
```

### "No Files Found"
```bash
# Your system might be clean, or permissions issue
# Check if cache directories exist:
ls -la ~/Library/Caches/
```

### "Command Not Found"
```bash
# Reinstall package
pip uninstall MacCleanCLI
pip install -e .

# Or use direct Python
python main.py
```

### Application Freezes
```bash
# Check logs
cat ~/.macos-cleaner/logs/*.log

# Reset config
rm ~/.macos-cleaner/config.json
```

For more issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📚 Next Steps

### Learn More
- 📖 [Full Documentation](README.md)
- 🔧 [Troubleshooting Guide](TROUBLESHOOTING.md)
- 🐛 [Report Issues](https://github.com/QDenka/MacCleanCLI/issues)

### Advanced Usage
```bash
# Custom config file
macos-cleaner --config ~/my-config.json

# Combine multiple flags
macos-cleaner --scan-only --verbose --config ~/safe-config.json

# Direct Python with options
python main.py --auto --verbose
```

### Development
```bash
# Run tests
pytest

# Check code coverage
pytest --cov=. --cov-report=html

# Format code
black . --line-length 100
```

---

## 🎯 Pro Tips

1. **Schedule Weekly Scans**
   ```bash
   # Add to crontab for weekly scans
   0 9 * * 1 /usr/local/bin/macos-cleaner --scan-only
   ```

2. **Monitor Disk Space**
   - Use system info panel in app
   - Check before and after cleaning
   - Track savings over time

3. **Developer Setup**
   - Create separate config for dev vs production
   - Use `--dry-run` to test before batch operations
   - Enable verbose logging for debugging

4. **Backup Strategy**
   - Keep app backups for 7 days (default)
   - Use Time Machine for critical files
   - Export config before major changes

5. **Performance Optimization**
   - Close browsers before cleaning browser cache
   - Increase `max_workers` for faster scans (4-8)
   - Run during system idle time

---

## ✨ What's New

### Version 1.0 Features
- ✅ 19 cleaning categories
- ✅ **NEW: File detail preview with pagination**
- ✅ **NEW: Developer tools cleanup** (Xcode, Docker, Homebrew, Node.js, Python)
- ✅ Multi-threaded scanning
- ✅ Priority-based cleaning
- ✅ Rich console UI
- ✅ Backup system
- ✅ 87 tests passing

---

**Happy Cleaning! 🧹✨**

Need help? Open an issue on [GitHub](https://github.com/QDenka/MacCleanCLI/issues)
