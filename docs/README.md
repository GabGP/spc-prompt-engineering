# SPC Transformation Engine — Documentation Hub

Welcome to the documentation repository for the **SPC Transformation Engine**, an empirical research system combining **Statistical Process Control (SPC)** and **Prompt Engineering** to optimize LLM transformation latency and eliminate context bloat.

---

## 1. Documentation Index

The following core documents provide complete specifications, operating instructions, and technical references:

| Document | Purpose | Target Audience |
| :--- | :--- | :--- |
| [**Quick Start Guide**](quickstart.md) | Rapid onboarding, prerequisites, environment setup, and executing your first run in under 5 minutes. | All Users & New Operators |
| [**System Architecture**](architecture.md) | Detailed architectural breakdown, theoretical formalization ($S = (C,R,I,O,F)$), transfer function, Shewhart I-MR mechanics, subsystem design, and token accounting invariants. | Software Engineers, Data Scientists, & System Architects |
| [**Operator & Reference Manual**](manual.md) | Exhaustive CLI command reference (`run`, `status`, `slice`, `rebuild-cache`), 4-phase experimental protocols, deterministic quality gate rules, offline mock simulation, and troubleshooting. | Daily Operators, Quality Analysts, & Researchers |
| [**Google Sheets Webhook Setup**](spreadsheet_webhook_setup.md) | Step-by-step setup guide for configuring real-time telemetry streaming to Google Sheets via Google Apps Script. | DevOps, System Administrators, & Operators |

---

## 2. Recommended Reading Paths by Persona

### Path A: Daily Operator / Experimenter
If you are responsible for running daily experimental units, slicing textbook PDFs, and maintaining the run log:
1. Follow the [Quick Start Guide](quickstart.md) to set up your `.env` and verify installation.
2. Read the **Command Reference** in the [Operator Manual](manual.md#2-cli-command-reference) for `spc slice`, `spc status`, and `spc run`.
3. Consult the **Experimental Protocols** in the [Operator Manual](manual.md#3-experimental-protocol-guidelines) to ensure proper factor settings ($X_1, X_2$) for the current phase.
4. Keep the **Troubleshooting FAQ** in the [Operator Manual](manual.md#6-troubleshooting--operational-faqs) handy.

### Path B: Statistical Quality Analyst / Researcher
If you are analyzing process capability ($C_p, C_{pk}$), plotting control charts (I-MR), or fitting the response transfer function:
1. Review the **Theoretical Framework** in the [System Architecture](architecture.md#1-theoretical-framework--mathematical-formulation) for Shewhart constants ($d_2 = 1.128, D_4 = 3.267$) and limit formulas.
2. Review the **Token Invariants & Decomposition** in the [System Architecture](architecture.md#4-token-accounting--input-wip-formalization) to understand input token components ($context + instruction + page + framing = prompt$).
3. Inspect the **Ledger Schema** in the [Operator Manual](manual.md#5-ledger--telemetry-specification) for all 20 tracked variables in `data/main_event_log.csv`.
4. Optionally configure live cloud streaming via the [Google Sheets Webhook Setup](spreadsheet_webhook_setup.md).

### Path C: Software Engineer / Maintainer
If you are modifying codebase functionality, adding inspection rules, or integrating new LLM providers:
1. Examine the **Subsystem Decomposition** and Mermaid pipeline in the [System Architecture](architecture.md#2-end-to-end-system-architecture).
2. Review the **Deterministic Quality Gate** logic in the [System Architecture](architecture.md#6-deterministic-inspection-gate--quality-control).
3. Review engineering constraints in [`GEMINI.md`](../GEMINI.md) (e.g. strict 150-LOC production code ceiling, mirrored test suites with > 80% coverage).
4. Run `pytest` to verify the test suite.

---

## 3. High-Level System Overview

### Core Transfer Function
The engine models and evaluates the linear response transfer function:

$$Y = \alpha_0 + \alpha_1 X_1 + \alpha_2 X_2 + \epsilon$$

* **Response Variable ($Y$):** Continuous transformation cycle time $T$ in seconds.
* **Controllable Factor 1 ($X_1$ — Context Buffer):** `0` = Accumulating session buffer (Phase I); `1` = Zero-WIP session reset (Phases II–IV).
* **Controllable Factor 2 ($X_2$ — External Memory / Schema):** `0` = Bare ad-hoc prompt; `1` = Standard Operating Procedure (SOP) schema injection (`memory_context.md`).

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

Non-conforming outputs trigger an automated dynamic reflection rework loop ($P = P + 1$).

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
  - Documentation (`docs/`, `README.md`, `GEMINI.md`)
  - Telemetry ledger (`data/main_event_log.csv`)
* **Never Tracked in Version Control:**
  - Raw textbook source PDFs (`data/raw/*.pdf`)
  - Sliced target page PDFs (`data/inputs/*.pdf`)
  - Generated markdown output documents (`data/outputs/*.md`)
  - Detailed forensic audit JSON files (`data/logs/*.json`)
  - Local session caches (`.cache/*`)
  - Internal planning scratch files (`experimental_process_plan.md`, `implementation_plan.md`)
