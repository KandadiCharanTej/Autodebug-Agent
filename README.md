# 🤖 Agentic Code Debugger

**An Intelligent, Self-Correcting AI-Powered Code Debugging Agent**

Agentic Code Debugger is an autonomous code debugging system that analyzes, fixes, validates, and executes buggy code in real-time. Unlike one-shot code generation tools, this agent implements an iterative reasoning loop that continuously attempts to fix errors, learns from validation feedback, and applies self-correction strategies across up to 3 retries per bug.

The system combines advanced LLM reasoning with deterministic validation and sandbox execution to deliver production-ready code fixes with explainability.

---

## ✨ Core Features

### 🎯 **Multi-Language Support**
- Intelligently detects and handles errors across:
  - **Python** (including syntax errors, runtime exceptions, and logical bugs)
  - **JavaScript** (ES6+ syntax and runtime issues)
  - **Java**, **C++**, **C#**, **PHP**, **Rust**, **Go**
  - **SQL** queries and database errors
  - **URL/HTTP errors** (malformed URLs, missing protocols, domain issues)

### 🔄 **Self-Correcting Iteration Loop**
- Implements a **Fix → Validate → Retry** sequence with up to 3 intelligent retry strategies
- Each retry adapts based on validation feedback:
  - **Retry 1**: Functional fix (addressing logic errors)
  - **Retry 2**: Syntax correction (fixing structural problems)
  - **Retry 3**: Safe fallback logic (applying defensive patterns)
- Terminates early upon successful validation—no unnecessary iterations

### 🧠 **Pattern Memory System**
- Stores successful error-to-fix mappings in persistent `patterns.json`
- Before analyzing each new error, checks historical patterns for similar issues
- Rapidly retrieves past solutions with 85%+ similarity match confidence
- Enables continuous learning—the system gets smarter with each resolved bug
- Caps storage at 100 patterns to maintain performance

### 🏝️ **Python Code Execution Sandbox**
- Safely executes Python code within a controlled environment
- Validates that fixes actually work before returning to the user
- Captures output, exceptions, and runtime behavior
- Detects silent failures and incorrect logic that syntax validation would miss
- Uses process isolation to prevent malicious code execution

### ✂️ **Code Optimization Layer**
- Not satisfied with merely "making it work"—the agent further refines generated code
- Removes redundancy, improves readability, and applies best practices
- Ensures final output is clean, maintainable, and follows language conventions

### 📡 **Real-Time Streaming with Server-Sent Events (SSE)**
- Streams step-by-step reasoning in real-time to the frontend
- Users observe:
  - Pattern lookup results
  - LLM analysis and root cause identification
  - Fix generation strategies
  - Validation outcomes
  - Retry attempts and feedback
  - Sandbox execution results
  - Code optimization progress
- Creates an engaging, transparent debugging experience

### 💬 **Follow-Up Conversational Interface**
- After a fix is generated, engage with the AI via a built-in chat interface
- Ask clarifying questions about:
  - Why the bug occurred
  - How the fix works
  - Alternative approaches
  - Best practices for similar issues
- Maintains context from the debugging session

### 📊 **Confidence Scoring**
- Computes an overall confidence score (0–100) for each fix based on:
  - LLM confidence from analysis phase
  - Validation success/failure signals
  - Sandbox execution results
  - Retry count (fewer retries = higher confidence)
- Helps users assess reliability of proposed solutions

---

## 📁 Project Structure

```
autodebug-agent/
├── agents/                           # Core autonomous agent modules
│   ├── analyzer.py                   # Step 1: Analyzes error & identifies root cause
│   │                                    ├─ Parses stack traces
│   │                                    ├─ Classifies error type
│   │                                    └─ Returns structured JSON analysis
│   │
│   ├── fixer.py                      # Step 2: Generates code fix strategies
│   │                                    ├─ Creates context-aware prompts
│   │                                    ├─ Calls LLM with retry strategies
│   │                                    └─ Extracts code from LLM response
│   │
│   ├── python_validator.py           # Step 3a: Syntax & semantic validation for Python
│   │                                    ├─ Compiles code to AST
│   │                                    ├─ Checks for syntax errors
│   │                                    └─ Validates basic semantics
│   │
│   ├── validator.py                  # Step 3b: Generic validation for other languages
│   │                                    ├─ Regex-based pattern matching
│   │                                    ├─ Heuristic-based checks
│   │                                    └─ Format validation (URLs, SQL, etc.)
│   │
│   ├── sandbox.py                    # Step 4: Sandboxed Python code execution
│   │                                    ├─ Process-isolated execution
│   │                                    ├─ Timeout protection
│   │                                    ├─ Output/exception capture
│   │                                    └─ Prevents malicious code impact
│   │
│   └── simplifier.py                 # Step 5: Code optimization & refactoring
│                                        ├─ Removes redundancy
│                                        ├─ Improves readability
│                                        └─ Applies language idioms
│
├── utils/                            # Utility modules
│   ├── llm_client.py                 # LLM client configuration
│   │                                    ├─ Initializes Groq API client
│   │                                    ├─ Sets model name (llama-3.3-70b-versatile)
│   │                                    └─ Manages API communication
│   │
│   ├── json_parser.py                # Robust JSON extraction from LLM responses
│   │                                    ├─ Handles incomplete/malformed JSON
│   │                                    ├─ Extracts code blocks
│   │                                    └─ Fallback parsing strategies
│   │
│   └── pattern_store.py              # Pattern Memory persistence layer
│                                        ├─ Loads/saves patterns.json
│                                        ├─ Similarity matching (SequenceMatcher)
│                                        ├─ Deduplication logic
│                                        └─ Pattern cap management (max 100)
│
├── static/                           # Frontend web assets
│   ├── index.html                    # Single-page app HTML structure
│   │                                    ├─ Error/code input fields
│   │                                    ├─ Real-time results panel
│   │                                    ├─ Follow-up chat interface
│   │                                    └─ Dark theme UI
│   │
│   ├── script.js                     # Frontend interactivity & SSE parsing
│   │                                    ├─ Handles /debug-stream endpoint connection
│   │                                    ├─ Parses and displays SSE events
│   │                                    ├─ Real-time updates on UI
│   │                                    ├─ Follow-up chat message handling
│   │                                    └─ Syntax highlighting with Prism.js
│   │
│   └── style.css                     # Responsive vanilla CSS styling
│                                        ├─ Dark theme with accent colors
│                                        ├─ Mobile-responsive layout
│                                        └─ Smooth animations & transitions
│
├── patterns.json                     # Persistent pattern memory (auto-generated)
│                                        ├─ Stores up to 100 error-fix mappings
│                                        ├─ JSON array format
│                                        └─ Updated after each successful fix
│
├── main.py                           # FastAPI backend application entry point
│                                        ├─ Defines DebugRequest/FollowUpRequest models
│                                        ├─ Orchestrates the debugging pipeline
│                                        ├─ Implements /debug-stream SSE endpoint
│                                        ├─ Implements /followup chat endpoint
│                                        ├─ Serves static frontend
│                                        └─ Handles CORS for development
│
├── requirements.txt                  # Python dependencies specification
│
├── .env                              # Environment variables (not in git)
│                                        └─ GROQ_API_KEY=your_api_key_here
│
└── README.md                         # This file
```

---

## 🛠️ Technologies Used

### **Backend Stack**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI (Python 3.9+) | Async web server with auto-documentation |
| **Server** | Uvicorn with `[standard]` extras | High-performance ASGI server with WebSocket support |
| **LLM Provider** | Groq AI API | Fast inference using `llama-3.3-70b-versatile` model |
| **LLM Client** | OpenAI Python SDK | Unified client interface compatible with Groq |
| **Code Execution** | Python subprocess module | Safe sandboxed Python code execution |
| **Config Management** | python-dotenv | Environment variable loading from `.env` |

### **Frontend Stack**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Markup** | HTML5 | Semantic structure with responsive meta tags |
| **Styling** | Vanilla CSS3 | No build tools required; pure CSS Grid/Flexbox |
| **Interactivity** | Vanilla JavaScript (ES6+) | Lightweight client-side logic; no frameworks |
| **Code Highlighting** | Prism.js | Syntax highlighting for 100+ languages |
| **Real-Time Updates** | Server-Sent Events (SSE) | Streaming from `/debug-stream` endpoint |

### **Data Storage**
| Component | Format | Purpose |
|-----------|--------|---------|
| **Pattern Memory** | JSON file (`patterns.json`) | Persistent storage of learned fixes |
| **Session Data** | In-memory or JSON payloads | Temporary debugging context |

---

## 🚀 Getting Started

### Prerequisites
- **Python**: Version 3.9 or later
- **Groq API Key**: Free or paid tier from [Groq Console](https://console.groq.com/keys)
- **Network Access**: Internet connection to reach Groq API
- **Operating System**: Windows, macOS, or Linux

### Installation & Setup

#### Step 1: Clone or Navigate to the Project
```bash
cd /path/to/autodebug-agent
```

#### Step 2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows
.venv\Scripts\activate

# Activate on macOS/Linux
source .venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

The following packages will be installed:
- `fastapi` — Web framework
- `uvicorn[standard]` — ASGI server with WebSocket support
- `openai` — LLM client library (works with Groq API)
- `python-dotenv` — Environment variable loader

#### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

**How to obtain a Groq API key:**
1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Create an API key
4. Copy and paste into `.env`

#### Step 5: Launch the Application
```bash
# Start the FastAPI server with auto-reload enabled (development mode)
uvicorn main:app --reload

# Or without auto-reload (production mode)
uvicorn main:app

# To specify a custom host and port:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see output similar to:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Step 6: Access the Application
Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

You should see the Agentic Code Debugger web interface with:
- **Input Section**: Fields for error message and source code
- **Run Debug Agent Button**: Trigger the debugging pipeline
- **Results Panel**: Real-time streaming of debug steps
- **Follow-Up Chat**: Ask questions about the fix

---

## 🔍 How It Works

### **Debugging Pipeline Overview**

```
User Input (Error + Code)
        ↓
┌───────────────────────────────────────────────────────────────┐
│ STEP 0: Pattern Memory Lookup                                 │
│ - Check if similar error has been seen before               │
│ - If match found (similarity > 85%), show historical fix    │
│ - Accelerates resolution for repeated bugs                  │
└───────────────────────────────────────────────────────────────┘
        ↓ (no match or used as reference)
┌───────────────────────────────────────────────────────────────┐
│ STEP 1: Error Analysis                                        │
│ - Parse error message and source code                       │
│ - Classify error type (SyntaxError, TypeError, etc.)       │
│ - Identify root cause with high precision                  │
│ - Detect programming language                              │
│ - Return structured analysis as JSON                        │
└───────────────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────────────┐
│ STEP 2: Fix Generation (Up to 3 Attempts)                     │
│                                                               │
│ Attempt 1: Functional Fix Strategy                          │
│   - LLM generates code addressing root cause               │
│   - Validates Python syntax or general correctness         │
│   - If valid → SKIP to Step 4                             │
│   - If invalid → collect error feedback                    │
│                                                               │
│ Attempt 2: Syntax Correction Strategy                      │
│   - Corrects structural Python syntax errors               │
│   - Retains functional logic from Attempt 1                │
│   - If valid → SKIP to Step 4                             │
│   - If invalid → collect error feedback                    │
│                                                               │
│ Attempt 3: Safe Fallback Strategy                          │
│   - Applies defensive programming patterns                 │
│   - Simplifies logic to avoid complex errors               │
│   - If valid → SKIP to Step 4                             │
│   - If invalid → return best-effort fix                    │
└───────────────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────────────┐
│ STEP 3: Validation                                             │
│ - Python code: Compile to AST, check syntax/semantics      │
│ - Other languages: Apply heuristic pattern matching        │
│ - URL errors: Validate protocol, domain structure          │
│ - Return validation status: VALID / INVALID + reason       │
└───────────────────────────────────────────────────────────────┘
        ↓ (if Python and validation passed)
┌───────────────────────────────────────────────────────────────┐
│ STEP 4: Sandbox Execution (Python Only)                       │
│ - Execute fixed code in isolated subprocess                 │
│ - Capture stdout, stderr, return values                     │
│ - Monitor for runtime exceptions                            │
│ - Enforce timeout (prevents infinite loops)                 │
│ - Detect silent failures or incorrect logic                 │
└───────────────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────────────┐
│ STEP 5: Code Optimization                                      │
│ - Remove redundant code and dead branches                   │
│ - Improve variable naming and comments                      │
│ - Apply language-specific idioms                            │
│ - Enhance readability for maintainability                   │
└───────────────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────────────┐
│ STEP 6: Pattern Storage                                        │
│ - Save error-to-fix mapping for future reference            │
│ - Maintain pattern memory (max 100 entries)                 │
│ - Enable faster resolution of similar future bugs           │
└───────────────────────────────────────────────────────────────┘
        ↓
        Return Results to User
```

### **Detailed Step Descriptions**

#### **STEP 0: Pattern Memory Lookup**
- **What**: Checks `patterns.json` for historically resolved similar errors
- **Why**: Dramatically speeds up resolution for recurring bugs
- **How**: Uses sequence matching with 85%+ similarity threshold for error type + cause
- **Output**: If found, displays previous fix alongside new analysis

#### **STEP 1: Error Analysis**
- **What**: Deep analysis of the error message and code
- **Prompt**: Low-temperature (0.1) LLM prompt ensuring deterministic, accurate output
- **Returns**:
  ```json
  {
    "error_type": "ZeroDivisionError",
    "line_hint": "line 15: result = 10 / denominator",
    "cause": "denominator variable is 0 when function called without checking",
    "fix_approach": "Add validation: if denominator == 0: return None or raise ValueError",
    "language": "Python",
    "confidence": "high"
  }
  ```

#### **STEP 2: Fix Generation (Retry Loop)**
Each attempt uses a different strategy based on validation feedback:

**Attempt 1 (Functional Fix)**
- Prompt: "Analyze the error. Generate a functional code fix."
- Focus: Addressing the root cause directly
- Example: For `ZeroDivisionError`, add denominator validation

**Attempt 2 (Syntax Correction)**
- Prompt: "Previous syntax validation failed. Correct the syntax errors."
- Focus: Fixing structural problems (missing colons, parentheses, etc.)
- Example: Fix indentation issues or quote mismatches

**Attempt 3 (Safe Fallback)**
- Prompt: "Simplify logic to bypass error safely. No SyntaxErrors allowed."
- Focus: Defensive, simplified approach
- Example: Wrap in try-except or use safer default values

#### **STEP 3: Validation**
- **For Python**: Compiles code to Abstract Syntax Tree (AST) to detect syntax errors
- **For URLs**: Validates protocol (http/https), domain format, structure
- **For JavaScript/Others**: Regex-based pattern matching for common errors
- **Returns**: `{valid: true/false, reason: "descriptive error message"}`

#### **STEP 4: Sandbox Execution** (Python only)
- **Isolated Subprocess**: Code runs in a separate process to prevent harmful effects
- **Timeout**: Execution limited to 10 seconds (prevents infinite loops)
- **Captures**:
  - Standard output
  - Error messages
  - Return values
  - Exception tracebacks
- **Example Output**:
  ```json
  {
    "success": true,
    "output": "Result: 42",
    "error": null,
    "execution_time": 0.025
  }
  ```

#### **STEP 5: Code Optimization**
- Refactors fixed code for readability and best practices
- Removes redundancy and improves naming
- Applies language-specific idioms
- **Example**: Converts verbose loops to list comprehensions in Python

#### **STEP 6: Pattern Storage**
- Saves to `patterns.json`: `error_type`, `cause`, `fix_explanation`, `updated_code`, `language`, `timestamp`
- Prevents exact duplicates (>85% similarity)
- Maintains FIFO queue (oldest pattern removed if count > 100)

### **Real-World Example**

**User Input:**
```
Error: ZeroDivisionError: division by zero at line 5
Code:
def calculate_average(numbers):
    total = sum(numbers)
    avg = total / len(numbers)
    return avg

result = calculate_average([])
```

**Pipeline Execution:**

1. **Pattern Lookup**: Check if "ZeroDivisionError with empty list" exists → Found! (confidence: medium)
2. **Analysis**: Root cause identified: "Empty list causes len(numbers) = 0"
3. **Fix Attempt 1**: Add input validation
4. **Validation**: ✅ Passes syntax check
5. **Sandbox Execution**: ✅ Runs without error, returns correct value
6. **Optimization**: Simplify to one-liner with default parameter
7. **Storage**: Save pattern for future reference

**Final Output:**
```python
def calculate_average(numbers):
    if not numbers:
        return 0  # or raise ValueError("Empty list provided")
    return sum(numbers) / len(numbers)

result = calculate_average([])  # Returns 0 safely
```

---

## 📡 API Endpoints

### **`POST /debug-stream`** (Streaming Endpoint)
**Purpose**: Core debugging pipeline with real-time SSE streaming

**Request Body**:
```json
{
  "error": "ZeroDivisionError: division by zero",
  "code": "result = 10 / 0"
}
```

**Response**: Server-Sent Events (SSE) stream with multiple event types:

| Event Type | Payload Example | Description |
|-----------|-----------------|-------------|
| `status` | `{"step": "analyzing", "message": "🔍 Analyzing error..."}` | Pipeline step updates |
| `pattern_match` | `{"error_type": "ZeroDivisionError", "fix_explanation": "..."}` | Historical pattern found |
| `analysis` | `{"analysis": {...}, "detected_language": "Python", "problem_type": "python_error"}` | Root cause analysis |
| `retry` | `{"attempt": 1, "reason": "SyntaxError on line 2"}` | Retry feedback |
| `fix` | `{"fix": {...}, "validation": {...}, "steps": [...], "retries_taken": 2}` | Final fix result |
| `sandbox` | `{"success": true, "output": "...", "error": null}` | Execution result |
| `optimization` | `{"optimized_code": "...", "improvements": [...]}` | Optimized code |
| `confidence` | `{"score": 87}` | Overall confidence score (0-100) |
| `error` | `{"error": "API key invalid"}` | Error message |

**Example cURL**:
```bash
curl -X POST http://127.0.0.1:8000/debug-stream \
  -H "Content-Type: application/json" \
  -d '{
    "error": "TypeError: cannot add NoneType to int",
    "code": "x = None\nresult = x + 5"
  }'
```

### **`POST /followup`** (Chat Endpoint)
**Purpose**: Ask questions about the generated fix

**Request Body**:
```json
{
  "question": "Why does this approach work better than try-except?",
  "original_error": "ZeroDivisionError: division by zero",
  "original_code": "avg = total / len(numbers)",
  "fixed_code": "avg = total / len(numbers) if numbers else 0",
  "analysis": {"error_type": "ZeroDivisionError", "cause": "..."},
  "fix_explanation": "Added conditional check for empty list"
}
```

**Response**:
```json
{
  "response": "This approach is better because...",
  "reasoning": "..."
}
```

### **`GET /`** (Frontend)
**Purpose**: Serves the web UI

**Response**: HTML page with integrated Prism.js highlighting and SSE client

---

## ⚙️ Configuration

### **Environment Variables** (`.env`)
```env
# Required
GROQ_API_KEY=gsk_your_api_key_here

# Optional (defaults shown)
# MODEL=llama-3.3-70b-versatile  # LLM model name
# SANDBOX_TIMEOUT=10              # Python execution timeout in seconds
# MAX_RETRIES=3                   # Max fix attempts
# MAX_PATTERNS=100                # Pattern memory cap
```

### **Customization Points**

**1. Change LLM Model**
Edit [utils/llm_client.py](utils/llm_client.py):
```python
MODEL = "llama-3.3-70b-versatile"  # Change to any Groq-supported model
```

**2. Adjust Retry Strategies**
Edit [main.py](main.py) function `debug_stream`:
```python
max_retries = 5  # Increase to 5 attempts
```

**3. Modify Sandbox Timeout**
Edit [agents/sandbox.py](agents/sandbox.py):
```python
timeout_seconds = 20  # Increase from 10
```

**4. Change Pattern Memory Limit**
Edit [utils/pattern_store.py](utils/pattern_store.py):
```python
MAX_PATTERNS = 200  # Increase from 100
```

---

## 📊 Usage Examples

### **Example 1: Fixing a Python Logic Error**
Input:
```
Error: IndexError: list index out of range
Code:
def get_first_item(items):
    return items[0]

print(get_first_item([]))
```

Expected Output:
```python
def get_first_item(items):
    if not items:
        return None
    return items[0]

print(get_first_item([]))  # Output: None
```

### **Example 2: Fixing a URL Error**
Input:
```
Error: Invalid URL
Code: url = "example.com"
```

Expected Output:
```
https://example.com
```

### **Example 3: Fixing a JavaScript Error**
Input:
```
Error: Cannot read property 'length' of undefined
Code: const str = undefined; const len = str.length;
```

Expected Output:
```javascript
const str = undefined;
const len = str ? str.length : 0;
```

---

## 🏗️ Architecture & Components

### **Agent Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Server                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              /debug-stream Endpoint                  │  │
│  │         (Main debugging pipeline orchestrator)       │  │
│  └──────────────────────────────────────────────────────┘  │
│           │                                                │
│           ├─→ Analyzer Agent                              │
│           │   ├─ LLM Call: Error Analysis                │
│           │   └─ Output: JSON with root cause            │
│           │                                              │
│           ├─→ Pattern Store                              │
│           │   ├─ Lookup: Find similar historical fixes   │
│           │   └─ Save: Store successful patterns         │
│           │                                              │
│           ├─→ Fixer Agent (Retry Loop)                  │
│           │   ├─ LLM Call: Generate fix                 │
│           │   ├─ Strategy: Functional → Syntax → Fallback│
│           │   └─ Output: Fixed code                     │
│           │                                              │
│           ├─→ Validator (Deterministic)                 │
│           │   ├─ Python: AST compilation check          │
│           │   ├─ Others: Regex pattern matching         │
│           │   └─ Output: Valid / Invalid + reason       │
│           │                                              │
│           ├─→ Sandbox (Python only)                     │
│           │   ├─ Safe subprocess execution              │
│           │   ├─ Timeout protection                     │
│           │   └─ Output: Success / Failure + output     │
│           │                                              │
│           ├─→ Simplifier Agent                          │
│           │   ├─ LLM Call: Optimize code                │
│           │   └─ Output: Cleaner, readable code         │
│           │                                              │
│           └─→ SSE Stream → Frontend                     │
│               ├─ Real-time step updates                 │
│               ├─ Intermediate results                   │
│               └─ Final output                           │
│                                                         │
└─────────────────────────────────────────────────────────────┘
```

### **Data Flow Diagram**

```
┌──────────────────┐
│  User Input      │
│ (Error + Code)   │
└────────┬─────────┘
         │
         ├─→ Classification: Problem Type, Language Detection
         │
         ├─→ Pattern Lookup: Similar historical fixes?
         │
         ├─→ LLM Analysis (Low Temp 0.1): Root cause
         │                  ↓
         │          ┌───────────────────┐
         │          │ Retry Loop (×3)   │
         │          ├───────────────────┤
         │          │ Attempt 1: Fix    │
         │          │    ↓              │
         │          │ Validate (Pass?)  │
         │          │    ↓ No           │
         │          │ Attempt 2: Syntax │
         │          │    ↓              │
         │          │ Validate (Pass?)  │
         │          │    ↓ No           │
         │          │ Attempt 3: Safe   │
         │          │    ↓              │
         │          │ Validate (Pass)   │
         │          └──────┬────────────┘
         │                 │
         ├─→ Sandbox Execution (Python): Test fix
         │
         ├─→ Code Optimization: Make it clean
         │
         ├─→ Pattern Storage: Learn from fix
         │
         └─→ Stream Results: SSE to Frontend
```

### **Component Responsibilities**

| Component | Responsibility | Input | Output |
|-----------|-----------------|-------|--------|
| **Analyzer** | Parse error, identify root cause | Error + Code | JSON analysis with error_type, cause, fix_approach |
| **Fixer** | Generate fixes with adaptive strategies | Analysis + Feedback | Fixed code (string) |
| **Validator (Python)** | Check syntax via AST compilation | Python code | `{valid: bool, reason: str}` |
| **Validator (Generic)** | Pattern-based validation | Code | `{valid: bool, reason: str}` |
| **Sandbox** | Safe execution in subprocess | Python code | `{success: bool, output: str, error: str, time: float}` |
| **Simplifier** | Optimize and refactor code | Fixed code | Simplified code |
| **Pattern Store** | Learn and retrieve from history | Error data / Query | Save success / Find match |

---

## 🐛 Troubleshooting

### **Issue: "GROQ_API_KEY not found"**
**Solution**: Ensure `.env` file exists in project root with correct API key
```bash
# Create .env if missing
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Verify it was created
cat .env
```

### **Issue: "Connection refused" when accessing http://127.0.0.1:8000**
**Solution**: Ensure Uvicorn server is running
```bash
# Check if process is running
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# If not running, start it:
uvicorn main:app --reload
```

### **Issue: "Module not found: fastapi"**
**Solution**: Install dependencies in activated virtual environment
```bash
# Activate venv first
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Then install
pip install -r requirements.txt

# Verify installation
pip list
```

### **Issue: Sandbox execution timeout on simple code**
**Solution**: Check for infinite loops in generated code or increase timeout
```python
# In agents/sandbox.py
timeout_seconds = 20  # Increase from 10
```

### **Issue: Pattern memory not persisting across sessions**
**Solution**: Check file permissions on `patterns.json`
```bash
# Ensure write permissions
chmod 644 patterns.json  # macOS/Linux

# Or delete and let app recreate
rm patterns.json
```

### **Issue: High API usage / Rate limiting errors**
**Solution**: Implement request batching or increase delay
- Groq has generous free tier limits
- Monitor API usage in Groq Console
- Consider premium tier for production use

---

## 📈 Performance Characteristics

| Metric | Typical Value | Notes |
|--------|---------------|-------|
| **Analysis Time** | 0.5–1.5s | Depends on error complexity & LLM latency |
| **Fix Generation** | 0.5–2s per attempt | Up to 3 attempts possible |
| **Validation Time** | 10–100ms | Python AST compilation is fast |
| **Sandbox Execution** | 10ms–10s | Depends on code complexity; capped at 10s |
| **Optimization Time** | 0.5–1s | LLM refactoring call |
| **Total Pipeline** | 2–10s | Typical end-to-end for most bugs |
| **Pattern Lookup** | <10ms | Near-instant file I/O |
| **Pattern Memory Size** | ~50KB (100 entries) | Negligible disk/memory footprint |

---

## 🔐 Security Considerations

### **Sandbox Safety**
- ✅ Python code executed in **isolated subprocess** (not same process)
- ✅ **Timeout protection** prevents infinite loops (default: 10s)
- ✅ **Read-only file access** by default
- ⚠️ Sandbox does NOT prevent:
  - File I/O (intentional—may be needed for testing)
  - Network requests (intentional—may be needed for testing)
  - System calls through subprocess
  - **Recommendation**: Only use on trusted code / in isolated environment

### **API Security**
- ✅ Groq API key stored in `.env` (not in source code)
- ⚠️ CORS middleware allows all origins (`"*"`) in development
- ⚠️ No authentication on `/debug-stream` endpoint
- **Recommendation**: Add auth middleware for production deployment

### **Input Validation**
- ✅ FastAPI Pydantic models validate request structure
- ⚠️ LLM prompts include user input (indirect injection risk)
- **Mitigation**: Low temperature (0.1) reduces hallucination/injection risk

---

## 🚀 Production Deployment

### **Recommended Setup**
```bash
# 1. Use production ASGI server (Gunicorn + Uvicorn)
pip install gunicorn

# 2. Run with multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 3. Add reverse proxy (Nginx) for:
#    - SSL/TLS termination
#    - Rate limiting
#    - Static file serving

# 4. Monitor with systemd or supervisor
sudo systemctl start autodebug-agent

# 5. Set up logging
export LOG_LEVEL=info
```

### **Environment Variables for Production**
```env
GROQ_API_KEY=gsk_your_production_key_here
ENVIRONMENT=production
LOG_LEVEL=info
SANDBOX_TIMEOUT=5
MAX_RETRIES=3
CORS_ORIGINS=["https://yourdomain.com"]
```

---

## 📝 License & Attribution

This project uses:
- **Groq API** for LLM inference
- **FastAPI** for the web framework
- **Prism.js** for syntax highlighting

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- [ ] Support for more languages (Go, Rust, TypeScript)
- [ ] Enhanced sandbox sandboxing (chroot, Docker)
- [ ] Web UI dark mode improvements
- [ ] Performance optimizations (caching, async patterns)
- [ ] Comprehensive test suite

---

## 📞 Support & Feedback

- **API Issues**: Check Groq Console logs
- **Code Issues**: Enable debug logging (`logging.basicConfig(level=logging.DEBUG)`)
- **Feature Requests**: Create an issue with detailed description
- **Bug Reports**: Include error trace and reproduction steps

### **Contact**
- **Email**: [kandadicharantej21@gmail.com](mailto:kandadicharantej21@gmail.com)
- **LinkedIn**: [linkedin.com/in/kandadicharantej](https://linkedin.com/in/kandadicharantej)

---

**Happy Debugging! 🚀** 
