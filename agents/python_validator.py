import ast

def validate_python_fix(updated_code: str) -> dict:
    """Validate Python code syntax. Returns a dict with 'valid' and 'reason' keys."""
    if not updated_code or not isinstance(updated_code, str):
        return {
            "valid": False,
            "reason": "Input is not a valid string."
        }
    try:
        ast.parse(updated_code)
        return {
            "valid": True,
            "reason": "Python code compiled successfully without syntax errors."
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "reason": f"SyntaxError at line {e.lineno}: {e.msg}"
        }
    except Exception as e:
        return {
            "valid": False,
            "reason": f"Validation completely failed: {str(e)}"
        }
