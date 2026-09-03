# SPC Project: LLM Latency & Context Bloat Optimization Engine

An empirical research engine combining **Statistical Process Control (SPC)** and **Prompt Engineering** to optimize Large Language Model (LLM) transformation latency and eliminate context bloat.

---

## 1. Project Overview

This project models human-LLM interaction as a digital service transformation system:

$$S = (C, R, I, O, F)$$

We evaluate the governing response transfer function:

$$Y = \alpha_0 + \alpha_1 X_1 + \alpha_2 X_2$$

* **Primary Response ($Y$):** Transformation Cycle Time ($T$ in seconds), analyzed using Shewhart Individuals–Moving Range (I-MR) control charts.
* **Controllable Factor 1 ($X_1$ — Context Buffer Management):**
  * `0`: Unbounded accumulation (persistent session, tokens grow across iterations).
  * `1`: Zero-WIP policy (context flushed before each run).
* **Controllable Factor 2 ($X_2$ — Prompt Engineering & SOP Schema Scaffolding):**
  * `0`: Bare / ad-hoc prompt without schema constraints.
  * `1`: Standard Operating Procedure (SOP) schema injection (`memory_context.md`).
* **Deterministic Quality Gate (Go / No-Go):**
  Outputs are inspected for mandatory structural headers, closed LaTeX `$$` blocks, and a strict `"NONE RECORDED"` empty-formula handling rule. Non-conforming outputs trigger an automated dynamic reflection rework loop ($P = P + 1$).

### Experimental Phases
1. **Phase I (Baseline Observation):** Sept 2 – Sept 23 ($X_1=0, X_2=0$, unbounded context buffer).
2. **Phase II (Context Reset Isolation):** Sept 24 – Oct 7 ($X_1=1, X_2=0$, daily session reset).
3. **Phase III (SOP Schema Injection):** Oct 8 – Oct 21 ($X_1=1, X_2=1$, clean reset + prompt schema).
4. **Phase IV (Process Capability & Packaging):** Oct 22 – Nov 2 ($C_p, C_{pk}, P_p, P_{pk}$ & OLS model fit).

---

## 2. Environment Setup & Installation

### Option A: Using Conda / Miniconda (Recommended for Windows 11 & Linux)

1. **Create and activate a dedicated conda environment:**
   ```bash
   # Create a clean Python 3.11 environment
   conda create -n spc-env python=3.11 -y

   # Activate the environment
   conda activate spc-env
   ```

2. **Clone the repository and navigate to the project root:**
   ```bash
   cd spc-prompt-engineering
   ```

3. **Install the package in editable mode with development & analysis tools:**
   ```bash
   pip install -e ".[dev]"
   ```

---

### Option B: Using Standard Python `venv`

#### Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install package and dependencies
pip install -e ".[dev]"
```

#### Linux / macOS (Bash / Zsh):
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install package and dependencies
pip install -e ".[dev]"
```

---

## 3. Configuration

1. **Create your environment file:**
   Create a new file named `.env` in the project root by duplicating `.env.example`.

2. **Configure your settings inside `.env`:**
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key
   GEMINI_MODEL=gemini-3.8-flash
   OPERATOR_NAME=your_name_or_identifier
   SHEET_WEBHOOK_URL=  # Optional: Google Apps Script Webhook URL
   ```

---

## 4. Running Tests & Quality Verification

This project enforces strict **Test-Driven Development (TDD)** and **> 80% code coverage**:

```bash
# Run pytest with live line-by-line coverage reporting
pytest
```

---

## 5. CLI Usage & Commands

Once installed, the `spc` command is available directly in your terminal:

```bash
# Check active phase, operator, and next scheduled run
spc status

# Execute the next scheduled run according to the active phase protocol
spc run

# Slice a digital textbook into standardized input pages
spc slice --book path/to/textbook.pdf --start 45 --end 105
```

---

## 6. Documentation Hub

Comprehensive documentation and operator manuals are available in the [`docs/`](docs/README.md) directory:

* [**Documentation Hub (`docs/README.md`)**](docs/README.md): Index, persona-based reading paths, and cheat sheet.
* [**Quick Start Guide (`docs/quickstart.md`)**](docs/quickstart.md): 5-minute setup, configuration, and first execution.
* [**System Architecture (`docs/architecture.md`)**](docs/architecture.md): Formalization $S = (C,R,I,O,F)$, token invariants, Shewhart I-MR mechanics, and subsystem design.
* [**Operator & Reference Manual (`docs/manual.md`)**](docs/manual.md): Complete CLI reference, 4-phase protocols, quality gates, and troubleshooting.
* [**Google Sheets Webhook Setup (`docs/spreadsheet_webhook_setup.md`)**](docs/spreadsheet_webhook_setup.md): Real-time cloud streaming guide.

---

## 7. Git Hygiene & Data Privacy

* **Raw Textbooks & PDFs:** All raw and sliced files in `data/raw/`, `data/inputs/`, and `data/outputs/` are ignored by `.gitignore`.
* **Telemetry Ledger:** Only code, documentation, tests, and `data/main_event_log.csv` are tracked in Git.

---

## 8. Project Architecture

```text
spc-prompt-engineering/
├── src/                      # Direct source tree (no redundant nested folders)
│   ├── config.py             # Application settings & environment variables
│   ├── core/                 # SPC constants, calendar windows, & data models
│   ├── prompts/              # Prompt engineering templates & reflection loader
│   ├── validation/           # Deterministic Go / No-Go inspection gates
│   ├── state/                # Calendar date phase resolution & session tracking
│   ├── engine/               # Gemini API client & latency measurement loop
│   ├── persistence/          # CSV logger & Google Sheets webhook
│   ├── ingestion/            # PDF page slicer & text density validator
│   └── ui/                   # Rich terminal dashboard & CLI commands
├── tests/                    # Mirrored pytest suite (>80% coverage enforced)
├── docs/                     # Comprehensive documentation, manuals, & architecture
├── data/                     # Ignored raw inputs/outputs & tracked main_event_log.csv
├── pyproject.toml            # Packaging configuration & pytest options
└── README.md                 # Project root documentation
```
