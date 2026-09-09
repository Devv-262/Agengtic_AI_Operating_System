"""
tests/test_tools.py
--------------------
Unit tests for OS-level tool safety: destructive tools (delete/move/exec)
must refuse to act without user confirmation, and must proceed when
confirmed.
"""
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_manager import delete_file, move_file
from tools.shell_executor import execute_command


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
