import json
import re
from urllib.parse import urlparse

def validate_fix(updated_code: str) -> dict:
    """Validate a URL fix. Returns a dict with 'valid' and 'reason' keys."""
    try:
        if not updated_code or not isinstance(updated_code, str):
            return {
                "valid": False,
                "reason": "Input is not a valid string."
            }

        parsed = urlparse(updated_code.strip())

        if parsed.scheme != "https":
            return {
                "valid": False,
                "reason": "Invalid scheme: Must be 'https'."
            }

        if not parsed.netloc:
            return {
                "valid": False,
                "reason": "Invalid URL: Missing domain (netloc)."
            }

        # Ensure the hostname contains a valid domain structure with a TLD
        if not parsed.hostname or not re.match(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$', parsed.hostname):
            return {
                "valid": False,
                "reason": "Invalid URL: Missing a proper domain structure with a valid TLD (e.g., .com, .org)."
            }

        return {
            "valid": True,
            "reason": "URL is properly formatted"
        }

    except Exception as e:
        return {
            "valid": False,
            "reason": f"Validation completely failed: {str(e)}"
        }
