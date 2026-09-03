# GEMINI.md - Engineering Guidelines & Operational Rules

## 1. Project Overview
This project is an empirical research engine combining **Statistical Process Control (SPC)** and **Prompt Engineering** to optimize LLM transformation latency and eliminate context bloat.

---

## 2. Mandatory Architectural Constraints
1. **Strict Line Count Ceilings:** 
   - **Production Code (`src/`):** No file may exceed **150 lines of code (LOC)**. If a file approaches 150 LOC, decompose it into single-responsibility submodules.
   - **Test Suite (`tests/`):** Test files may have up to a **300 LOC hard ceiling**.
2. **Single Responsibility Principle (SRP):** Each module must have exactly one reason to change.
3. **Mirrored Test Suite:** Every production module in `src/spc/` must have a corresponding test file in `tests/`.
4. **Mandatory Test Coverage:** Test suites must be run and verified with **> 80% code coverage** before a milestone step is considered complete.
5. **Git Hygiene & Data Privacy:**
   - **NEVER** stage or commit `experimental_process_plan.md` or `implementation_plan.md`.
   - **NEVER** commit raw textbook PDFs, sliced page PDFs, or generated markdown outputs.
   - Only code, documentation, `tests/`, `data/.gitkeep`, and `data/main_event_log.csv` are tracked.
   - **NEVER** hardcode personal names, secrets, or API keys in code or configuration templates.

---

## 3. Workflow & Approval Protocol
After completing each milestone step:
1. Run all tests and verify **> 80% coverage**.
2. Perform a line-count audit verifying all files are $\le 150$ LOC.
3. Present the completed work and provide a formatted `git commit` suggestion (excluding plan files).
4. **STOP and AWAIT explicit user instruction** before advancing to the next step.

---

## 4. Key Terminology & Standards
- Primary log file: `data/main_event_log.csv`
- Experimental phases: `Phase_I`, `Phase_II`, `Phase_III`, `Phase_IV`
- Factors: $X_1$ (Context Buffer: `0`=accumulating, `1`=reset), $X_2$ (Schema: `0`=bare, `1`=SOP)
- Primary metric: $Y$ (Cycle Time $T$ in seconds)
- Inspection gate: 3 deterministic rules (Headers, LaTeX closure, `"NONE RECORDED"` empty rule)
