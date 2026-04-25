import json
import re

def extract_and_parse_json(text_response, fallback):
    """
    Safely extracts and parses JSON from a messy LLM text response.
    Returns the fallback dict if parsing fails entirely.
    """
    try:
        # First attempt: simply try to parse the entire text as JSON
        return json.loads(text_response)
    except json.JSONDecodeError:
        pass

    try:
        # Second attempt: use regex to find the first JSON-like block {}
        # This matches the first occurrence of curly braces and their contents
        match = re.search(r'\{.*\}', text_response, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
    except Exception:
        pass

    # If all parsing attempts fail, return the safe fallback
    return fallback
