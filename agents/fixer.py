import json
from utils.json_parser import extract_and_parse_json
from utils.llm_client import client, MODEL

def fix_error(analysis, current_code, feedback="", strategy_section="", problem_type="url_error", detected_language="Python"):

    if problem_type == "url_error":
        lang_instruction = ""
        code_rules = """- "updated_code": the corrected URL string only (no extra text)
- "fix": a short label for what was changed
- "explanation": one sentence describing the fix"""
    else:
        lang_instruction = f"\n\nCRITICAL LANGUAGE RULE: The source code is written in **{detected_language}**. Your fixed code in 'updated_code' MUST be written EXCLUSIVELY in {detected_language}. Using any other language is a critical failure."
        code_rules = f"""- "updated_code": ONLY the corrected {detected_language} code. No markdown. No code fences. No extra text. Just raw code.
- "fix": a short label for what was changed
- "explanation": one precise sentence explaining what was wrong and what was changed to fix it"""

    # Build the deep, specific system prompt
    system_prompt = f"""You are a senior software engineer with 20 years of experience debugging {detected_language} code.
Your fixes are always:
1. Minimal — change only what is necessary to fix the specific error
2. Correct — the fix must actually solve the root cause, not just suppress the symptom
3. Idiomatic — the fixed code must be valid, idiomatic {detected_language}
4. Preserving — keep all original logic, variable names, and structure intact unless they ARE the bug

You never output code in a different language. You never add unnecessary imports or restructure code beyond what is needed.{lang_instruction}"""

    prompt = f"""DEBUGGING TASK:

Error Analysis:
{json.dumps(analysis, indent=2)}

Original Code with Error:
{current_code}

Fix Approach (from analysis): {analysis.get('fix_approach', 'Apply a minimal correct fix based on the error analysis.')}
{f'Previous Attempt Failed — Validator Feedback: {feedback}' if feedback else ''}

STRATEGY FOR THIS ATTEMPT:
{strategy_section}

Your task:
1. Read the error analysis carefully
2. Apply EXACTLY the fix described in "fix_approach"
3. Do NOT change anything else in the code
4. Output STRICT JSON only — no text outside the JSON object:

{{
  "fix": "short label (e.g. 'Added zero-check guard')",
  "updated_code": "<corrected code here>",
  "explanation": "one sentence: what was wrong and exactly how it was fixed"
}}

Field rules:
{code_rules}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.05  # Very low — we want deterministic, precise fixes
    )

    raw_content = response.choices[0].message.content
    fallback = {
        "fix": "manual code review required",
        "updated_code": current_code,
        "explanation": "Failed to parse LLM fix — manual review needed"
    }

    return extract_and_parse_json(raw_content, fallback)