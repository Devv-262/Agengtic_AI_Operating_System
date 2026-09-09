"""
tests/test_document_reader.py
-------------------------------
Unit tests for document text extraction: supported/unsupported extensions,
missing files, and the sandbox gate on read_document.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.document_reader import extract_text, read_document


def test_extract_text_reads_txt(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("hello world")
    assert extract_text(path) == "hello world"


def test_extract_text_missing_file(tmp_path):
    result = extract_text(tmp_path / "missing.txt")
    assert result.startswith("Error:")


def test_extract_text_unsupported_extension(tmp_path):
    path = tmp_path / "video.mp4"
    path.write_bytes(b"\x00\x01")
    result = extract_text(path)
    assert "Unsupported document format" in result


def test_read_document_refuses_path_outside_sandbox():
    outside = "C:/Windows/System32/drivers/etc/hosts" if os.name == "nt" else "/etc/hosts"
    result = read_document.invoke({"file_path": outside})
    assert "outside the allowed sandbox" in result


def test_read_document_reads_txt_inside_sandbox(tmp_path, monkeypatch):
    # tmp_path is under the user's home dir (AppData/Local/Temp on Windows),
    # which check_path_allowed permits by default.
    path = tmp_path / "notes.txt"
    path.write_text("sandboxed content")
    result = read_document.invoke({"file_path": str(path)})
    assert result == "sandboxed content"
