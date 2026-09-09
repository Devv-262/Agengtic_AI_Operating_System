"""
tools/shell_executor.py
-----------------------
Role: Executes shell commands securely. In a full implementation, this should 
require human confirmation for destructive actions.
"""
import subprocess
import platform
from langchain_core.tools import tool

from tools._confirm import confirm_action
from tools._safety import check_command_blocked

@tool
def execute_command(command: str) -> str:
    """Executes a shell command (PowerShell on Windows, bash elsewhere) on the local system."""
    try:
        blocked_error = check_command_blocked(command)
        if blocked_error:
            return blocked_error

        if not confirm_action(f"Run shell command: {command}"):
            return "Cancelled: user did not approve running this command."

        # Use shell=True for windows to allow built-ins like 'dir'
        use_shell = platform.system() == "Windows"
        
        result = subprocess.run(
            command,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=30 # Prevent long-running/hanging commands
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nError Output:\n{result.stderr}"
            
        if not output.strip():
            return "Command executed successfully (no output)."
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

shell_executor_tools = [execute_command]
