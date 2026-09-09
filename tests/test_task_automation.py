"""
tests/test_task_automation.py
-------------------------------
Unit tests for Task Automation: image resizing, zip creation, and zip
extraction (including a zip-slip path-traversal guard).
"""
import os
import sys
import zipfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

from tools.task_automation import resize_images, create_archive, extract_archive


def test_resize_images_creates_resized_subfolder(tmp_path):
    img = Image.new("RGB", (4000, 2000), color="red")
    img.save(tmp_path / "big.jpg")

    with patch("tools.task_automation.confirm_action", return_value=True):
        result = resize_images.invoke({"directory_path": str(tmp_path), "max_dimension": 1000})

    assert "Resized 1 image(s)" in result
    output = tmp_path / "resized" / "big.jpg"
    assert output.exists()
    with Image.open(output) as resized:
        assert max(resized.size) <= 1000


def test_resize_images_cancelled_without_confirmation(tmp_path):
    Image.new("RGB", (100, 100)).save(tmp_path / "small.png")

    with patch("tools.task_automation.confirm_action", return_value=False):
        result = resize_images.invoke({"directory_path": str(tmp_path)})

    assert "Cancelled" in result
    assert not (tmp_path / "resized").exists()


def test_resize_images_no_images_found(tmp_path):
    (tmp_path / "notes.txt").write_text("not an image")
    result = resize_images.invoke({"directory_path": str(tmp_path)})
    assert "No images found" in result


def test_create_archive_zips_files(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")
    output = tmp_path / "out.zip"

    with patch("tools.task_automation.confirm_action", return_value=True):
        result = create_archive.invoke({
            "paths": [str(tmp_path / "a.txt"), str(tmp_path / "b.txt")],
            "output_path": str(output),
        })

    assert "Created archive" in result
    assert output.exists()
    with zipfile.ZipFile(output) as zf:
        assert set(zf.namelist()) == {"a.txt", "b.txt"}


def test_create_archive_cancelled_without_confirmation(tmp_path):
    (tmp_path / "a.txt").write_text("A")
    output = tmp_path / "out.zip"

    with patch("tools.task_automation.confirm_action", return_value=False):
        result = create_archive.invoke({"paths": [str(tmp_path / "a.txt")], "output_path": str(output)})

    assert "Cancelled" in result
    assert not output.exists()


def test_extract_archive_restores_files(tmp_path):
    archive = tmp_path / "data.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("hello.txt", "hi there")

    destination = tmp_path / "extracted"
    with patch("tools.task_automation.confirm_action", return_value=True):
        result = extract_archive.invoke({"archive_path": str(archive), "destination_dir": str(destination)})

    assert "Extracted 1 file(s)" in result
    assert (destination / "hello.txt").read_text() == "hi there"


def test_extract_archive_blocks_zip_slip(tmp_path):
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../../escaped.txt", "malicious")
        zf.writestr("safe.txt", "fine")

    destination = tmp_path / "extracted"
    with patch("tools.task_automation.confirm_action", return_value=True):
        extract_archive.invoke({"archive_path": str(archive), "destination_dir": str(destination)})

    assert (destination / "safe.txt").exists()
    assert not (tmp_path / "escaped.txt").exists()
