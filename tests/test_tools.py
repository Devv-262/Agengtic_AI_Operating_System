"""
tests/test_tools.py
--------------------
Unit tests for OS-level tool safety: destructive tools (delete/move/exec)
must refuse to act without user confirmation, and must proceed when
confirmed.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_manager import delete_file, move_file, read_file
from tools.shell_executor import execute_command
from tools._safety import check_path_allowed, check_command_blocked


def test_delete_file_cancelled_without_confirmation(tmp_path):
    target = tmp_path / "victim.txt"
    target.write_text("data")

    with patch("tools.file_manager.confirm_action", return_value=False):
        result = delete_file.invoke({"file_path": str(target)})

    assert "Cancelled" in result
    assert target.exists()


def test_delete_file_proceeds_when_confirmed(tmp_path):
    target = tmp_path / "victim.txt"
    target.write_text("data")

    with patch("tools.file_manager.confirm_action", return_value=True):
        result = delete_file.invoke({"file_path": str(target)})

    assert "Successfully deleted" in result
    assert not target.exists()


def test_move_file_cancelled_without_confirmation(tmp_path):
    src = tmp_path / "source.txt"
    src.write_text("data")
    dst = tmp_path / "dest.txt"

    with patch("tools.file_manager.confirm_action", return_value=False):
        result = move_file.invoke({"source_path": str(src), "destination_path": str(dst)})

    assert "Cancelled" in result
    assert src.exists()
    assert not dst.exists()


def test_execute_command_cancelled_without_confirmation():
    with patch("tools.shell_executor.confirm_action", return_value=False):
        result = execute_command.invoke({"command": "echo hi"})

    assert "Cancelled" in result


def test_path_outside_sandbox_is_rejected():
    # A path far outside the user's home directory should never pass.
    outside = Path("C:/Windows/System32/config" if os.name == "nt" else "/etc/shadow")
    error = check_path_allowed(outside)
    assert error is not None
    assert "outside the allowed sandbox" in error


def test_path_inside_home_is_allowed():
    inside = Path.home() / "Desktop" / "notes.txt"
    assert check_path_allowed(inside) is None


def test_read_file_refuses_path_outside_sandbox():
    outside = "C:/Windows/System32/drivers/etc/hosts" if os.name == "nt" else "/etc/hosts"
    result = read_file.invoke({"file_path": outside})
    assert "outside the allowed sandbox" in result


def test_blocked_command_rm_rf_is_refused():
    error = check_command_blocked("rm -rf /")
    assert error is not None
    assert "refused" in error


def test_blocked_command_format_is_refused():
    error = check_command_blocked("format c: /q")
    assert error is not None


def test_safe_command_is_not_blocked():
    assert check_command_blocked("echo hello world") is None
    assert check_command_blocked("dir C:\\Users") is None


def test_execute_command_hard_blocks_without_asking_confirmation():
    # The blocklist should short-circuit before confirm_action is even
    # called — a rushed "y" must not be able to approve a wipe.
    with patch("tools.shell_executor.confirm_action") as mock_confirm:
        result = execute_command.invoke({"command": "rm -rf /"})

    assert "refused" in result
    mock_confirm.assert_not_called()
