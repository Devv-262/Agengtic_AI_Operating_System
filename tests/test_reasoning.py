"""
tests/test_reasoning.py
------------------------
Unit tests for the specialist-model tools: generate_shell_command should
default to the shell native to the current host OS when target_shell isn't
given.
"""
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.reasoning import generate_shell_command


def _capturing_get_llm(captured: dict, reply: str):
    def fake_invoke(messages):
        captured["messages"] = messages
        return SimpleNamespace(content=reply)

    def fake_get_llm(task, temperature=0):
        return SimpleNamespace(invoke=fake_invoke)

    return fake_get_llm


def test_generate_shell_command_defaults_to_windows_powershell():
    captured = {}
    with patch("tools.reasoning.platform.system", return_value="Windows"), \
         patch("tools.reasoning.get_llm", side_effect=_capturing_get_llm(captured, "dir")):
        generate_shell_command.invoke({"natural_language_request": "list files"})

    assert "powershell" in captured["messages"][0].content.lower()


def test_generate_shell_command_defaults_to_linux_bash():
    captured = {}
    with patch("tools.reasoning.platform.system", return_value="Linux"), \
         patch("tools.reasoning.get_llm", side_effect=_capturing_get_llm(captured, "ls")):
        generate_shell_command.invoke({"natural_language_request": "list files"})

    assert "bash" in captured["messages"][0].content.lower()


def test_generate_shell_command_respects_explicit_target_shell():
    captured = {}
    with patch("tools.reasoning.platform.system", return_value="Windows"), \
         patch("tools.reasoning.get_llm", side_effect=_capturing_get_llm(captured, "ls")):
        generate_shell_command.invoke({"natural_language_request": "list files", "target_shell": "bash"})

    assert "bash" in captured["messages"][0].content.lower()
