"""
tools/system_controller.py
--------------------------
Role: Tools for adjusting system settings like volume and dark/light mode.
Implementation is platform-specific (Windows registry / osascript / amixer).
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
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                return f"Volume set to {level}% on Windows."
            except ImportError:
                return (
                    "Error: 'pycaw' and 'comtypes' are required for Windows volume "
                    "control. Install them with: pip install pycaw comtypes"
                )
        elif os_name == "Darwin":  # macOS
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
            return f"Volume set to {level}% on macOS."
        elif os_name == "Linux":
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", f"{level}%"], check=True)
            return f"Volume set to {level}% on Linux."
        else:
            return f"Volume control not implemented for OS: {os_name}"
    except Exception as e:
        return f"Error setting volume: {str(e)}"

@tool
def set_dark_mode(enabled: bool) -> str:
    """Turns the OS dark mode on (True) or off (False)."""
    os_name = platform.system()
    try:
        if os_name == "Windows":
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            value = 0 if enabled else 1  # 0 = dark, 1 = light
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
            return f"Dark mode {'enabled' if enabled else 'disabled'} on Windows."
        elif os_name == "Darwin":
            script = (
                'tell application "System Events" to tell appearance preferences '
                f'to set dark mode to {"true" if enabled else "false"}'
            )
            subprocess.run(["osascript", "-e", script], check=True)
            return f"Dark mode {'enabled' if enabled else 'disabled'} on macOS."
        else:
            return f"Dark mode toggle not implemented for OS: {os_name}"
    except Exception as e:
        return f"Error setting dark mode: {str(e)}"

system_controller_tools = [get_system_info, set_volume, set_dark_mode]
