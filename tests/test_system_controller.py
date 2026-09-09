"""
tests/test_system_controller.py
---------------------------------
Unit tests for the system controller tools. Volume/dark-mode implementations
are platform-specific, so platform.system() is mocked to exercise each
branch regardless of what OS the tests actually run on.
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.system_controller import get_system_info, set_volume, set_dark_mode


def test_get_system_info_reports_os_name():
    result = get_system_info.invoke({})
    assert "Operating System:" in result


def test_set_volume_rejects_out_of_range():
    assert "must be between 0 and 100" in set_volume.invoke({"level": 150})
    assert "must be between 0 and 100" in set_volume.invoke({"level": -1})


def test_set_volume_unsupported_os():
    with patch("tools.system_controller.platform.system", return_value="Plan9"):
        result = set_volume.invoke({"level": 50})
    assert "not implemented" in result


def test_set_volume_macos_calls_osascript():
    with patch("tools.system_controller.platform.system", return_value="Darwin"), \
         patch("tools.system_controller.subprocess.run") as mock_run:
        result = set_volume.invoke({"level": 40})

    mock_run.assert_called_once()
    assert "40%" in result


def test_set_dark_mode_unsupported_os():
    with patch("tools.system_controller.platform.system", return_value="Plan9"):
        result = set_dark_mode.invoke({"enabled": True})
    assert "not implemented" in result


def test_set_dark_mode_macos_calls_osascript():
    with patch("tools.system_controller.platform.system", return_value="Darwin"), \
         patch("tools.system_controller.subprocess.run") as mock_run:
        result = set_dark_mode.invoke({"enabled": True})

    mock_run.assert_called_once()
    assert "enabled" in result
