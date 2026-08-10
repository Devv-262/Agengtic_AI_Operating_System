"""
tools/shell_executor.py
-----------------------
Role: Executes shell commands securely. In a full implementation, this should 
require human confirmation for destructive actions.
"""
import subprocess
import platform
from langchain_core.tools import tool

@tool
def execute_command(command: str) -> str:
    """Executes a shell command on the local system."""
    try:
        # Warning: Direct execution of LLM generated commands is dangerous.
        # In a real app, you would add a human-in-the-loop confirmation step here.
        
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
