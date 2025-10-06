# 🔧 macOS Cleaner - Troubleshooting Guide

Comprehensive solutions for common issues and errors.

---

## 🚨 Installation Issues

### Issue 1: ModuleNotFoundError: No module named 'main'

**Error:**
```bash
$ macos-cleaner
Traceback (most recent call last):
  File "/Library/Frameworks/Python.framework/Versions/3.13/bin/macos-cleaner", line 3, in <module>
    from main import main
ModuleNotFoundError: No module named 'main'
```

**Root Cause:** Package entry point can't find the main module

**Solution:**
```bash
# Method 1: Reinstall package
pip uninstall MacCleanCLI
pip install -e .

# Method 2: Verify setup.py contains py_modules
# setup.py should have:
#   py_modules=['main'],

# Method 3: Run directly with Python
python main.py
```

**Verify Fix:**
```bash
# Both commands should work
macos-cleaner --help
mclean --help
```

---

### Issue 2: Command Not Found

**Error:**
```bash
$ macos-cleaner
-bash: macos-cleaner: command not found
```

**Root Cause:** Python scripts directory not in PATH or package not installed

**Solution:**
```bash
# Step 1: Check if package is installed
pip show MacCleanCLI

# Step 2: Find where scripts are installed
which python
pip show MacCleanCLI | grep Location

# Step 3: Add Python scripts to PATH (if needed)
# For zsh (macOS default):
echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash:
echo 'export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile

# Step 4: Reinstall if needed
pip install -e .
```

**Workaround:**
```bash
# Use direct Python execution
python main.py
```

---

### Issue 3: Permission Denied During Installation

**Error:**
```bash
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Option 1: Install in user mode (recommended)
pip install --user -e .

# Option 2: Use virtual environment (best practice)
python -m venv venv
source venv/bin/activate
pip install -e .

# Option 3: Fix permissions (if necessary)
sudo chown -R $(whoami) ~/.local/lib/python*/site-packages
pip install -e .
```

---

## 🔐 Permission Issues

### Issue 4: Permission Denied When Scanning

**Error:**
```bash
PermissionError: [Errno 1] Operation not permitted: '/System/Library/Caches'
```

**Root Cause:** macOS System Integrity Protection (SIP) or missing Full Disk Access

**Solution:**

**Step 1: Grant Full Disk Access**
1. Open **System Settings** (macOS Ventura+) or **System Preferences** (older)
2. Navigate to **Privacy & Security** → **Full Disk Access**
3. Click 🔒 to unlock
4. Click **+** button
5. Add your Terminal app:
   - `/Applications/Utilities/Terminal.app`
   - `/Applications/iTerm.app` (if using iTerm2)
6. Restart Terminal
7. Re-run `macos-cleaner`

**Step 2: Verify Permissions**
```bash
# Test access to common directories
ls -la ~/Library/Caches/         # Should list files
ls -la /Library/Caches/          # Should list files
ls -la /var/folders/             # Should list files

# If still denied, check SIP status
csrutil status
```

**Step 3: Alternative for System Paths**
```bash
# Some system paths require sudo
sudo macos-cleaner --scan-only

# Warning: Not recommended for regular use
# Only use sudo for one-time system scans
```

---

### Issue 5: Cannot Access Browser Caches

**Problem:** Browser cache scan returns 0 files

**Root Cause:** Browser-specific permissions or browsers are running

**Solution:**

**Step 1: Close All Browsers**
```bash
# Close all browser instances
killall Safari Chrome Firefox Brave "Google Chrome" "Microsoft Edge"
```

**Step 2: Verify Cache Locations**
```bash
# Check if cache directories exist
ls -la ~/Library/Caches/com.apple.Safari/
ls -la ~/Library/Caches/Google/Chrome/
ls -la ~/Library/Caches/Firefox/
ls -la ~/Library/Caches/BraveSoftware/
```

**Step 3: Grant Permissions**
```bash
# If directories exist but can't read:
chmod -R u+r ~/Library/Caches/

# For stubborn caches, check extended attributes
xattr -d com.apple.quarantine ~/Library/Caches/* 2>/dev/null
```

**Browser-Specific Paths:**
- **Safari**: `~/Library/Caches/com.apple.Safari/`
- **Chrome**: `~/Library/Caches/Google/Chrome/Default/Cache/`
- **Firefox**: `~/Library/Caches/Firefox/Profiles/*/cache2/`
- **Brave**: `~/Library/Caches/BraveSoftware/Brave-Browser/Default/Cache/`
- **Edge**: `~/Library/Caches/Microsoft Edge/Default/Cache/`

---

## 🧹 Cleaning Issues

### Issue 6: Files Not Deleted

**Problem:** Clean operation completes but files still exist

**Root Cause:** Files in use, protected, or verification failed

**Diagnosis:**
```bash
# Check application logs
cat ~/.macos-cleaner/logs/cleaner_*.log | grep -i "failed\|error"

# Check if files are in use
lsof +D ~/Library/Caches/ | head -20
```

**Solutions:**

**1. Close Applications Using Files:**
```bash
# Identify processes
lsof ~/Library/Caches/* | awk '{print $1}' | sort -u

# Close specific apps
killall Safari Spotify Chrome
```

**2. Enable Dry Run to Test:**
```bash
# Test what would be deleted
macos-cleaner --dry-run
```

**3. Check Protected Paths:**
```bash
# View protected paths in config
cat ~/.MacCleanCLI/config.json | jq '.protected_directories'

# Files in protected paths are never deleted
```

**4. Verify Backup System:**
```bash
# If backup enabled, files moved here:
ls -la ~/.macos-cleaner/backups/

# Restore if needed
cp -r ~/.macos-cleaner/backups/YYYY-MM-DD_HHMMSS/* /original/location/
```

---

### Issue 7: Cleanup Fails with Errors

**Error:**
```bash
CleaningError: Failed to delete 45 files
See logs for details: ~/.macos-cleaner/logs/
```

**Investigation:**
```bash
# Check detailed logs
tail -50 ~/.macos-cleaner/logs/cleaner_$(date +%Y%m%d).log

# Common reasons in logs:
# - "Permission denied" → Need sudo or Full Disk Access
# - "File in use" → Close applications
# - "No such file or directory" → File deleted between scan and clean
```

**Solutions by Error Type:**

**Permission Errors:**
```bash
# Grant Full Disk Access (see Issue 4)
# Or use sudo for specific clean:
sudo macos-cleaner --auto
```

**Files in Use:**
```bash
# Close all applications
osascript -e 'tell application "System Events" to set quitapps to name of every application process whose visible is true and name is not "Finder"'

# Quit specific app
osascript -e 'quit app "Safari"'
```

**Path Doesn't Exist:**
```bash
# File was already deleted or moved
# This is safe to ignore, check verification summary
```

---

## 🔍 Scanning Issues

### Issue 8: Scan Finds 0 Files

**Problem:** Scan completes but reports 0 files

**Diagnosis:**
```bash
# Check if system is actually clean
du -sh ~/Library/Caches/
du -sh /Library/Caches/
du -sh ~/Library/Developer/Xcode/DerivedData/ 2>/dev/null

# Check minimum file size filter
cat ~/.MacCleanCLI/config.json | jq '.min_file_size_mb'
```

**Solutions:**

**1. Lower File Size Threshold:**
```bash
# Edit config to scan smaller files
nano ~/.MacCleanCLI/config.json
# Change: "min_file_size_mb": 0.0001  (100 bytes)
```

**2. Enable Hidden Files:**
```json
{
  "scan_hidden_files": true
}
```

**3. Check Specific Paths:**
```bash
# Manually verify cache directories exist
ls -la ~/Library/Caches/ | head -20
ls -la ~/Library/Developer/Xcode/DerivedData/ 2>/dev/null
ls -la ~/Library/Containers/*/Data/Library/Caches/ 2>/dev/null
```

**4. Run Verbose Scan:**
```bash
macos-cleaner --scan-only --verbose
# Check output for skipped paths or errors
```

---

### Issue 9: Scan is Very Slow

**Problem:** Scanning takes >10 minutes

**Root Cause:** Large external drives, network shares, or low worker count

**Solutions:**

**1. Increase Worker Threads:**
```bash
# Edit config file
nano ~/.MacCleanCLI/config.json
# Change: "max_workers": 8
# Default is 4, try 6-8 for faster scans
```

**2. Exclude Network Drives:**
```bash
# Unmount network shares during scan
# Or create custom config excluding them
```

**3. Monitor Progress:**
```bash
# Run with verbose mode to see what's being scanned
macos-cleaner --scan-only --verbose

# Check system resources
top -l 1 | grep macos-cleaner
```

**4. Scan Specific Categories Only:**
```bash
# Instead of scanning all, choose specific categories
# In interactive mode: Select categories individually
# This is much faster for targeted cleaning
```

---

## 🚀 System Optimization Issues

### Issue 10: Memory Purge Fails

**Error:**
```bash
OptimizationError: Failed to purge memory: [Errno 1] Operation not permitted
```

**Root Cause:** Memory purge requires admin privileges

**Solution:**
```bash
# Memory purge requires sudo
sudo purge

# Or run optimization with sudo
sudo macos-cleaner
# Then select: [3] Optimize System → [1] Purge Memory
```

**Alternative (no sudo needed):**
```bash
# Force applications to release memory
# Close memory-intensive apps:
killall -HUP Safari Chrome Spotify

# Check current memory usage
vm_stat

# Restart computer (most effective)
sudo shutdown -r now
```

---

### Issue 11: Cannot Disable Startup Items

**Error:**
```bash
Failed to disable startup item: com.example.service
```

**Root Cause:** SIP protection or insufficient permissions

**Solutions:**

**1. Check Item Type:**
```bash
# User LaunchAgents (can modify):
ls -la ~/Library/LaunchAgents/

# System LaunchAgents (require sudo):
ls -la /Library/LaunchAgents/

# System LaunchDaemons (require sudo):
ls -la /Library/LaunchDaemons/
```

**2. Disable via System Preferences:**
```bash
# For Login Items:
# System Settings → Users & Groups → Login Items
# Remove items manually
```

**3. Manual Disable:**
```bash
# For user agents
launchctl unload ~/Library/LaunchAgents/com.example.service.plist

# For system agents (requires sudo)
sudo launchctl unload /Library/LaunchAgents/com.example.service.plist

# For daemons (requires sudo)
sudo launchctl unload /Library/LaunchDaemons/com.example.service.plist
```

---

### Issue 12: Spotlight Rebuild Doesn't Work

**Error:**
```bash
Failed to rebuild Spotlight index
```

**Solution:**
```bash
# Complete Spotlight rebuild (requires sudo)

# Step 1: Stop indexing
sudo mdutil -a -i off

# Step 2: Delete index (this is normal and safe)
sudo rm -rf /.Spotlight-V100

# Step 3: Restart indexing
sudo mdutil -a -i on

# Step 4: Force reindex specific volume
sudo mdutil -E /

# Step 5: Check status
mdutil -s /
# Should show: "Indexing enabled"

# Wait 10-30 minutes for reindex to complete
```

**Verify:**
```bash
# Check indexing progress
sudo fs_usage -w -f filesys mds mdworker | grep -i spotlight

# Or check Spotlight preferences
# System Settings → Spotlight → Search Results
```

---

## 🐳 Developer Tools Issues

### Issue 13: Cannot Clean Docker Data

**Problem:** Docker data category shows 0 files or errors

**Solutions:**

**1. Docker Not Running:**
```bash
# Start Docker
open -a Docker

# Or use Docker CLI
docker info
```

**2. Clean Docker Manually:**
```bash
# Stop all containers
docker stop $(docker ps -aq)

# Remove all containers
docker rm $(docker ps -aq)

# Remove unused images
docker image prune -a

# Remove all unused data
docker system prune -a --volumes

# Check space saved
docker system df
```

**3. Docker Desktop Settings:**
```bash
# Open Docker Desktop → Preferences → Resources → Advanced
# Clean up via UI: "Clean / Purge Data"
```

---

### Issue 14: Xcode DerivedData Not Found

**Problem:** Xcode category finds nothing

**Verification:**
```bash
# Check if directory exists
ls -la ~/Library/Developer/Xcode/DerivedData/

# Check disk space used
du -sh ~/Library/Developer/Xcode/DerivedData/

# Check archives
du -sh ~/Library/Developer/Xcode/Archives/
```

**Solutions:**

**1. If Xcode Not Installed:**
```bash
# Category will show 0 files (expected)
# Skip this category
```

**2. If Xcode Installed but No Data:**
```bash
# Build a project to generate DerivedData
# Or clean from Xcode:
# Xcode → Product → Clean Build Folder (⌘⇧K)
```

**3. Manual Cleanup:**
```bash
# Safe to delete DerivedData
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Xcode will regenerate on next build
```

---

### Issue 15: Node Modules Detection Issues

**Problem:** node_modules not being detected

**Root Cause:** Requires directory traversal or specific path

**Verification:**
```bash
# Find all node_modules directories
find ~ -name "node_modules" -type d 2>/dev/null | head -20

# Check total size
du -sh ~/Projects/*/node_modules/ 2>/dev/null
```

**Solutions:**

**1. Scan from Project Root:**
```bash
# Ensure scanning from home directory
# App should find all node_modules under ~/

# If not, check config:
cat ~/.MacCleanCLI/config.json
```

**2. Manual Cleanup:**
```bash
# Clean specific project
cd ~/Projects/my-project
rm -rf node_modules
npm install  # Reinstall if needed

# Clean all old projects (use with caution!)
find ~/Projects -name "node_modules" -type d -mtime +90 -exec rm -rf {} \;
```

**3. Use npm:**
```bash
# Clean npm cache
npm cache clean --force

# Clean specific project
cd ~/Projects/my-project
npm ci  # Clean install
```

---

## 🖥️ Application Issues

### Issue 16: Application Crashes or Freezes

**Diagnosis:**
```bash
# Check crash logs
ls -lt ~/Library/Logs/DiagnosticReports/Python* | head -5

# Check application logs
tail -100 ~/.macos-cleaner/logs/cleaner_*.log

# Check system log
log show --predicate 'process == "Python"' --last 1h
```

**Solutions:**

**1. Clear Application Data:**
```bash
# Remove config (will recreate with defaults)
rm ~/.MacCleanCLI/config.json

# Remove logs
rm ~/.macos-cleaner/logs/*

# Remove backups (optional, only if space needed)
rm -rf ~/.macos-cleaner/backups/*
```

**2. Reinstall Application:**
```bash
# Complete reinstall
pip uninstall MacCleanCLI
rm -rf ~/Library/Python/*/site-packages/macos_cleaner*
pip install -e .
```

**3. Check Python Version:**
```bash
# Requires Python 3.10+
python --version

# Upgrade if needed
brew upgrade python
```

**4. Check Dependencies:**
```bash
# Verify all dependencies installed
pip list | grep -E "rich|psutil|click"

# Reinstall if missing
pip install rich psutil click
```

---

### Issue 17: Config File Errors

**Error:**
```bash
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution:**
```bash
# Backup current config
cp ~/.MacCleanCLI/config.json ~/.MacCleanCLI/config.json.bak

# Remove corrupted config
rm ~/.MacCleanCLI/config.json

# Run app to generate new config
macos-cleaner

# Or create valid config manually
cat > ~/.MacCleanCLI/config.json << 'EOF'
{
  "dry_run": false,
  "enable_backup": true,
  "verify_cleaning": true,
  "remove_empty_dirs": true,
  "max_workers": 4,
  "backup_retention_days": 7,
  "min_file_size_mb": 0.001,
  "scan_hidden_files": false
}
EOF
```

---

## 🔬 Debug Mode

### Enable Comprehensive Logging

```bash
# Create debug configuration
cat > ~/.MacCleanCLI/debug_config.json << 'EOF'
{
  "dry_run": true,
  "verbose": true,
  "log_level": "DEBUG",
  "enable_backup": true,
  "max_workers": 2
}
EOF

# Run with debug config
macos-cleaner --config ~/.MacCleanCLI/debug_config.json --verbose

# View detailed logs
tail -f ~/.macos-cleaner/logs/cleaner_$(date +%Y%m%d).log
```

### Collect Diagnostic Information

```bash
# System information
sw_vers
python --version
pip list | grep -E "MacCleanCLI|rich|psutil"

# Disk space
df -h

# Permission check
ls -la ~/Library/Caches/ | head -5
ls -la /Library/Caches/ | head -5

# Config check
cat ~/.MacCleanCLI/config.json

# Recent errors
tail -100 ~/.macos-cleaner/logs/*.log | grep -i error
```

---

## 🆘 Emergency Recovery

### If Something Goes Wrong

**1. Restore from Backup:**
```bash
# List available backups
ls -lt ~/.macos-cleaner/backups/

# Restore specific backup
cp -r ~/.macos-cleaner/backups/2024-10-06_170000/* ~/

# Or restore specific file
cp ~/.macos-cleaner/backups/2024-10-06_170000/Library/Caches/somefile ~/Library/Caches/
```

**2. Use Time Machine:**
```bash
# Enter Time Machine
# Navigate to deleted files
# Restore files

# Or via command line
tmutil listbackups
tmutil restore /path/to/backup/file /restore/location
```

**3. Stop Application Immediately:**
```bash
# Kill all instances
killall -9 Python macos-cleaner

# Check for background processes
ps aux | grep macos-cleaner
```

**4. Reset to Factory State:**
```bash
# Complete reset
rm -rf ~/.MacCleanCLI/
rm -rf ~/.macos-cleaner/
pip uninstall MacCleanCLI
pip install -e .
```

---

## 📋 Pre-Reporting Checklist

Before reporting a bug, gather this information:

```bash
# 1. System Information
sw_vers > ~/debug-report.txt
echo "\n=== Python Version ===" >> ~/debug-report.txt
python --version >> ~/debug-report.txt

# 2. Package Information
echo "\n=== Package Info ===" >> ~/debug-report.txt
pip show MacCleanCLI >> ~/debug-report.txt

# 3. Configuration
echo "\n=== Configuration ===" >> ~/debug-report.txt
cat ~/.MacCleanCLI/config.json >> ~/debug-report.txt

# 4. Recent Logs
echo "\n=== Recent Errors ===" >> ~/debug-report.txt
tail -50 ~/.macos-cleaner/logs/*.log | grep -i error >> ~/debug-report.txt

# 5. Permissions
echo "\n=== Permissions ===" >> ~/debug-report.txt
ls -la ~/Library/Caches/ | head -10 >> ~/debug-report.txt

# View report
cat ~/debug-report.txt
```

---

## 📞 Getting Additional Help

### Resources
- 📖 [Documentation](README.md)
- 🚀 [Quick Start Guide](QUICKSTART.md)
- 🐛 [Report Issues](https://github.com/QDenka/MacCleanCLI/issues)
- 💬 [GitHub Discussions](https://github.com/QDenka/MacCleanCLI/discussions)

### When Reporting Bugs

Include:
1. macOS version
2. Python version
3. Installation method
4. Full error message
5. Steps to reproduce
6. Config file content (remove sensitive data)
7. Relevant log excerpts

### Community Support

- **Search existing issues** before creating new ones
- **Provide debug information** from checklist above
- **Be specific** about what you expected vs what happened
- **Include screenshots** if UI-related

---

## ⚠️ Known Limitations

1. **System Integrity Protection (SIP)**
   - Cannot modify SIP-protected files
   - Some system directories are read-only
   - This is by design for system security

2. **iCloud Files**
   - Downloaded iCloud files may reappear after deletion
   - iCloud syncs deleted items back

3. **Active Files**
   - Cannot delete files currently in use
   - Close applications before cleaning

4. **Permissions**
   - Some operations require admin access
   - Full Disk Access needed for complete scan

5. **File Size Detection**
   - Minimum 1KB for general scanning
   - 100KB minimum for duplicate detection
   - Adjustable via config

---

**Still having issues? [Open an issue on GitHub](https://github.com/QDenka/MacCleanCLI/issues)**

**Made with ❤️ for macOS users**
