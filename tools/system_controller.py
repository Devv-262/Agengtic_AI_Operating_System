"""
tools/system_controller.py
--------------------------
Role: Tools for adjusting system settings like volume, brightness, or dark mode.
Note: Implementation details vary heavily by OS (Windows/Mac/Linux).
"""
import platform
import subprocess
from langchain_core.tools import tool

@tool
def get_system_info() -> str:
    """Returns basic information about the current operating system."""
    try:
        os_name = platform.system()
        os_release = platform.release()
        return f"Operating System: {os_name} {os_release}"
    except Exception as e:
        return f"Error getting system info: {str(e)}"

@tool
def set_volume(level: int) -> str:
    """Sets the system volume to a specific level (0-100)."""
    if not (0 <= level <= 100):
        return "Error: Volume level must be between 0 and 100."
        
    os_name = platform.system()
    try:
        if os_name == "Windows":
            # Native volume control on Windows via command line is complex without 3rd party tools
            # This is a placeholder for the actual implementation
            return f"Simulated: Volume set to {level}% on Windows. (Requires pycaw or similar library for actual control)"
        elif os_name == "Darwin": # macOS
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
            return f"Volume set to {level}% on macOS."
        elif os_name == "Linux":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"])
            return f"Volume set to {level}% on Linux."
        else:
            return f"Volume control not implemented for OS: {os_name}"
    except Exception as e:
        return f"Error setting volume: {str(e)}"

system_controller_tools = [get_system_info, set_volume]
