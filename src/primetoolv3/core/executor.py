import subprocess
from typing import Optional, Sequence

from primetoolv3.core.environment import environment_exists, get_venv_python
from primetoolv3.utils.paths import get_script_dir

def execute_tool(arguments: Optional[Sequence[str]] = None) -> int:
    """
    Execute the downloaded tool using its isolated python environment
    Args:
        arguments: Command-line arguments to forward to tool.py
    Returns:
        Tools exit code.
    """
    tool_script = get_script_dir()/"tool.py"
    if not tool_script.is_file():
        raise FileNotFoundError(f"Tool script not found: {tool_script}")

    if not environment_exists():
        raise RuntimeError("Tool environment does not exist. Run 'prime-tool-v3 run' to initialize it")
    venv_python = get_venv_python()
    command = [str(venv_python), str(tool_script), *(arguments or [])]

    try:
        result = subprocess.run(command)
        return result.returncode
    except OSError as error:
        raise RuntimeError(f"Failed to execute tool: {error}") from error
