"""
Sandboxed Python code execution.
Runs user code in a restricted subprocess with timeout protection.
"""
import subprocess
import sys
import time
import tempfile
import os


def execute_python(code: str, timeout: int = 5) -> dict:
    """
    Execute Python code in a sandboxed subprocess.
    Returns dict with success status, output, error, and execution time.
    """
    if not code or not isinstance(code, str):
        return {
            "success": False,
            "output": "",
            "error": "No code provided for execution.",
            "execution_time_ms": 0,
        }

    # Create a temporary file for the code
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".sandbox_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    tmp_path = os.path.join(tmp_dir, f"sandbox_{int(time.time() * 1000)}.py")

    try:
        # Write code to temp file
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        start = time.perf_counter()

        # Run in subprocess with restricted environment
        result = subprocess.run(
            [sys.executable, "-u", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": "",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            cwd=tmp_dir,
        )

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return {
            "success": result.returncode == 0,
            "output": result.stdout[:2000] if result.stdout else "",
            "error": result.stderr[:2000] if result.stderr else "",
            "execution_time_ms": elapsed_ms,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"Execution timed out after {timeout} seconds.",
            "execution_time_ms": timeout * 1000,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"Sandbox error: {str(e)}",
            "execution_time_ms": 0,
        }
    finally:
        # Clean up temp file
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
