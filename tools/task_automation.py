"""
tools/task_automation.py
--------------------------
Role: Task Automation — chaining-friendly tools for batch image resizing
and zip archive creation/extraction, so requests like "resize all images in
this folder to 1080p and zip them" can be done by the ReAct loop calling
these tools in sequence (no separate orchestration layer needed).
"""
import zipfile
from pathlib import Path
from typing import List

from langchain_core.tools import tool

from tools._confirm import confirm_action
from tools._safety import check_path_allowed

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


@tool
def resize_images(directory_path: str, max_dimension: int = 1920, output_subfolder: str = "resized") -> str:
    """
    Resizes every image directly inside a directory so its longest side is
    at most max_dimension pixels (aspect ratio preserved), saving results
    into a subfolder (default "resized") rather than overwriting originals.
    Images already smaller than max_dimension are copied through unchanged.
    """
    try:
        try:
            from PIL import Image
        except ImportError:
            return "Error: 'Pillow' is required to resize images. Install it with: pip install Pillow"

        directory = Path(directory_path).expanduser().resolve()
        sandbox_error = check_path_allowed(directory)
        if sandbox_error:
            return sandbox_error
        if not directory.is_dir():
            return f"Error: '{directory}' is not a directory."

        images = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTENSIONS]
        if not images:
            return f"No images found directly in '{directory}'."

        output_dir = directory / output_subfolder
        dest_error = check_path_allowed(output_dir)
        if dest_error:
            return dest_error

        if not confirm_action(f"Resize {len(images)} image(s) in '{directory}' to max {max_dimension}px, saving into '{output_dir}'"):
            return "Cancelled: user did not approve the resize."

        output_dir.mkdir(parents=True, exist_ok=True)
        resized, failed = 0, []
        for path in images:
            try:
                with Image.open(path) as img:
                    img.thumbnail((max_dimension, max_dimension))
                    img.save(output_dir / path.name)
                resized += 1
            except Exception as e:
                failed.append(f"{path.name}: {e}")

        summary = f"Resized {resized} image(s) into '{output_dir}'."
        if failed:
            summary += f"\n{len(failed)} failed:\n" + "\n".join(failed)
        return summary

    except Exception as e:
        return f"Error resizing images: {str(e)}"


@tool
def create_archive(paths: List[str], output_path: str) -> str:
    """Zips the given files/folders into a single .zip archive at output_path."""
    try:
        resolved_sources = [Path(p).expanduser().resolve() for p in paths]
        output = Path(output_path).expanduser().resolve()

        for src in resolved_sources:
            sandbox_error = check_path_allowed(src)
            if sandbox_error:
                return sandbox_error
            if not src.exists():
                return f"Error: '{src}' does not exist."
        dest_error = check_path_allowed(output)
        if dest_error:
            return dest_error

        listing = "\n".join(f"  {p}" for p in resolved_sources)
        if not confirm_action(f"Create archive '{output}' from:\n{listing}"):
            return "Cancelled: user did not approve the archive."

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for src in resolved_sources:
                if src.is_file():
                    zf.write(src, arcname=src.name)
                else:
                    for file_path in src.rglob("*"):
                        if file_path.is_file():
                            zf.write(file_path, arcname=str(file_path.relative_to(src.parent)))

        return f"Created archive '{output}' with {len(resolved_sources)} top-level item(s)."

    except Exception as e:
        return f"Error creating archive: {str(e)}"


@tool
def extract_archive(archive_path: str, destination_dir: str) -> str:
    """Extracts a .zip archive into destination_dir."""
    try:
        archive = Path(archive_path).expanduser().resolve()
        destination = Path(destination_dir).expanduser().resolve()

        sandbox_error = check_path_allowed(archive) or check_path_allowed(destination)
        if sandbox_error:
            return sandbox_error
        if not archive.is_file():
            return f"Error: '{archive}' does not exist."

        if not confirm_action(f"Extract '{archive}' into '{destination}'"):
            return "Cancelled: user did not approve the extraction."

        destination.mkdir(parents=True, exist_ok=True)
        extracted = 0
        with zipfile.ZipFile(archive, "r") as zf:
            for member in zf.namelist():
                target = (destination / member).resolve()
                # Guard against zip-slip: refuse any entry that would land
                # outside destination_dir after path resolution.
                if destination != target and destination not in target.parents:
                    continue
                if member.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source, open(target, "wb") as out_file:
                    out_file.write(source.read())
                extracted += 1

        return f"Extracted {extracted} file(s) into '{destination}'."

    except Exception as e:
        return f"Error extracting archive: {str(e)}"


task_automation_tools = [resize_images, create_archive, extract_archive]
