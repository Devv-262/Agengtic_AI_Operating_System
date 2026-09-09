"""
tests/test_file_organizer.py
-----------------------------
Unit tests for the Smart File Organizer: batch confirmation (not one prompt
per file), correct moves per the model's plan, and undo support.
"""
import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.file_organizer import organize_directory, undo_last_organize


def _fake_llm(plan: dict):
    """Returns an object whose .invoke(...) mimics a ChatOpenAI response."""
    response = SimpleNamespace(content=json.dumps(plan))
    return SimpleNamespace(invoke=lambda messages: response)


def test_organize_directory_cancelled_without_confirmation(tmp_path):
    (tmp_path / "invoice.txt").write_text("total due: $42")
    (tmp_path / "photo.png").write_bytes(b"\x89PNG")

    plan = {"invoice.txt": "Invoices", "photo.png": "Images"}
    with patch("tools.file_organizer.get_llm", return_value=_fake_llm(plan)), \
         patch("tools.file_organizer.confirm_action", return_value=False):
        result = organize_directory.invoke({"directory_path": str(tmp_path)})

    assert "Cancelled" in result
    assert (tmp_path / "invoice.txt").exists()
    assert (tmp_path / "photo.png").exists()


def test_organize_directory_moves_files_with_single_confirmation(tmp_path):
    (tmp_path / "invoice.txt").write_text("total due: $42")
    (tmp_path / "photo.png").write_bytes(b"\x89PNG")

    plan = {"invoice.txt": "Invoices", "photo.png": "Images"}
    with patch("tools.file_organizer.get_llm", return_value=_fake_llm(plan)), \
         patch("tools.file_organizer.confirm_action", return_value=True) as mock_confirm:
        result = organize_directory.invoke({"directory_path": str(tmp_path)})

    assert mock_confirm.call_count == 1  # one batch prompt, not per-file
    assert "Organized 2 file(s)" in result
    assert (tmp_path / "Invoices" / "invoice.txt").exists()
    assert (tmp_path / "Images" / "photo.png").exists()
    assert not (tmp_path / "invoice.txt").exists()


def test_organize_directory_rejects_invalid_json(tmp_path):
    (tmp_path / "a.txt").write_text("data")

    bad_llm = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="not json"))
    with patch("tools.file_organizer.get_llm", return_value=bad_llm):
        result = organize_directory.invoke({"directory_path": str(tmp_path)})

    assert "invalid JSON" in result
    assert (tmp_path / "a.txt").exists()


def test_organize_directory_empty_dir(tmp_path):
    result = organize_directory.invoke({"directory_path": str(tmp_path)})
    assert "Nothing to organize" in result


def test_undo_last_organize_restores_files(tmp_path):
    (tmp_path / "invoice.txt").write_text("total due: $42")

    plan = {"invoice.txt": "Invoices"}
    with patch("tools.file_organizer.get_llm", return_value=_fake_llm(plan)), \
         patch("tools.file_organizer.confirm_action", return_value=True):
        organize_directory.invoke({"directory_path": str(tmp_path)})

    assert (tmp_path / "Invoices" / "invoice.txt").exists()

    with patch("tools.file_organizer.confirm_action", return_value=True):
        undo_result = undo_last_organize.invoke({"directory_path": str(tmp_path)})

    assert "Restored 1 file(s)" in undo_result
    assert (tmp_path / "invoice.txt").exists()
    assert not (tmp_path / "Invoices" / "invoice.txt").exists()


def test_undo_with_no_prior_run(tmp_path):
    result = undo_last_organize.invoke({"directory_path": str(tmp_path)})
    assert "nothing to undo" in result
