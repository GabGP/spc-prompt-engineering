# SPC Transformation Engine — Documentation Hub

Welcome to the documentation repository for the **SPC Transformation Engine**, an empirical research system combining **Statistical Process Control (SPC)** and **Prompt Engineering** to optimize LLM transformation latency and eliminate context bloat.

---

## 1. Documentation Index

The following core documents provide complete specifications, operating instructions, and technical references:

| Document | Purpose | Target Audience |
| :--- | :--- | :--- |
| [**Quick Start Guide**](quickstart.md) | Rapid onboarding, prerequisites, environment setup, and executing your first run in under 5 minutes. | All Users & New Operators |
| [**System Architecture**](architecture.md) | Detailed architectural breakdown, theoretical formalization `S = (C, R, I, O, F)`, transfer function, Shewhart I-MR mechanics, subsystem design, and token invariants. | Software Engineers, Data Scientists, & System Architects |
| [**Operator & Reference Manual**](manual.md) | Exhaustive CLI command reference (`run`, `status`, `slice`, `rebuild-cache`), 4-phase experimental protocols, deterministic quality gate rules, offline mock simulation, and troubleshooting. | Daily Operators, Quality Analysts, & Researchers |
| [**Token Accounting & Lifecycle**](token_accounting.md) | Formal token decomposition equations, boundary framing (ε), EOS preemption, thinking tokens lifecycle (live chat vs. persistence), and CSV telemetry mapping. | Statistical Analysts, System Architects, & Researchers |
| [**Google Sheets Webhook Setup**](spreadsheet_webhook_setup.md) | Step-by-step setup guide for configuring real-time telemetry streaming to Google Sheets via Google Apps Script. | DevOps, System Administrators, & Operators |

---

## 2. Recommended Reading Paths by Persona

### Path A: Daily Operator / Experimenter
If you are responsible for running daily experimental units, slicing textbook PDFs, and maintaining the run log:
1. Follow the [Quick Start Guide](quickstart.md) to set up your `.env` and verify installation.
2. Read the **Command Reference** in the [Operator Manual](manual.md#2-cli-command-reference) for `spc slice`, `spc status`, and `spc run`.
3. Consult the **Experimental Protocols** in the [Operator Manual](manual.md#3-experimental-protocol-guidelines) to ensure proper factor settings (`X₁, X₂`) for the current phase.
4. Keep the **Troubleshooting FAQ** in the [Operator Manual](manual.md#6-troubleshooting--operational-faqs) handy.

### Path B: Statistical Quality Analyst / Researcher
If you are analyzing process capability (`Cp, Cpk`), plotting control charts (I-MR), or fitting the response transfer function:
1. Review the **Theoretical Framework** in the [System Architecture](architecture.md#1-theoretical-framework--mathematical-formulation) for Shewhart constants (`d₂ = 1.128, D₄ = 3.267`) and limit formulas.
2. Review the **Token Invariants & Decomposition** in the [System Architecture](architecture.md#4-token-accounting--input-wip-formalization) and [Token Accounting Specification](token_accounting.md) to understand input token components (`context + instruction + page + framing + rework = prompt`).
3. Inspect the **Ledger Schema** in the [Operator Manual](manual.md#5-ledger--telemetry-specification) for all 22 tracked variables in `data/main_event_log.csv`.
4. Optionally configure live cloud streaming via the [Google Sheets Webhook Setup](spreadsheet_webhook_setup.md).

### Path C: Software Engineer / Maintainer
If you are modifying codebase functionality or integrating new LLM providers:
1. Examine the **Subsystem Decomposition** and Mermaid pipeline in the [System Architecture](architecture.md#2-end-to-end-system-architecture).
2. Review the **Deterministic Quality Gate** logic in the [System Architecture](architecture.md#6-deterministic-inspection-gate--quality-control).

---

## 3. High-Level System Overview

### Core Transfer Function
The engine models and evaluates the linear response transfer function:

```text
Y = α₀ + α₁·X₁ + α₂·X₂ + ε
```

* **Response Variable (Y):** Continuous transformation cycle time `T` in seconds.
* **Controllable Factor 1 (X₁ — Context Buffer):** `0` = Accumulating session buffer (Phase I); `1` = Zero-WIP session reset (Phases II–IV).
* **Controllable Factor 2 (X₂ — External Memory / Schema):** `0` = Bare ad-hoc prompt; `1` = Standard Operating Procedure (SOP) schema injection (`memory_context.md`).

### Experimental Timeline
```text
[Phase I: Baseline]          [Phase II: Reset Isolation]  [Phase III: SOP Schema]      [Phase IV: Capability]
Sept 2 – Sept 23             Sept 24 – Oct 7              Oct 8 – Oct 21               Oct 22 – Nov 2
X1 = 0, X2 = 0               X1 = 1, X2 = 0               X1 = 1, X2 = 1               X1 = 1, X2 = 1
Target: m = 22 runs          Target: m = 14 runs          Target: m = 14 runs          Freeze Limits, OLS Fit
```

### Deterministic Quality Inspection
Outputs must strictly satisfy 3 binary rules before acceptance:
1. **Structural Completeness:** Level-2 headers (`## Core Synthesis`, `## Technical Taxonomy`, `## Analytical Formulations`).
2. **Syntactical Validity:** Balanced LaTeX block tags (`$$`).
3. **Empty Formula Handling:** Must contain `"NONE RECORDED"` if the input page contains no mathematical equations.

Non-conforming outputs trigger an automated dynamic reflection rework loop (`P = P + 1`).

---

## 4. Quick Command Cheat Sheet

```bash
# Display operational status, active phase, and cache turn count
spc status

# Execute the next scheduled run
spc run

# Execute a run with a specific phase override
spc run --phase Phase_II

# Execute an offline mock run testing the rework reflection cycle
spc run --mock rework

# Slice pages 1 to 30 from a source textbook PDF
spc slice --book data/raw/textbook.pdf --start 1 --end 30

# Rebuild session cache from forensic audit logs if cache was deleted
spc rebuild-cache --phase Phase_I
```

---

## 5. Repository & File Hygiene Rules

To maintain experimental validity and protect data privacy:
* **Tracked in Version Control:**
  - Production code (`src/`)
  - Test suites (`tests/`)
  - Documentation (`docs/`, `README.md`)
  - Configuration & environment templates (`pyproject.toml`, `.env.example`)
* **Never Tracked in Version Control (Ignored via `.gitignore`):**
  - Entire runtime data directory (`data/`):
    - Raw textbook source PDFs (`data/raw/`)
    - Sliced target page PDFs (`data/inputs/`)
    - Generated markdown output documents (`data/outputs/`)
    - Detailed forensic audit JSON files (`data/logs/`)
    - Primary telemetry ledger (`data/main_event_log.csv`)
  - Local session caches (`.cache/*`)
  - Environment secrets (`.env`)
