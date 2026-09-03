# SPC Transformation Engine — Operator & Reference Manual

This manual provides a complete operational guide and technical command reference for conducting experiments with the **Statistical Process Control (SPC) & Prompt Engineering Research Engine**.

---

## 1. System Configuration & Environment

The engine reads runtime configuration from environment variables or a local `.env` file at the root of the project.

### Configuration Parameters

| Variable | Type | Default | Mandatory? | Description |
| :--- | :---: | :---: | :---: | :--- |
| `GEMINI_API_KEY` | String | `""` | **Yes** | Google Gemini API key used for live API inference and token counting. |
| `GEMINI_MODEL` | String | `gemini-3.8-flash` | No | Server-side Gemini model checkpoint (e.g., `gemini-3.8-flash`, `gemini-2.5-flash`). |
| `OPERATOR_NAME` | String | `operator` | No | Identifier of the operator conducting the run (logged in CSV and JSON audits). |
| `SHEET_WEBHOOK_URL` | String | `None` | No | Full HTTP POST endpoint for real-time Google Sheets streaming. |

### Directory Structure & Defaults

The engine organizes runtime data into dedicated directories:
* `data/raw/`: Place unprocessed textbook source PDFs here.
* `data/inputs/`: Holds sliced 1-indexed target page PDFs (`page_001.pdf`, `page_002.pdf`, ...).
* `data/outputs/`: Holds accepted transformation Markdown files (`run_001.md`, ...).
* `data/logs/`: Holds full forensic JSON audit payloads (`run_001_audit.json`, ...).
* `data/main_event_log.csv`: Primary 20-column CSV ledger tracking all runs.
* `.cache/`: Local cache directory storing active multi-turn conversation sessions.

---

## 2. CLI Command Reference

The engine provides a unified CLI via the `spc` command.

```text
usage: spc [-h] {run,status,slice,rebuild-cache} ...
```

---

### 2.1 `spc status`

Displays the current operational status, active experimental phase, factor settings, run ledger statistics, and cache state.

```bash
spc status
```

#### Output Metrics Displayed
* **Active Calendar Phase:** Resolved automatically based on system date.
* **Factor X1 (Context Buffer):** `0 (Accumulating Buffer)` or `1 (Daily Reset)`.
* **Factor X2 (Prompt Schema):** `0 (Bare / Ad-Hoc Prompt)` or `1 (SOP Schema Injection)`.
* **Total Runs Completed:** Count of executed runs in `data/main_event_log.csv`.
* **Next Target Run ID:** Sequential identifier for the next execution.
* **Active Cache Turns:** Current conversation turns and estimated token load in memory.
* **Last Logged Run Summary:** Brief summary of the most recent run (ID, phase, cycle time $T$, conformance, rework count).

---

### 2.2 `spc run`

Executes a single transformation run, including input resolution, LLM dispatch, wall-clock timing, deterministic quality inspection, potential rework loops, and telemetry persistence.

```bash
spc run [OPTIONS]
```

#### Command Options & Flags

##### Input & Backlog Group
* `-p PATH, --page PATH`  
  Explicit path to input document page PDF or text file.  
  *Default:* Auto-resolves `page_{run_id:03d}.pdf` from `data/inputs/`.
* `-r ID, --run-id ID`  
  Explicit sequential run ID override (integer).  
  *Default:* Increments highest existing `run_id` in `data/main_event_log.csv` by 1.

##### Experimental Factors Group
* `--phase NAME`  
  Overrides calendar-based phase resolution.  
  *Accepted values:* `Phase_I`, `Phase_II`, `Phase_III`, `Phase_IV`.
* `--math`  
  Forces equation presence mode. Quality gate expects mathematical formulas in the output.
* `--no-math`  
  Forces equation absence mode. Quality gate strictly enforces the `"NONE RECORDED"` marker under `## Analytical Formulations`.  
  *Default (neither specified):* Auto-detects formula presence from source page text using regex.

##### Quality Gate & Process Control Group
* `--reworks N`  
  Maximum number of automated reflection rework attempts before concluding run.  
  *Default:* `3`.
* `--cause TEXT`  
  Special cause annotation for assignable variation (e.g. `NETWORK_LATENCY`, `OPERATOR_PAUSE`).  
  *Default:* `NONE`. (Note: If the API returns a non-`STOP` finish reason, this is automatically set to `API_{finish_reason}`).

##### Offline Simulation Group
* `--mock [SCENARIO]`  
  Runs the pipeline offline without requiring an API key or consuming quota.  
  *Choices:*
  * `rework`: Fails first inspection attempt with unclosed LaTeX delimiters, then generates a compliant artifact on rework iteration 1 (*default*).
  * `pass`: Emits a conforming artifact on the initial pass without reworks.
  * `fail`: Emits non-conforming responses continuously until rework limit is reached.
  * `latex`: Emits unclosed LaTeX `$$` delimiters to test syntactical rejection.
  * `empty_math`: Omits math formulas without including the required `"NONE RECORDED"` marker.

#### Examples

```bash
# Standard scheduled run (auto-detects phase and next page)
spc run

# Run with explicit page and phase override
spc run --page data/inputs/page_012.pdf --phase Phase_II

# Run an offline simulation testing the rework loop
spc run --mock rework

# Run logging an external assignable cause
spc run --cause "WIFI_PACKET_LOSS"
```

---

### 2.3 `spc slice`

Slices a raw textbook PDF into individual single-page PDF files placed in `data/inputs/`.

```bash
spc slice -s START -e END [OPTIONS]
```

#### Command Options & Flags
* `-b PATH, --book PATH`  
  Path to source textbook PDF.  
  *Default:* Auto-discovers single PDF file residing in `data/raw/` or `data/`.
* `-s PAGE, --start PAGE` (**Required**)  
  Starting 1-indexed page number in the source PDF.
* `-e PAGE, --end PAGE` (**Required**)  
  Ending 1-indexed page number in the source PDF (inclusive).
* `-o DIR, --output-dir DIR`  
  Destination directory for sliced pages.  
  *Default:* `data/inputs`.
* `--sequential`  
  Names output files sequentially starting from `page_001.pdf` regardless of source page number.
* `--start-index N`  
  Custom starting index for output filenames (e.g., `--start-index 10` produces `page_010.pdf`, `page_011.pdf`, etc.).

#### Examples

```bash
# Slice pages 45 to 105 named page_045.pdf through page_105.pdf
spc slice --book data/raw/textbook.pdf --start 45 --end 105

# Slice pages 50 to 80 renamed sequentially starting from page_001.pdf
spc slice --book data/raw/textbook.pdf --start 50 --end 80 --sequential
```

---

### 2.4 `spc rebuild-cache`

Reconstructs the active multi-turn session cache (`.cache/session_cache.json`) by scanning forensic JSON audit files in `data/logs/`.

```bash
spc rebuild-cache [OPTIONS]
```

#### Command Options & Flags
* `--phase NAME`  
  Experimental phase to reconstruct.  
  *Default:* `Phase_I`.
* `--logs-dir DIR`  
  Directory containing forensic audit logs.  
  *Default:* `data/logs`.

#### Example
```bash
# Reconstruct Phase I session cache after accidental file deletion
spc rebuild-cache --phase Phase_I
```

---

## 3. Experimental Protocol Guidelines

The research experiment runs across four calendar phases. Operators must adhere to the following daily operational standards:

```text
[Phase I: Baseline]          [Phase II: Reset Isolation]  [Phase III: SOP Schema]      [Phase IV: Process Capability]
Sept 2 – Sept 23             Sept 24 – Oct 7              Oct 8 – Oct 21               Oct 22 – Nov 2
X1 = 0, X2 = 0               X1 = 1, X2 = 0               X1 = 1, X2 = 1               X1 = 1, X2 = 1
Accumulating WIP Session     Zero-WIP Daily Reset         Zero-WIP + SOP Memory        Freeze Limits & OLS Fit
Target: m = 22 runs          Target: m = 14 runs          Target: m = 14 runs          Model Fit: Y = a0 + a1X1 + a2X2
```

### Phase I: Baseline Observation ($X_1 = 0, X_2 = 0$)
* **Calendar Window:** September 2 – September 23, 2026.
* **Factor Settings:** Context Buffer accumulating ($X_1 = 0$), Bare prompt template ($X_2 = 0$).
* **Execution Rule:** Execute exactly 1 run per scheduled unit.
* **Context State:** **DO NOT** delete `.cache/session_cache.json`. The session buffer must grow naturally with each run to measure context bloat latency.
* **Target Sample Size:** $m = 22$ runs to compute baseline Shewhart control limits ($UCL_I, LCL_I, UCL_{MR}$).

### Phase II: Context Reset Isolation ($X_1 = 1, X_2 = 0$)
* **Calendar Window:** September 24 – October 7, 2026.
* **Factor Settings:** Zero-WIP daily session reset ($X_1 = 1$), Bare prompt template ($X_2 = 0$).
* **Execution Rule:** Run context is flushed before every run.
* **Context State:** `context_tokens` is strictly 0.

### Phase III: SOP Schema Injection ($X_1 = 1, X_2 = 1$)
* **Calendar Window:** October 8 – October 21, 2026.
* **Factor Settings:** Zero-WIP reset ($X_1 = 1$), SOP Schema injection ($X_2 = 1$).
* **Execution Rule:** Prepend `memory_context.md` to establish standard terminology, formatting constraints, and error boundaries.
* **Objective:** Evaluate interaction effect on cycle time variance and rework reduction.

### Phase IV: Process Capability & Regression Analysis ($X_1 = 1, X_2 = 1$)
* **Calendar Window:** October 22 – November 2, 2026.
* **Analysis Deliverable:**
  - Freeze Shewhart control limits based on Phase III in-control data.
  - Compute Process Capability ($C_p, C_{pk}$) and Performance ($P_p, P_{pk}$) against customer latency targets.
  - Fit Ordinary Least Squares (OLS) response transfer function:
    $$Y = \alpha_0 + \alpha_1 X_1 + \alpha_2 X_2$$

---

## 4. Deterministic Quality Gate Specification

Every transformed Markdown document must satisfy three deterministic criteria before acceptance:

```text
                  [ Generated Markdown Output ]
                               │
                               ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Gate 1: Structural Completeness                             │
 │ Must contain exact Level-2 Markdown headers:                │
 │   • ## Core Synthesis                                       │
 │   • ## Technical Taxonomy                                   │
 │   • ## Analytical Formulations                              │
 └─────────────────────────────┬───────────────────────────────┘
                               │ PASS
                               ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Gate 2: Syntactical Validity                                │
 │ LaTeX block delimiters ($$) must be evenly balanced.        │
 │ delimiter_count % 2 == 0                                    │
 └─────────────────────────────┬───────────────────────────────┘
                               │ PASS
                               ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Gate 3: Empty Formula Rule                                  │
 │ If no mathematical formulas exist in source document page:  │
 │ "## Analytical Formulations" must contain "NONE RECORDED"   │
 └─────────────────────────────┬───────────────────────────────┘
                               │ PASS
                               ▼
                     [ CONFORMING OUTPUT ]
```

### Defect Handling & Rework Cycle
If an output fails any rule:
1. Conformance flag is marked as `0`.
2. Detailed diagnostic bullets are compiled.
3. The engine generates a reflection prompt detailing the exact deficiency.
4. Gemini is asked to regenerate the full document.
5. If the document passes on a subsequent iteration, the final output is saved, and the rework count ($P$) is logged in the CSV ledger.

---

## 5. Ledger & Telemetry Specification

The CSV ledger at `data/main_event_log.csv` records 20 standardized columns:

| Col # | Field Name | Type | Example | Description |
| :-: | :--- | :---: | :--- | :--- |
| 1 | `run_id` | Integer | `1` | Sequential run identifier ($1, 2, \dots$). |
| 2 | `timestamp` | ISO-8601 | `2026-09-03T18:24:00.123456+00:00` | UTC timestamp of run dispatch. |
| 3 | `phase` | String | `Phase_I` | Active calendar phase. |
| 4 | `operator` | String | `analyst_1` | Operator conducting the transformation. |
| 5 | `model_version` | String | `gemini-3.8-flash` | Server-side model checkpoint. |
| 6 | `input_file` | String | `page_001.pdf` | Sliced source page processed. |
| 7 | `factor_x1` | Integer | `0` | Context Buffer: `0`=Accumulating, `1`=Reset. |
| 8 | `factor_x2` | Integer | `0` | Prompt Schema: `0`=Bare, `1`=SOP Schema. |
| 9 | `context_tokens` | Integer | `3410` | Backlog WIP tokens from prior turns. |
| 10 | `instruction_tokens` | Integer | `32` | Prompt template tokens ($\approx 32$ Bare, $\approx 380$ SOP). |
| 11 | `page_tokens` | Integer | `465` | Raw textbook page text tokens. |
| 12 | `framing_tokens` | Integer | `18` | Protocol framing & delimiter tokens ($\epsilon$). |
| 13 | `prompt_tokens` | Integer | `3925` | Total forward-pass API input tokens. |
| 14 | `output_tokens` | Integer | `280` | Generated response candidate tokens. |
| 15 | `total_tokens` | Integer | `4205` | Total transaction tokens (`prompt + output`). |
| 16 | `conforming` | Integer | `1` | First-pass quality status (`1`=Conforming, `0`=Defect). |
| 17 | `rework_cycles` | Integer | `0` | Number of reflection prompts dispatched ($P$). |
| 18 | `finish_reason` | String | `STOP` | Provider finish reason (`STOP`, `MAX_TOKENS`, etc.). |
| 19 | `cycle_time_sec` | Float | `6.4215` | **Primary Response ($Y$):** Cycle time in seconds. |
| 20 | `assignable_cause` | String | `NONE` | Special cause annotation (`NONE` if in-control). |

---

## 6. Troubleshooting & Operational FAQs

### 1. `GEMINI_API_KEY is not configured`
* **Symptom:** CLI exits with error: `ValueError: GEMINI_API_KEY is not configured.`
* **Solution:** Create a `.env` file in the project root containing your API key:
  ```env
  GEMINI_API_KEY=AIzaSy...your_real_key_here
  ```

### 2. `No input files found in 'data/inputs'`
* **Symptom:** `spc run` reports: `FileNotFoundError: No input files found in 'data/inputs'.`
* **Solution:** Slice your textbook PDF first using `spc slice`:
  ```bash
  spc slice --book data/raw/textbook.pdf --start 1 --end 30
  ```

### 3. Session Cache Corrupted or Deleted
* **Symptom:** Phase I session memory is accidentally wiped or contains corrupted JSON.
* **Solution:** Reconstruct the multi-turn session cache from forensic JSON logs:
  ```bash
  spc rebuild-cache --phase Phase_I
  ```

### 4. Cloud Webhook Timeout or Failure
* **Symptom:** Google Sheets fails to receive rows; terminal displays `Cloud Webhook: Skipped / Offline`.
* **Solution:**
  1. Webhook failures are non-blocking; the local CSV and forensic audit files are always committed safely.
  2. Verify that `SHEET_WEBHOOK_URL` in `.env` matches the deployed Apps Script URL.
  3. Ensure the Apps Script web app deployment has access set to **"Anyone"** (refer to [Google Sheets Webhook Setup Guide](spreadsheet_webhook_setup.md)).

### 5. Running Experiments Outside Scheduled Calendar Dates
* **Symptom:** `spc run` raises: `ValueError: Date does not fall within any configured experimental phase window.`
* **Solution:** Pass an explicit phase override flag:
  ```bash
  spc run --phase Phase_I
  ```
