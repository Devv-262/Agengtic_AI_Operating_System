"""
tools/__init__.py
-----------------
Role: Makes 'tools' a proper Python package and exposes the canonical list of
      LangChain tools that the OSAgentSystem agent can use.
      Any new tool module added under this package should be imported here and
      its tool object(s) appended to ALL_TOOLS so the agent picks them up
      automatically.
"""
from tools.file_manager       import file_manager_tools
from tools.system_controller  import system_controller_tools
from tools.document_reader    import document_reader_tools
from tools.shell_executor     import shell_executor_tools
# Master list consumed by agent.py when binding tools to the LLM.
ALL_TOOLS: list = [
    *file_manager_tools,
    *system_controller_tools,
    *document_reader_tools,
    *shell_executor_tools,
]
__all__ = [
    "ALL_TOOLS",
    "file_manager_tools",
    "system_controller_tools",
    "document_reader_tools",
    "shell_executor_tools",
]
