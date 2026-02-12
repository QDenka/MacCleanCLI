# Operations & Recovery Guide

## Safe Operating Procedure

1. Start with `--scan-only`.
2. Review categories and priority.
3. Run clean with backups enabled.
4. Verify result summary.
5. Keep backup retention at least 7 days.

## Recommended Runbooks

### Daily (quick)
```bash
macos-cleaner --auto
```

### Weekly (manual review)
```bash
macos-cleaner --scan-only
```
Then clean high + medium priority categories.

## Backup Location

By default backups are created under:

```bash
~/.macos-cleaner/backups/
```

Each run gets a timestamped folder with file copies and metadata.

## Restore Procedure

### Restore single file
```bash
cp ~/.macos-cleaner/backups/<timestamp>/path/to/file ~/path/to/file
```

### Restore entire backup set
```bash
cp -R ~/.macos-cleaner/backups/<timestamp>/* ~/
```

### Verify restored file
```bash
ls -la ~/path/to/file
```

## Emergency Rollback

If an operation deleted something important:

1. Stop current cleaning run.
2. Identify backup timestamp.
3. Restore target files from that backup.
4. Re-run in `--scan-only` to validate state.

## Permissions Checklist

- Terminal has Full Disk Access.
- User has read/write access to home directory.
- For optimization tasks requiring privileged operations, run explicit sudo commands manually.

## Logging & Debug

Logs are written to:

```bash
~/.macos-cleaner/logs/
```

Useful commands:

```bash
tail -n 100 ~/.macos-cleaner/logs/cleaner_$(date +%Y%m%d).log
grep -i "error\|failed" ~/.macos-cleaner/logs/cleaner_$(date +%Y%m%d).log
```

## Incident Reporting Template

Include:
- macOS version
- Python version
- command run
- relevant log excerpt
- whether backup was enabled
