"""Tests for platform detection utilities."""

import pytest
from unittest.mock import patch, MagicMock
from app.utils.platform_utils import (
    is_linux,
    is_windows,
    is_macos,
    has_raw_socket_capability,
    get_default_interface,
    get_nmap_privilege_flags,
)


class TestPlatformDetection:
    @patch("sys.platform", "linux")
    def test_is_linux_true(self):
        assert is_linux() is True
        assert is_windows() is False
        assert is_macos() is False

    @patch("sys.platform", "win32")
    def test_is_windows_true(self):
        assert is_windows() is True
        assert is_linux() is False

    @patch("sys.platform", "darwin")
    def test_is_macos_true(self):
        assert is_macos() is True
        assert is_linux() is False


class TestPrivilegeDetection:
    @patch("sys.platform", "win32")
    def test_windows_never_privileged(self):
        assert has_raw_socket_capability() is False

    @patch("sys.platform", "linux")
    @patch("os.geteuid", create=True, return_value=0)
    def test_linux_root_is_privileged(self, mock_euid):
        assert has_raw_socket_capability() is True

    @patch("sys.platform", "linux")
    @patch("os.geteuid", create=True, return_value=1000)
    @patch("subprocess.run")
    def test_linux_with_capability(self, mock_run, mock_euid):
        mock_run.return_value = MagicMock(stdout="cap_net_raw", returncode=0)
        assert has_raw_socket_capability() is True


class TestInterfaceDetection:
    @patch("sys.platform", "linux")
    @patch("subprocess.run")
    def test_linux_interface_from_ip_route(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="default via 192.168.1.1 dev enp3s0 proto dhcp",
            returncode=0
        )
        assert get_default_interface() == "enp3s0"

    @patch("sys.platform", "linux")
    @patch("subprocess.run")
    @patch("os.path.exists")
    def test_linux_fallback_to_eth0(self, mock_exists, mock_run):
        mock_run.return_value = MagicMock(stdout="", returncode=1)
        mock_exists.side_effect = lambda p: p == "/sys/class/net/eth0"
        assert get_default_interface() == "eth0"


class TestNmapFlags:
    @patch("sys.platform", "win32")
    def test_windows_always_unprivileged(self):
        assert get_nmap_privilege_flags() == "--unprivileged"

    @patch("sys.platform", "linux")
    @patch("app.utils.platform_utils.has_raw_socket_capability", return_value=True)
    def test_linux_privileged(self, mock_cap):
        assert get_nmap_privilege_flags() == ""

    @patch("sys.platform", "linux")
    @patch("app.utils.platform_utils.has_raw_socket_capability", return_value=False)
    def test_linux_unprivileged(self, mock_cap):
        assert get_nmap_privilege_flags() == "--unprivileged"
