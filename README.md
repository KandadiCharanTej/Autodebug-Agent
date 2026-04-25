# Agentic Code Debugger

Agentic Code Debugger is an AI-powered autonomous code debugging tool that analyzes, fixes, validates, and executes code in real-time. Unlike simple "one-shot" generation tools, this agent applies reasoning to continuously loop and self-correct errors across multiple attempts.

## Core Features

- **Multi-Language Support**: Automatically detects and handles errors in Python, JavaScript, Java, C++, Python, PHP, Rust, Go, SQL, and even URLs.
- **Self-Correcting Iteration loop**: Follows a fix → validate → retry sequence (up to 3 retries per bug) dynamically learning from validation outcomes.
- **Pattern Memory**: Remembers past fixes and compares incoming bugs to past bugs, learning optimizations dynamically.
- **Python Code Execution Sandbox**: Safely executes Python code in a simulated sandbox to verify fixes function correctly.
- **Code Optimization Layer**: Not satisfied with just "making it work," the agent further simplifies generated code for clean readability.
- **Real-Time Streaming**: Stream SSE (Server-Sent Events) dynamically push step-by-step reasoning steps to the beautiful web UI.
- **Follow-Up Conversational Experience**: Engage with the AI via a built-in chat interface to ask questions about the applied code fix. 

## Project Structure

```
autodebug-agent/
├── agents/                   # Core autonomous agents logic
│   ├── analyzer.py               # Identifies error root cause
│   ├── fixer.py                  # Generates code fix strategies
│   ├── python_validator.py       # Syntax validation for Python
│   ├── sandbox.py                # Simulated code execution
│   ├── simplifier.py             # Optimizes fixed code
│   └── validator.py              # Generic validation
├── utils/                    # Utility scripts
│   ├── json_parser.py            # Extracts JSON intelligently
│   ├── llm_client.py             # Configures Groq/OpenAI client instance
│   └── pattern_store.py          # Saves matching logic for Pattern Memory
├── static/                   # Frontend assets
│   ├── index.html                # Main UI HTML
│   ├── style.css                 # Vanilla CSS
│   └── script.js                 # Frontend interactions / SSE parsing
├── .env                      # API keys and environment variables (ignored in Git)
├── main.py                   # FastAPI backend / API routing
└── requirements.txt          # Python dependencies
```

## Technologies Used

- **Backend**: Python 3.x, FastAPI
- **Frontend**: Vanilla JS, HTML, CSS with Prism.js for code highlights
- **AI Backend**: Groq AI API utilizing `llama-3.3-70b-versatile` via the standard `openai` pip client.

## Getting Started

### Prerequisites
- Python 3.9+
- A valid [Groq API Key](https://console.groq.com/keys)

### Setup Instructions

1. **Clone or switch to the directory**
   Navigate to the project root directory where the codebase resides.

2. **Create and Activate a Virtual Environment** (Recommended)
   ```bash
   python -m venv .venv
   
   # For Windows:
   .venv\Scripts\activate
   # For macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   Install all the necessary packages via `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Configuration**
   Ensure an `.env` file exists in the root directory. If it doesn't, create it:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```

### Running the Application

To fire up the Backend and Frontend simultaneously, launch the FastAPI server using Uvicorn:
```bash
uvicorn main:app --reload
```

The output will indicate that Uvicorn is running. Open your preferred browser and navigate to:
**http://127.0.0.1:8000** 

## How It Works

1. Enter an error track/stack trace & related code in the Inputs on the web frontend. 
2. Press "Run Debug Agent". 
3. Watch the pipeline live in the results panel:
   * **Pattern Lookup** (It will check history data.)
   * **Analyze** (Determines the error root cause with high detail.)
   * **Fix & Validate Loop** (Runs iterations to guarantee the new code actually avoids the stated error).
   * **Execute Sandbox** (Test-runs the fix to confirm functionality).
   * **Optimize** (Makes code simpler/cleaner).
4. After resolution, you may review the newly generated code snippet, view agentic reasoning, or chat about the fix in the Follow-up interface. 
