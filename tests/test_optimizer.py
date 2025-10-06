import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import plistlib
import subprocess
from unittest.mock import Mock, patch, MagicMock

from core.optimizer import SystemOptimizer, StartupItem, OptimizationResult
from utils.config import Config


class TestStartupItem:

    def test_startup_item_creation(self):
        item = StartupItem(
            name="com.test.app",
            path=Path("/Applications/Test.app"),
            type="LaunchAgent",
            enabled=True,
            description="Test application",
            can_disable=True,
            location=Path("/Library/LaunchAgents/com.test.app.plist")
        )

        assert item.name == "com.test.app"
        assert item.enabled is True
        assert item.can_disable is True

    def test_startup_item_identifier(self):
        item = StartupItem(
            name="com.test.app",
            path=Path("/Applications/Test.app"),
            type="LaunchAgent",
            enabled=True,
            description="Test app",
            can_disable=True,
            location=Path("/Library/LaunchAgents/com.test.app.plist")
        )

        assert item.identifier == "LaunchAgent:com.test.app"


class TestOptimizationResult:

    def test_optimization_result_defaults(self):
        result = OptimizationResult()

        assert result.memory_freed == 0
        assert result.startup_items_disabled == []
        assert result.startup_items_enabled == []
        assert result.dns_cache_flushed is False
        assert result.spotlight_reindexed is False
        assert result.errors == []

    def test_optimization_result_with_values(self):
        result = OptimizationResult(
            memory_freed=1024*1024*100,
            startup_items_disabled=["com.test.app"],
            dns_cache_flushed=True
        )

        assert result.memory_freed == 1024*1024*100
        assert len(result.startup_items_disabled) == 1
        assert result.dns_cache_flushed is True


class TestSystemOptimizer:

    @pytest.fixture
    def config(self):
        return Config(
            dry_run=True,
            optimize_memory=True,
            flush_dns=True,
            rebuild_spotlight=False
        )

    @pytest.fixture
    def optimizer(self, config):
        return SystemOptimizer(config)

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

    def test_optimizer_initialization(self, optimizer):
        assert optimizer is not None
        assert optimizer.config is not None
        assert optimizer.dry_run is True
        assert len(optimizer.protected_services) > 0
        assert len(optimizer.safe_to_disable) > 0

    def test_can_disable_service_protected(self, optimizer):
        assert optimizer._can_disable_service("com.apple.launchd") is False
        assert optimizer._can_disable_service("com.apple.SystemProfiler") is False
        assert optimizer._can_disable_service("com.openssh.sshd") is False

    def test_can_disable_service_safe(self, optimizer):
        assert optimizer._can_disable_service("com.adobe.AdobeCreativeCloud") is True
        assert optimizer._can_disable_service("com.spotify.webhelper") is True
        assert optimizer._can_disable_service("com.google.keystone.agent") is True

    def test_can_disable_service_unknown(self, optimizer):
        assert optimizer._can_disable_service("com.unknown.service") is False

    def test_get_service_description_known(self, optimizer):
        desc = optimizer._get_service_description(
            "com.adobe.AdobeCreativeCloud",
            {}
        )
        assert "Adobe" in desc

    def test_get_service_description_with_program(self, optimizer):
        plist_data = {"Program": "/usr/bin/test"}
        desc = optimizer._get_service_description("unknown.service", plist_data)
        assert "test" in desc

    def test_get_service_description_unknown(self, optimizer):
        desc = optimizer._get_service_description("unknown.service", {})
        assert desc == "Background service"

    def test_parse_launch_plist(self, optimizer, temp_dir):
        plist_path = temp_dir / "com.test.app.plist"
        plist_data = {
            "Label": "com.test.app",
            "Program": "/usr/bin/test",
            "Disabled": False
        }

        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_data, f)

        item = optimizer._parse_launch_plist(plist_path, "user_agents")

        assert item is not None
        assert item.name == "com.test.app"
        assert item.enabled is True
        assert item.type == "LaunchAgent"

    def test_parse_launch_plist_disabled(self, optimizer, temp_dir):
        plist_path = temp_dir / "com.test.daemon.plist"
        plist_data = {
            "Label": "com.test.daemon",
            "ProgramArguments": ["/usr/bin/daemon"],
            "Disabled": True
        }

        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_data, f)

        item = optimizer._parse_launch_plist(plist_path, "system_daemons")

        assert item is not None
        assert item.enabled is False
        assert item.type == "LaunchDaemon"

    def test_parse_launch_plist_invalid(self, optimizer, temp_dir):
        plist_path = temp_dir / "invalid.plist"
        plist_path.write_text("invalid data")

        item = optimizer._parse_launch_plist(plist_path, "user_agents")

        assert item is None

    def test_scan_launch_directory_empty(self, optimizer, temp_dir):
        items = optimizer._scan_launch_directory(temp_dir, "user_agents")
        assert items == []

    def test_scan_launch_directory_with_plists(self, optimizer, temp_dir):
        plist1 = temp_dir / "com.test.app1.plist"
        plist2 = temp_dir / "com.test.app2.plist"

        for plist in [plist1, plist2]:
            plist_data = {
                "Label": plist.stem,
                "Program": "/usr/bin/test"
            }
            with open(plist, 'wb') as f:
                plistlib.dump(plist_data, f)

        items = optimizer._scan_launch_directory(temp_dir, "user_agents")

        assert len(items) == 2

    @patch('subprocess.run')
    def test_get_login_items(self, mock_run, optimizer):
        mock_run.return_value = Mock(
            stdout="App1, App2, App3",
            returncode=0
        )

        items = optimizer._get_login_items()

        assert len(items) == 3
        assert items[0].name == "App1"
        assert items[0].type == "LoginItem"
        assert items[1].name == "App2"

    @patch('subprocess.run')
    def test_get_login_items_failure(self, mock_run, optimizer):
        mock_run.side_effect = subprocess.CalledProcessError(1, "osascript")

        items = optimizer._get_login_items()

        assert items == []

    def test_disable_startup_item_protected(self, optimizer):
        item = StartupItem(
            name="com.apple.test",
            path=Path("/System/Library/test"),
            type="LaunchAgent",
            enabled=True,
            description="Protected",
            can_disable=False,
            location=Path("/Library/LaunchAgents/com.apple.test.plist")
        )

        result = optimizer.disable_startup_item(item)

        assert result is False

    @patch('subprocess.run')
    def test_disable_launch_item_dry_run(self, mock_run, optimizer):
        item = StartupItem(
            name="com.test.app",
            path=Path("/Applications/Test.app"),
            type="LaunchAgent",
            enabled=True,
            description="Test",
            can_disable=True,
            location=Path("/Library/LaunchAgents/com.test.app.plist")
        )

        result = optimizer._disable_launch_item(item)

        assert result is True
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_enable_launch_item_dry_run(self, mock_run, optimizer):
        item = StartupItem(
            name="com.test.app",
            path=Path("/Applications/Test.app"),
            type="LaunchAgent",
            enabled=False,
            description="Test",
            can_disable=True,
            location=Path("/Library/LaunchAgents/com.test.app.plist")
        )

        result = optimizer._enable_launch_item(item)

        assert result is True
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_disable_login_item_dry_run(self, mock_run, optimizer):
        item = StartupItem(
            name="TestApp",
            path=Path("/Applications/TestApp.app"),
            type="LoginItem",
            enabled=True,
            description="Test",
            can_disable=True,
            location=Path("LoginItems")
        )

        result = optimizer._disable_login_item(item)

        assert result is True
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_enable_login_item_dry_run(self, mock_run, optimizer):
        item = StartupItem(
            name="TestApp",
            path=Path("/Applications/TestApp.app"),
            type="LoginItem",
            enabled=False,
            description="Test",
            can_disable=True,
            location=Path("LoginItems")
        )

        result = optimizer._enable_login_item(item)

        assert result is True
        mock_run.assert_not_called()

    @patch('subprocess.run')
    @patch('psutil.virtual_memory')
    def test_purge_inactive_memory_dry_run(self, mock_memory, mock_run, optimizer):
        result = optimizer.purge_inactive_memory()

        assert result == 0
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_flush_dns_cache_dry_run(self, mock_run, optimizer):
        result = optimizer.flush_dns_cache()

        assert result is True
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_rebuild_spotlight_index_dry_run(self, mock_run, optimizer):
        result = optimizer.rebuild_spotlight_index()

        assert result is True
        mock_run.assert_not_called()

    @patch('subprocess.run')
    @patch('psutil.virtual_memory')
    def test_purge_inactive_memory_actual(self, mock_memory, mock_run):
        config = Config(dry_run=False, optimize_memory=True)
        optimizer = SystemOptimizer(config)

        mem_before = Mock(available=1024*1024*1000)
        mem_after = Mock(available=1024*1024*1200)
        mock_memory.side_effect = [mem_before, mem_after]
        mock_run.return_value = Mock(returncode=0)

        result = optimizer.purge_inactive_memory()

        assert result > 0
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_flush_dns_cache_actual(self, mock_run):
        config = Config(dry_run=False, flush_dns=True)
        optimizer = SystemOptimizer(config)
        mock_run.return_value = Mock(returncode=0)

        result = optimizer.flush_dns_cache()

        assert result is True
        assert mock_run.call_count == 2

    @patch('subprocess.run')
    def test_verify_disk_success(self, mock_run, optimizer):
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Disk verification passed"
        )

        success, errors = optimizer.verify_disk()

        assert success is True
        assert errors == []

    @patch('subprocess.run')
    def test_verify_disk_failure(self, mock_run, optimizer):
        mock_run.return_value = Mock(
            returncode=1,
            stdout="Error: Volume corrupt"
        )

        success, errors = optimizer.verify_disk()

        assert success is False
        assert len(errors) > 0

    @patch('subprocess.run')
    @patch('psutil.virtual_memory')
    def test_optimize_system_dry_run(self, mock_memory, mock_run, optimizer):
        result = optimizer.optimize_system()

        assert result is not None
        assert isinstance(result, OptimizationResult)

    @patch('subprocess.run')
    @patch('psutil.virtual_memory')
    def test_optimize_system_with_errors(self, mock_memory, mock_run):
        config = Config(
            dry_run=False,
            optimize_memory=True,
            flush_dns=True
        )
        optimizer = SystemOptimizer(config)

        mock_run.side_effect = subprocess.CalledProcessError(1, "sudo")
        mock_memory.side_effect = Exception("Memory error")

        result = optimizer.optimize_system()

        assert len(result.errors) > 0

    def test_applescript_string_escape(self):
        from core.optimizer import _escape_applescript_string

        assert _escape_applescript_string('test') == 'test'
        assert _escape_applescript_string('test"quote') == 'test\\"quote'
        assert _escape_applescript_string('test\\slash') == 'test\\\\slash'
        assert _escape_applescript_string('test"and\\both') == 'test\\"and\\\\both'


if __name__ == "__main__":
    pytest.main([__file__])
