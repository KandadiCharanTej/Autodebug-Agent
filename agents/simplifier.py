import json
from utils.json_parser import extract_and_parse_json
from utils.llm_client import client, MODEL

def simplify_fix(working_code: str, original_code: str, error_type: str, detected_language: str, problem_type: str) -> dict:
    """
    Takes a validated working fix and returns the simplest, most readable version.
    Only called after the fix has already passed validation.
    """
    # URLs don't need simplification — return as-is
    if problem_type == "url_error":
        return {"simplified_code": working_code, "simplified": False, "reason": "URL fixes do not require simplification."}

    # Detect if this is SQL for domain-specific rules
    is_sql = detected_language.lower() in ("sql", "sqlite", "postgresql", "mysql", "tsql")
    sql_rules = """
SQL-specific rules (CRITICAL):
- PREFER WHERE clause filtering over CASE WHEN logic when the goal is simply to exclude rows
- PREFER COALESCE(col, 0) over CASE WHEN col IS NULL THEN 0 END
- PREFER aggregation with WHERE over wrapping in CASE
- AVOID nested subqueries if a JOIN or simple WHERE achieves the same result
- Remove GROUP BY columns that are not needed in the SELECT""" if is_sql else ""

    prompt = f"""You are a senior {detected_language} engineer and code quality expert with 20 years of experience writing clean, minimal, production-grade code.

A working fix has been generated for this error:
Error Type: {error_type}

Original (buggy) code:
{original_code}

Current working fix (already validated as correct):
{working_code}

Your task:
Act as an experienced engineer doing a code review. Determine if this fix is over-engineered and whether a simpler, cleaner solution exists.
{sql_rules}

General simplification rules (apply in order of priority):
1. PREFER filtering/guard conditions over conditional logic — simpler is better
2. REMOVE redundant conditions or checks that are not needed
3. AVOID unnecessary try/except if a guard condition works
4. AVOID CASE/switch statements if a simpler expression achieves the same result
5. PREFER standard library/built-in functions over manual implementations
6. ONLY minimal changes — preserve variable names, function signatures, and structure
7. If the fix is already minimal and correct, mark simplified = false and return it unchanged

Return STRICT JSON only — no explanation outside the JSON:
{{
  "final_solution": "<the cleanest correct code — simplified if possible, else same as working fix>",
  "simplified": true or false,
  "optimization_note": "one clear sentence explaining what was simplified and why, or why no change was needed"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"You are a {detected_language} code quality expert. You simplify code without changing its behavior. You never introduce bugs. You prefer idiomatic, readable solutions."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.05
    )

    raw_content = response.choices[0].message.content
    fallback = {
        "final_solution": working_code,
        "simplified": False,
        "optimization_note": "Simplification failed — using validated fix as-is."
    }

    return extract_and_parse_json(raw_content, fallback)
