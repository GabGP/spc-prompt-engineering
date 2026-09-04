# SPC Transformation Engine — Quick Start Guide

Welcome to the **SPC Transformation Engine**, an empirical research platform combining **Statistical Process Control (SPC)** and **Prompt Engineering** to optimize Large Language Model (LLM) transformation latency and eliminate context bloat.

This guide will get you set up and executing your first transformation run in **under 5 minutes**.

---

## 1. Prerequisites

Before installing the application, ensure your environment meets the following requirements:
* **Python:** Version `3.11` (Python 3.12+ may encounter dependency compatibility issues with certain analysis libraries).
* **Gemini API Key:** A valid Google AI Studio Gemini API key ([Get an API key here](https://aistudio.google.com/)).
* **Operating System:** Windows 10/11 (PowerShell), macOS, or Linux.
* **Git:** Installed and available on your system path.

---

## 2. Installation & Setup

### Step 1: Clone Repository & Create Environment

#### Option A: Using Conda / Miniconda (Recommended)
```bash
# Clone the repository
git clone https://github.com/GabGP/spc-prompt-engineering.git
cd spc-prompt-engineering

# Create a dedicated Python 3.11 environment
conda create -n spc-env python=3.11 -y

# Activate the environment
conda activate spc-env
```

#### Option B: Using Standard Python `venv` (PowerShell on Windows)
```powershell
# Clone the repository
git clone https://github.com/GabGP/spc-prompt-engineering.git
cd spc-prompt-engineering

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1
```

#### Option C: Using Standard Python `venv` (Linux / macOS)
```bash
# Clone the repository
git clone https://github.com/GabGP/spc-prompt-engineering.git
cd spc-prompt-engineering

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 2: Install Dependencies in Editable Mode

Install the package along with development and analysis dependencies:
```bash
pip install -e ".[dev]"
```

Verify that the CLI binary is registered:
```bash
spc --help
```

---

### Step 3: Configure Environment Variables

1. Copy the example configuration file to create `.env`:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```

2. Open `.env` and set your credentials:
   ```env
   # Mandatory: Google Gemini API Key
   GEMINI_API_KEY=AIzaSy...your_real_key_here

   # Recommended Default Model
   GEMINI_MODEL=gemini-3.8-flash

   # Operator Identifier (Used for audit tracking and CSV logs)
   OPERATOR_NAME=analyst_1

   # Optional: Real-time Cloud Telemetry (Google Sheets Webhook)
   # SHEET_WEBHOOK_URL=https://script.google.com/macros/s/.../exec
   ```

---

## 3. Verify Your Installation

Run the automated test suite to confirm everything is configured properly:
```bash
pytest
```
Expected output:
```text
============================= 115 passed in 2.80s =============================
Required test coverage of 80% reached. Total coverage: 100.00%
```

---

## 4. The 3-Step Operational Workflow

### Step 1: Prepare Input Material (`spc slice`)
The SPC transformation process uses standardized textbook PDF pages as input units to ensure uniform token sizes ($\pm 10\%$).

1. Place your source textbook PDF in `data/raw/` (e.g. `data/raw/textbook.pdf`).
2. Slice the desired page range (e.g., pages 1 through 30):
   ```bash
   spc slice --book data/raw/textbook.pdf --start 1 --end 30
   ```
   Or, if using sequential naming from `page_001.pdf`:
   ```bash
   spc slice --book data/raw/textbook.pdf --start 45 --end 75 --sequential
   ```
   The sliced PDFs are automatically placed into `data/inputs/` (e.g. `data/inputs/page_001.pdf`, `data/inputs/page_002.pdf`, etc.).

---

### Step 2: Check System & Phase Status (`spc status`)
Before triggering a transformation run, verify the active experimental phase, factor settings, and sequential run counter:
```bash
spc status
```

The system displays a Rich terminal dashboard:
* **Active Calendar Phase:** Resolved automatically based on the current local calendar date (or manually overridden).
* **Factor X1 (Context Buffer):** `0 (Accumulating Buffer)` in Phase I, or `1 (Daily Reset)` in Phases II–IV.
* **Factor X2 (Prompt Schema):** `0 (Bare Prompt)` in Phases I–II, or `1 (SOP Schema)` in Phases III–IV.
* **Next Target Run ID:** Sequential identifier for the next row in `data/main_event_log.csv`.
* **Active Cache Turns:** Count of historical conversation turns currently in WIP memory.

---

### Step 3: Execute a Transformation Run (`spc run`)
Run the next scheduled transformation unit:
```bash
spc run
```

What happens under the hood during `spc run`:
1. **Input Resolution:** Automatically selects the next uncompleted page from `data/inputs/`.
2. **Phase & Factor Binding:** Determines $X_1$ (Session state) and $X_2$ (Schema injection).
3. **LLM Transformation:** Sends the prompt payload to Gemini and starts a high-precision wall-clock timer.
4. **Deterministic Inspection Gate:** Evaluates the output against 3 strict rules:
   - Mandatory level-2 headers (`## Core Synthesis`, `## Technical Taxonomy`, `## Analytical Formulations`).
   - LaTeX syntax closure (all `$$` formula delimiters must be paired).
   - Empty formula handling (must state `NONE RECORDED` if no formulas are in the input).
5. **Dynamic Reflection Rework:** If defects are detected, an automated corrective reflection prompt is sent back to the model ($P = P + 1$).
6. **Telemetry & Ledger Persistence:**
   - Appends run telemetry to `data/main_event_log.csv`.
   - Saves complete JSON audit log to `data/logs/run_XXX_audit.json`.
   - Saves accepted markdown artifact to `data/outputs/run_XXX.md`.
   - Dispatches telemetry to Google Sheets if `SHEET_WEBHOOK_URL` is configured.

---

## 5. Offline Simulation Mode (No API Key Required)

If you need to test the pipeline without an active internet connection or API quota, use the built-in `--mock` flag:

```bash
# Simulate an immediate first-pass conforming run
spc run --mock pass

# Simulate a run with 1 rework rejection before passing
spc run --mock rework

# Simulate a syntax defect run (unclosed LaTeX $$ delimiters)
spc run --mock latex

# Simulate a missing formula rule defect
spc run --mock empty_math
```

---

## 6. Inspecting Results & Artifacts

After a run finishes, your artifacts are structured as follows:

| Path | Description | Tracked in Git |
| :--- | :--- | :---: |
| `data/` | Entire runtime directory (inputs, outputs, logs, `main_event_log.csv`) | No (Ignored via `.gitignore`) |
| `data/main_event_log.csv` | Primary 21-column telemetry ledger | No (Ignored via `.gitignore`) |
| `data/outputs/run_XXX.md` | Accepted structured Markdown artifact | No (Ignored via `.gitignore`) |
| `data/logs/run_XXX_audit.json` | Forensic audit trail (prompts, timing, rework history) | No (Ignored via `.gitignore`) |
| `.cache/session_cache.json` | Active multi-turn conversation context buffer | No (Ignored via `.gitignore`) |

---

## 7. Next Steps

* Read the [Operator & Reference Manual](manual.md) for full CLI parameter references, experimental protocols, and troubleshooting.
* Explore the [Architecture Specification](architecture.md) for mathematical definitions ($S = (C,R,I,O,F)$, token decomposition, I-MR equations).
* Set up real-time Google Sheets streaming with the [Google Sheets Webhook Setup Guide](spreadsheet_webhook_setup.md).
