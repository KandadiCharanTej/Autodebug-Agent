# Entry point for the autodebug agent
import asyncio
import json
import logging
import os
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.analyzer import analyze_error
from agents.fixer import fix_error
from agents.python_validator import validate_python_fix
from agents.sandbox import execute_python
from agents.simplifier import simplify_fix
from agents.validator import validate_fix
from utils.llm_client import client, MODEL
from utils.json_parser import extract_and_parse_json
from utils.pattern_store import save_pattern, find_similar, get_pattern_count

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────
app = FastAPI(title="AutoDebug Agent", version="2.0.0")

# CORS — allow frontend on different origins during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only mount static if the directory exists (it shouldn't crash if dir created after)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")


# ── Request models ─────────────────────────────────────────────────
class DebugRequest(BaseModel):
    error: str = ""
    code: str = ""

class FollowUpRequest(BaseModel):
    question: str = ""
    original_error: str = ""
    original_code: str = ""
    fixed_code: str = ""
    analysis: dict = {}
    fix_explanation: str = ""


# ── Helpers ────────────────────────────────────────────────────────
def classify_problem(error: str, code: str) -> str:
    combined = (error + " " + code).lower()
    if "http" in combined or "url" in combined or "domain" in combined:
        return "url_error"
    if "traceback" in combined or "error" in combined or "exception" in combined or "def " in combined or "import " in combined:
        return "python_error"
    return "general_code_error"

def detect_language(code: str) -> str:
    """Detect the programming language from code heuristics."""
    if any(k in code for k in ["def ", "import ", "print(", "elif ", "self.", "__init__"]):
        return "Python"
    if any(k in code for k in ["function ", "const ", "let ", "var ", "console.log", "=>", "require("]):
        return "JavaScript"
    if any(k in code for k in ["public class", "System.out", "void main", "import java"]):
        return "Java"
    if any(k in code for k in ["#include", "cout <<", "cin >>", "int main(", "std::"]):
        return "C++"
    if any(k in code for k in ["using System", "Console.Write", "namespace ", "public static void Main"]):
        return "C#"
    if any(k in code for k in ["<?php", "echo ", "$_GET", "$_POST"]):
        return "PHP"
    if any(k in code for k in ["fn ", "let mut", "println!", "use std"]):
        return "Rust"
    if any(k in code for k in ["func ", "fmt.Println", "package main", ":= "]):
        return "Go"
    return "the same programming language as the input"


def compute_confidence(analysis: dict, validation: dict, sandbox_result: dict | None, retries: int) -> int:
    """Compute a confidence score (0–100) from multiple signals."""
    score = 50  # Base score

    # LLM confidence
    llm_confidence = (analysis.get("confidence", "medium") or "medium").lower()
    if llm_confidence == "high":
        score += 30
    elif llm_confidence == "medium":
        score += 15
    elif llm_confidence == "low":
        score -= 10

    # Validation
    if validation and validation.get("valid"):
        score += 10
    elif validation:
        score -= 20

    # Sandbox execution
    if sandbox_result:
        if sandbox_result.get("success"):
            score += 15
        else:
            score -= 10

    # Retry penalty
    score -= max(0, (retries - 1)) * 8

    return max(0, min(100, score))


# ── SSE Streaming Debug Endpoint ──────────────────────────────────
@app.post("/debug-stream")
async def debug_stream(data: DebugRequest):
    error = data.error.strip()
    code = data.code.strip()

    if not error and not code:
        raise HTTPException(status_code=400, detail="Please provide an error message or source code.")

    async def event_generator():
        try:
            problem_type = classify_problem(error, code)
            detected_language = detect_language(code)

            # ── Step 0: Pattern Memory Lookup ──────────────────────
            yield _sse_event("status", {"step": "pattern_lookup", "message": "🧠 Checking pattern memory..."})
            await asyncio.sleep(0.1)

            similar_pattern = None
            try:
                # Need error_type from a quick classification
                error_type_guess = error.split(":")[0].strip() if ":" in error else "Unknown"
                cause_guess = error
                similar_pattern = find_similar(error_type_guess, cause_guess)
            except Exception:
                pass

            if similar_pattern:
                yield _sse_event("pattern_match", similar_pattern)

            # ── Step 1: Analyze ────────────────────────────────────
            yield _sse_event("status", {"step": "analyzing", "message": "🔍 Analyzing error..."})
            await asyncio.sleep(0.05)

            analysis = analyze_error(error, code)

            llm_language = analysis.get("language", "")
            if llm_language and llm_language.lower() not in ("unknown", ""):
                detected_language = llm_language

            yield _sse_event("analysis", {
                "analysis": analysis,
                "detected_language": detected_language,
                "problem_type": problem_type,
            })

            # ── Step 2–4: Fix → Validate → Retry loop ─────────────
            yield _sse_event("status", {"step": "fixing", "message": "🔧 Generating fix..."})
            await asyncio.sleep(0.05)

            max_retries = 3
            fix = None
            validation_status = None
            feedback = ""
            current_code = code
            steps = []
            updated_code = ""

            for attempt in range(max_retries):
                if problem_type == "url_error":
                    if attempt == 0:
                        strategy = "Detected missing protocol → added https"
                        prompt_strategy = "Retry 1: Prepend 'http://' to the URL (do nothing else)."
                    elif attempt == 1:
                        strategy = "Detected missing domain → appended .com"
                        prompt_strategy = "Retry 2: Append '.com' to the end of the URL (do nothing else)."
                    else:
                        strategy = "Normalized formatting"
                        prompt_strategy = "Retry 3: Change 'http://' to 'https://' and normalize formatting."
                else:
                    if attempt == 0:
                        strategy = "Detected syntax/logical error → attempting functional fix"
                        prompt_strategy = "Retry 1: Analyze the Python traceback. Identify the root cause and generate a functional code fix. Return only valid Python code."
                    elif attempt == 1:
                        strategy = "Syntax failure → correcting syntax structure"
                        prompt_strategy = "Retry 2: The previous Python code failed syntax validation. Correct the syntax errors and ensure strict Python formatting."
                    else:
                        strategy = "Persisting errors → applying safe fallback logic"
                        prompt_strategy = "Retry 3: Simplify the logic to ensure it bypasses the error safely. Ensure no SyntaxErrors remain."

                logger.info(f"Step 2 (attempt {attempt + 1}): Fixing with strategy: {strategy}")

                if attempt > 0:
                    yield _sse_event("status", {"step": "retrying", "message": f"🔄 Retry {attempt + 1}: {strategy}"})
                    await asyncio.sleep(0.05)

                fix = fix_error(analysis, current_code, feedback, prompt_strategy, problem_type, detected_language)
                updated_code = fix.get("updated_code", "")

                if isinstance(updated_code, dict):
                    updated_code = next(iter(updated_code.values()), "")
                    fix["updated_code"] = updated_code

                # Validate
                yield _sse_event("status", {"step": "validating", "message": "✅ Validating fix..."})
                await asyncio.sleep(0.05)

                if problem_type == "url_error":
                    validation_status = validate_fix(updated_code)
                else:
                    validation_status = validate_python_fix(updated_code)

                steps.append(f"Step {attempt + 1}: {strategy} → {updated_code}")

                if validation_status.get("valid") is True:
                    steps.append(f"Step {attempt + 2}: Validation passed")
                    break

                feedback = validation_status.get("reason", "Unknown validation error.")
                current_code = updated_code

                yield _sse_event("retry", {
                    "attempt": attempt + 1,
                    "reason": feedback,
                })

            yield _sse_event("fix", {
                "fix": fix,
                "validation": validation_status,
                "steps": steps,
                "retries_taken": attempt + 1,
            })

            # ── Step 5: Sandbox Execution (Python only) ────────────
            sandbox_result = None
            if detected_language.lower() == "python" and validation_status and validation_status.get("valid"):
                yield _sse_event("status", {"step": "executing", "message": "🖥️ Running code in sandbox..."})
                await asyncio.sleep(0.05)

                sandbox_result = execute_python(updated_code)
                yield _sse_event("execution", sandbox_result)

            # ── Step 6: Optimization ───────────────────────────────
            optimization_note = None
            if validation_status and validation_status.get("valid") is True and fix:
                yield _sse_event("status", {"step": "optimizing", "message": "⚡ Optimizing solution..."})
                await asyncio.sleep(0.05)

                error_type = analysis.get("error_type", "Unknown") if isinstance(analysis, dict) else "Unknown"
                simplification = simplify_fix(
                    working_code=updated_code,
                    original_code=code,
                    error_type=error_type,
                    detected_language=detected_language,
                    problem_type=problem_type
                )
                final_solution = simplification.get("final_solution", updated_code)
                optimization_note = simplification.get("optimization_note", "")
                if simplification.get("simplified"):
                    fix["updated_code"] = final_solution
                    updated_code = final_solution
                    steps.append(f"Optimization: {optimization_note}")

                yield _sse_event("optimization", {
                    "optimization_note": optimization_note,
                    "simplified": simplification.get("simplified", False),
                    "updated_code": fix.get("updated_code", updated_code),
                })

            # ── Step 7: Confidence Score ───────────────────────────
            confidence = compute_confidence(analysis, validation_status, sandbox_result, attempt + 1)

            # ── Step 8: Save to Pattern Memory ─────────────────────
            if validation_status and validation_status.get("valid"):
                try:
                    save_pattern(
                        error_type=analysis.get("error_type", "Unknown"),
                        cause=analysis.get("cause", ""),
                        fix_explanation=fix.get("explanation", ""),
                        updated_code=updated_code,
                        language=detected_language,
                    )
                except Exception:
                    pass

            # ── Final complete event ───────────────────────────────
            yield _sse_event("complete", {
                "problem_type": problem_type,
                "detected_language": detected_language,
                "analysis": analysis,
                "fix": fix,
                "validation": validation_status,
                "optimization_note": optimization_note,
                "retries_taken": attempt + 1,
                "steps": steps,
                "original_code": code,
                "confidence_score": confidence,
                "sandbox_result": sandbox_result,
                "similar_pattern": similar_pattern,
                "patterns_stored": get_pattern_count(),
            })

        except Exception as e:
            logger.error(f"Debug pipeline failed: {traceback.format_exc()}")
            yield _sse_event("error", {"detail": f"The debug agent encountered an error: {str(e)}"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


# ── Legacy non-streaming endpoint (fallback) ──────────────────────
@app.post("/debug")
async def debug(data: DebugRequest):
    error = data.error.strip()
    code = data.code.strip()

    if not error and not code:
        raise HTTPException(status_code=400, detail="Please provide an error message or source code.")

    try:
        problem_type = classify_problem(error, code)
        detected_language = detect_language(code)

        # Pattern lookup
        error_type_guess = error.split(":")[0].strip() if ":" in error else "Unknown"
        similar_pattern = find_similar(error_type_guess, error)

        # ── Step 1: Analyze ────────────────────────────────────
        logger.info("Step 1: Analyzing error...")
        analysis = analyze_error(error, code)

        llm_language = analysis.get("language", "")
        if llm_language and llm_language.lower() not in ("unknown", ""):
            detected_language = llm_language

        # ── Step 2–4: Fix → Validate → Retry loop ─────────────
        max_retries = 3
        fix = None
        validation_status = None
        feedback = ""
        current_code = code
        steps = []

        for attempt in range(max_retries):
            if problem_type == "url_error":
                if attempt == 0:
                    strategy = "Detected missing protocol → added https"
                    prompt_strategy = "Retry 1: Prepend 'http://' to the URL (do nothing else)."
                elif attempt == 1:
                    strategy = "Detected missing domain → appended .com"
                    prompt_strategy = "Retry 2: Append '.com' to the end of the URL (do nothing else)."
                else:
                    strategy = "Normalized formatting"
                    prompt_strategy = "Retry 3: Change 'http://' to 'https://' and normalize formatting."
            else:
                if attempt == 0:
                    strategy = "Detected syntax/logical error → attempting functional fix"
                    prompt_strategy = "Retry 1: Analyze the Python traceback. Identify the root cause and generate a functional code fix. Return only valid Python code."
                elif attempt == 1:
                    strategy = "Syntax failure → correcting syntax structure"
                    prompt_strategy = "Retry 2: The previous Python code failed syntax validation. Correct the syntax errors and ensure strict Python formatting."
                else:
                    strategy = "Persisting errors → applying safe fallback logic"
                    prompt_strategy = "Retry 3: Simplify the logic to ensure it bypasses the error safely. Ensure no SyntaxErrors remain."

            logger.info(f"Step 2 (attempt {attempt + 1}): Fixing with strategy: {strategy}")
            fix = fix_error(analysis, current_code, feedback, prompt_strategy, problem_type, detected_language)

            updated_code = fix.get("updated_code", "")

            if isinstance(updated_code, dict):
                updated_code = next(iter(updated_code.values()), "")
                fix["updated_code"] = updated_code

            logger.info(f"Step 3 (attempt {attempt + 1}): Validating fix...")
            if problem_type == "url_error":
                validation_status = validate_fix(updated_code)
            else:
                validation_status = validate_python_fix(updated_code)

            steps.append(f"Step {attempt + 1}: {strategy} → {updated_code}")

            if validation_status.get("valid") is True:
                steps.append(f"Step {attempt + 2}: Validation passed")
                break

            feedback = validation_status.get("reason", "Unknown validation error.")
            current_code = updated_code

        # ── Sandbox Execution ──────────────────────────────────
        sandbox_result = None
        if detected_language.lower() == "python" and validation_status and validation_status.get("valid"):
            sandbox_result = execute_python(updated_code)

        # ── Step 5: Optimization ───────────────────────────────
        optimization_note = None
        if validation_status and validation_status.get("valid") is True and fix:
            logger.info("Step 4: Optimizing/simplifying fix...")
            error_type = analysis.get("error_type", "Unknown") if isinstance(analysis, dict) else "Unknown"
            simplification = simplify_fix(
                working_code=updated_code,
                original_code=code,
                error_type=error_type,
                detected_language=detected_language,
                problem_type=problem_type
            )
            final_solution = simplification.get("final_solution", updated_code)
            optimization_note = simplification.get("optimization_note", "")
            if simplification.get("simplified"):
                fix["updated_code"] = final_solution
                steps.append(f"Optimization: {optimization_note}")

        # Confidence Score
        confidence = compute_confidence(analysis, validation_status, sandbox_result, attempt + 1)

        # Save pattern
        if validation_status and validation_status.get("valid"):
            try:
                save_pattern(
                    error_type=analysis.get("error_type", "Unknown"),
                    cause=analysis.get("cause", ""),
                    fix_explanation=fix.get("explanation", ""),
                    updated_code=fix.get("updated_code", updated_code),
                    language=detected_language,
                )
            except Exception:
                pass

        logger.info("✅ Debug pipeline complete.")
        return {
            "problem_type": problem_type,
            "detected_language": detected_language,
            "analysis": analysis,
            "fix": fix,
            "validation": validation_status,
            "optimization_note": optimization_note,
            "retries_taken": attempt + 1,
            "steps": steps,
            "original_code": code,
            "confidence_score": confidence,
            "sandbox_result": sandbox_result,
            "similar_pattern": similar_pattern,
            "patterns_stored": get_pattern_count(),
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Debug pipeline failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"The debug agent encountered an error: {str(e)}"
        )


# ── Conversational Follow-Up Endpoint ─────────────────────────────
@app.post("/followup")
async def followup(data: FollowUpRequest):
    question = data.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please provide a question.")

    try:
        context = f"""Context for your answer:

ORIGINAL ERROR:
{data.original_error}

ORIGINAL CODE:
{data.original_code}

ANALYSIS:
{json.dumps(data.analysis, indent=2) if data.analysis else 'N/A'}

FIX EXPLANATION:
{data.fix_explanation}

FIXED CODE:
{data.fixed_code}
"""
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful, expert software engineer. You are answering follow-up questions about a code fix that was just applied. Be concise, precise, and helpful. Use short paragraphs. If the user asks to modify the fix, provide the updated code."
                },
                {"role": "user", "content": f"{context}\n\nUSER QUESTION: {question}"},
            ],
            temperature=0.3,
        )

        answer = response.choices[0].message.content
        return {"answer": answer}

    except Exception as e:
        logger.error(f"Follow-up failed: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Follow-up failed: {str(e)}"
        )
