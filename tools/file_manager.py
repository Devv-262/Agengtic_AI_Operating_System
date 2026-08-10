"""
tools/file_manager.py
---------------------
Role: Tools for reading, moving, copying, and deleting files, as well as smart file organization.
"""
import os
import shutil
from pathlib import Path
from langchain_core.tools import tool

@tool
def list_directory(directory_path: str) -> str:
    """Lists the contents of a specified directory."""
    try:
        path = Path(directory_path).expanduser().resolve()
        if not path.exists():
            return f"Error: Directory '{path}' does not exist."
        if not path.is_dir():
            return f"Error: '{path}' is not a directory."
        
        items = os.listdir(path)
        if not items:
            return "Directory is empty."
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@tool
def read_file(file_path: str) -> str:
    """Reads the text content of a file."""
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return f"Error: File '{path}' does not exist."
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def move_file(source_path: str, destination_path: str) -> str:
    """Moves or renames a file or directory."""
    try:
        src = Path(source_path).expanduser().resolve()
        dst = Path(destination_path).expanduser().resolve()
        if not src.exists():
            return f"Error: Source '{src}' does not exist."
        
        shutil.move(str(src), str(dst))
        return f"Successfully moved '{src}' to '{dst}'."
    except Exception as e:
        return f"Error moving file: {str(e)}"

@tool
def delete_file(file_path: str) -> str:
    """Deletes a file or directory."""
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: File '{path}' does not exist."
        
        if path.is_file():
            os.remove(path)
        elif path.is_dir():
            shutil.rmtree(path)
        return f"Successfully deleted '{path}'."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

file_manager_tools = [list_directory, read_file, move_file, delete_file]
