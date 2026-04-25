import json
from utils.json_parser import extract_and_parse_json
from utils.llm_client import client, MODEL

def analyze_error(error, code):
    prompt = f"""You are a senior software engineer and expert debugger. Your job is to perform a deep, precise analysis of the given error and code.

ERROR MESSAGE:
{error}

SOURCE CODE:
{code}

Think step by step:
1. What is the exact error type and what does it mean?
2. On which line / in which part of the code does it originate?
3. What is the root cause — not just the symptom, but WHY it happens?
4. What is the minimal, correct fix needed?

Return STRICT JSON only — no markdown, no explanation outside the JSON:
{{
  "error_type": "exact error class name (e.g. ZeroDivisionError, SyntaxError, TypeError)",
  "line_hint": "line number or code snippet where the error occurs, or 'unknown'",
  "cause": "precise explanation of WHY the error happens",
  "fix_approach": "concrete description of exactly what code change is needed to fix it",
  "language": "detected programming language",
  "confidence": "high/medium/low"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an expert software debugger. You always return precise, accurate, factual JSON analysis. Never guess. If unsure, say so in the confidence field."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1  # Low temperature = more deterministic, accurate output
    )

    raw_content = response.choices[0].message.content
    fallback = {
        "error_type": "Unknown Error",
        "line_hint": "unknown",
        "cause": "Failed to parse LLM analysis",
        "fix_approach": "Manual review required",
        "language": "unknown",
        "confidence": "low"
    }

    return extract_and_parse_json(raw_content, fallback)
