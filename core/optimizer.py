"""
System optimizer module for improving macOS performance
"""

import os
import subprocess
import plistlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time

from utils.logger import get_logger
from utils.config import Config
from utils.exceptions import OptimizationError


logger = get_logger(__name__)


def _escape_applescript_string(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')


@dataclass
class StartupItem:
    """Represents a startup/login item."""
    name: str
    path: Path
    type: str  # 'LaunchAgent', 'LaunchDaemon', 'LoginItem'
    enabled: bool
    description: str
    can_disable: bool
    location: Path

    @property
    def identifier(self) -> str:
        """Get unique identifier for this item."""
        return f"{self.type}:{self.name}"


@dataclass
class OptimizationResult:
    """Results of optimization operations."""
    memory_freed: int = 0
    startup_items_disabled: List[str] = None
    startup_items_enabled: List[str] = None
    dns_cache_flushed: bool = False
    spotlight_reindexed: bool = False
    errors: List[str] = None

    def __post_init__(self):
        if self.startup_items_disabled is None:
            self.startup_items_disabled = []
        if self.startup_items_enabled is None:
            self.startup_items_enabled = []
        if self.errors is None:
            self.errors = []


class SystemOptimizer:
    """Optimizes macOS system performance."""

    def __init__(self, config: Config):
        self.config = config
        self.dry_run = config.dry_run

        # Paths for startup items
        self.launch_paths = {
            'system_agents': Path("/Library/LaunchAgents"),
            'system_daemons': Path("/Library/LaunchDaemons"),
            'user_agents': Path.home() / "Library" / "LaunchAgents",
        }

        # Known safe-to-disable services
        self.safe_to_disable = {
            'com.adobe.AdobeCreativeCloud',
            'com.microsoft.office.licensingV2.helper',
            'com.spotify.webhelper',
            'com.dropbox.DropboxMacUpdate.agent',
            'com.google.keystone.agent',
            'com.google.keystone.daemon',
            'com.skype.skype.helper',
            'com.oracle.java.Java-Updater',
            'ru.vpnmonster.service',
            'com.nordvpn.service',
            'com.expressvpn.service',
            'com.surfshark.service',
            'com.privateinternetaccess.service',
        }

        # Services that should never be disabled
        self.protected_services = {
            'com.apple.',  # All Apple services
            'com.openssh.',
            'com.cups.',  # Printing
        }

    def optimize_system(self) -> OptimizationResult:
        """Run full system optimization."""
        result = OptimizationResult()

        logger.info("Starting system optimization")

        # Purge memory
        if self.config.optimize_memory:
            try:
                memory_freed = self.purge_inactive_memory()
                result.memory_freed = memory_freed
            except (OptimizationError, subprocess.CalledProcessError, OSError, Exception) as e:
                logger.error(f"Failed to purge memory: {e}")
                result.errors.append(f"Memory optimization failed: {str(e)}")

        # Flush DNS cache
        if self.config.flush_dns:
            try:
                if self.flush_dns_cache():
                    result.dns_cache_flushed = True
            except (OptimizationError, subprocess.CalledProcessError, OSError) as e:
                logger.error(f"Failed to flush DNS: {e}")
                result.errors.append(f"DNS flush failed: {str(e)}")

        # Rebuild Spotlight index if requested
        if self.config.rebuild_spotlight:
            try:
                if self.rebuild_spotlight_index():
                    result.spotlight_reindexed = True
            except (OptimizationError, subprocess.CalledProcessError, OSError) as e:
                logger.error(f"Failed to rebuild Spotlight: {e}")
                result.errors.append(f"Spotlight rebuild failed: {str(e)}")

        logger.info("System optimization completed")

        return result

    def get_startup_items(self) -> List[StartupItem]:
        """Get all startup/login items."""
        startup_items = []

        # Scan LaunchAgents and LaunchDaemons
        for location_type, path in self.launch_paths.items():
            if not path.exists():
                continue

            items = self._scan_launch_directory(path, location_type)
            startup_items.extend(items)

        # Get Login Items
        login_items = self._get_login_items()
        startup_items.extend(login_items)

        return sorted(startup_items, key=lambda x: x.name)

    def _scan_launch_directory(self, directory: Path, location_type: str) -> List[StartupItem]:
        """Scan a launch directory for plist files."""
        items = []

        try:
            for plist_file in directory.glob("*.plist"):
                try:
                    item = self._parse_launch_plist(plist_file, location_type)
                    if item:
                        items.append(item)
                except (OSError, IOError, plistlib.InvalidFileException) as e:
                    logger.debug(f"Error parsing {plist_file}: {e}")

        except PermissionError:
            logger.warning(f"Permission denied accessing {directory}")

        return items

    def _parse_launch_plist(self, plist_path: Path, location_type: str) -> Optional[StartupItem]:
        """Parse a launch plist file."""
        try:
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)

            # Extract information
            name = plist_path.stem
            label = plist_data.get('Label', name)
            program = plist_data.get('Program', '')

            # Check if it's a program or script
            program_args = plist_data.get('ProgramArguments', [])
            if program_args:
                program = program_args[0] if program_args else ''

            # Determine if enabled
            enabled = not plist_data.get('Disabled', False)

            # Determine if safe to disable
            can_disable = self._can_disable_service(name)

            # Create description
            description = self._get_service_description(name, plist_data)

            # Determine type based on location_type
            item_type = 'LaunchDaemon' if 'daemons' in location_type.lower() else 'LaunchAgent'

            return StartupItem(
                name=name,
                path=Path(program) if program else plist_path,
                type=item_type,
                enabled=enabled,
                description=description,
                can_disable=can_disable,
                location=plist_path
            )

        except (OSError, IOError, plistlib.InvalidFileException) as e:
            logger.debug(f"Error parsing plist {plist_path}: {e}")
            return None
        except KeyError as e:
            logger.debug(f"Missing required key in plist {plist_path}: {e}")
            return None

    def _get_login_items(self) -> List[StartupItem]:
        """Get user login items."""
        items = []

        try:
            # Use osascript to get login items
            script = '''
            tell application "System Events"
                get the name of every login item
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout:
                item_names = result.stdout.strip().split(', ')

                for name in item_names:
                    items.append(StartupItem(
                        name=name,
                        path=Path("/Applications") / f"{name}.app",
                        type='LoginItem',
                        enabled=True,
                        description=f"Login item: {name}",
                        can_disable=True,
                        location=Path("LoginItems")
                    ))

        except subprocess.CalledProcessError:
            logger.debug("Could not retrieve login items")

        return items

    def _can_disable_service(self, service_name: str) -> bool:
        """Check if a service can be safely disabled."""
        # Check if it's a protected service
        for protected in self.protected_services:
            if service_name.startswith(protected):
                return False

        # Check if it's in the safe-to-disable list
        return service_name in self.safe_to_disable

    def _get_service_description(self, name: str, plist_data: dict) -> str:
        """Get a human-readable description for a service."""
        descriptions = {
            'com.adobe.AdobeCreativeCloud': 'Adobe Creative Cloud background service',
            'com.microsoft.office.licensingV2.helper': 'Microsoft Office licensing helper',
            'com.spotify.webhelper': 'Spotify web helper for browser integration',
            'com.dropbox.DropboxMacUpdate.agent': 'Dropbox auto-update service',
            'com.google.keystone.agent': 'Google software update service',
            'com.skype.skype.helper': 'Skype helper for notifications',
        }

        if name in descriptions:
            return descriptions[name]

        # Try to extract from plist
        if 'Program' in plist_data:
            return f"Runs: {Path(plist_data['Program']).name}"

        return "Background service"

    def disable_startup_item(self, item: StartupItem) -> bool:
        """Disable a startup item."""
        if not item.can_disable:
            logger.warning(f"Cannot disable protected item: {item.name}")
            return False

        try:
            if item.type == 'LoginItem':
                return self._disable_login_item(item)
            else:
                return self._disable_launch_item(item)

        except (OSError, IOError, subprocess.CalledProcessError) as e:
            logger.error(f"Failed to disable {item.name}: {e}")
            return False

    def enable_startup_item(self, item: StartupItem) -> bool:
        """Enable a startup item."""
        try:
            if item.type == 'LoginItem':
                return self._enable_login_item(item)
            else:
                return self._enable_launch_item(item)

        except (OSError, IOError, subprocess.CalledProcessError) as e:
            logger.error(f"Failed to enable {item.name}: {e}")
            return False

    def _disable_launch_item(self, item: StartupItem) -> bool:
        """Disable a LaunchAgent/LaunchDaemon."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would disable: {item.name}")
            return True

        try:
            # Use launchctl to unload
            subprocess.run(
                ['launchctl', 'unload', str(item.location)],
                check=True,
                capture_output=True
            )

            # Modify plist to set Disabled = true
            with open(item.location, 'rb') as f:
                plist_data = plistlib.load(f)

            plist_data['Disabled'] = True

            with open(item.location, 'wb') as f:
                plistlib.dump(plist_data, f)

            logger.info(f"Disabled startup item: {item.name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unload {item.name}: {e}")
            return False

    def _enable_launch_item(self, item: StartupItem) -> bool:
        """Enable a LaunchAgent/LaunchDaemon."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would enable: {item.name}")
            return True

        try:
            # Modify plist to set Disabled = false
            with open(item.location, 'rb') as f:
                plist_data = plistlib.load(f)

            plist_data['Disabled'] = False

            with open(item.location, 'wb') as f:
                plistlib.dump(plist_data, f)

            # Use launchctl to load
            subprocess.run(
                ['launchctl', 'load', str(item.location)],
                check=True,
                capture_output=True
            )

            logger.info(f"Enabled startup item: {item.name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to load {item.name}: {e}")
            return False

    def _disable_login_item(self, item: StartupItem) -> bool:
        if self.dry_run:
            logger.info(f"[DRY RUN] Would remove login item: {item.name}")
            return True

        safe_name = _escape_applescript_string(item.name)
        script = f'tell application "System Events" to delete login item "{safe_name}"'

        try:
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )
            logger.info(f"Removed login item: {item.name}")
            return True

        except subprocess.CalledProcessError:
            return False

    def _enable_login_item(self, item: StartupItem) -> bool:
        if self.dry_run:
            logger.info(f"[DRY RUN] Would add login item: {item.name}")
            return True

        if not item.path.exists():
            logger.error(f"Application not found: {item.path}")
            return False

        safe_path = _escape_applescript_string(str(item.path))
        script = f'tell application "System Events" to make login item at end with properties {{path:"{safe_path}", hidden:false}}'

        try:
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )
            logger.info(f"Added login item: {item.name}")
            return True

        except subprocess.CalledProcessError:
            return False

    def purge_inactive_memory(self) -> int:
        """Purge inactive memory and return amount freed."""
        if self.dry_run:
            logger.info("[DRY RUN] Would purge inactive memory")
            return 0

        try:
            # Get memory info before purge
            import psutil
            mem_before = psutil.virtual_memory()

            # Purge memory
            subprocess.run(['sudo', 'purge'], check=True, capture_output=True)

            # Get memory info after purge
            time.sleep(1)  # Give system time to update
            mem_after = psutil.virtual_memory()

            freed = mem_after.available - mem_before.available
            logger.info(f"Purged memory, freed approximately {freed / (1024**2):.0f} MB")

            return max(0, freed)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to purge memory: {e}")
            raise

    def flush_dns_cache(self) -> bool:
        """Flush DNS cache."""
        if self.dry_run:
            logger.info("[DRY RUN] Would flush DNS cache")
            return True

        try:
            # Command varies by macOS version
            # This works for macOS 10.15+
            subprocess.run(
                ['sudo', 'dscacheutil', '-flushcache'],
                check=True,
                capture_output=True
            )

            # Also kill mDNSResponder
            subprocess.run(
                ['sudo', 'killall', '-HUP', 'mDNSResponder'],
                check=True,
                capture_output=True
            )

            logger.info("Flushed DNS cache")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to flush DNS cache: {e}")
            return False

    def rebuild_spotlight_index(self) -> bool:
        """Rebuild Spotlight search index."""
        if self.dry_run:
            logger.info("[DRY RUN] Would rebuild Spotlight index")
            return True

        try:
            # Turn off indexing
            subprocess.run(
                ['sudo', 'mdutil', '-a', '-i', 'off'],
                check=True,
                capture_output=True
            )

            # Delete index
            subprocess.run(
                ['sudo', 'rm', '-rf', '/.Spotlight-V100'],
                check=True,
                capture_output=True
            )

            # Turn on indexing
            subprocess.run(
                ['sudo', 'mdutil', '-a', '-i', 'on'],
                check=True,
                capture_output=True
            )

            logger.info("Initiated Spotlight index rebuild")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to rebuild Spotlight index: {e}")
            return False

    def verify_disk(self) -> Tuple[bool, List[str]]:
        """Verify disk for errors."""
        errors = []

        try:
            result = subprocess.run(
                ['diskutil', 'verifyVolume', '/'],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                logger.info("Disk verification passed")
                return True, []
            else:
                errors = result.stdout.split('\n')
                logger.warning(f"Disk verification found issues: {result.stdout}")
                return False, errors

        except (subprocess.CalledProcessError, OSError, IOError) as e:
            logger.error(f"Failed to verify disk: {e}")
            return False, [str(e)]