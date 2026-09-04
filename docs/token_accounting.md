# Token Accounting & Lifecycle Specification

## 1. Executive Summary & Purpose
In Statistical Process Control (SPC) applied to generative AI pipelines, total token consumption cannot be treated as a single homogeneous number. Token usage is comprised of distinct physical mechanisms:
* **Static Input Data:** Raw source text ($I$).
* **Prompt Engineering Overhead:** Schema instructions ($X_2$) and framing protocols ($\epsilon$).
* **Process Backlog (WIP):** Prior conversation history ($X_1$).
* **Quality Remediation Waste:** Dynamic reflection rework loops ($W_{\text{rework}}$).
* **Model Reasoning Effort:** Internal thinking/scratchpad generation ($T$).

This specification formalizes how each token tier is measured, how protocol boundaries are handled, and why live multi-turn session tokens differ from serialized cache tokens.

---

## 2. Multi-Turn Token Decomposition Equation

For every experimental run logged in `data/main_event_log.csv`, the total prompt tokens ($W$) of the final accepted attempt satisfy the **Token Invariant**:

$$W = \text{context\_tokens} + \text{instruction\_tokens} + \text{page\_tokens} + \text{framing\_tokens} + \text{rework\_tokens}$$

The total transactional footprint processed across the entire run is defined as:

$$\text{total\_tokens} = W + \text{output\_tokens} + \text{thinking\_tokens}$$

Where:
* **`context_tokens` ($X_1$):** Token footprint of prior turns loaded from `.cache/session_cache.json` ($0$ in `Phase_II`+ due to daily reset).
* **`instruction_tokens` ($X_2$):** Pure tokens of the task prompt template ($\approx 20$ tokens for Bare prompt, $\approx 380$ tokens for SOP schema).
* **`page_tokens` ($I$):** Raw tokens contained within the extracted text of the input PDF page.
* **`framing_tokens` ($\epsilon$):** Protocol overhead injected by the API provider's server-side chat template.
* **`rework_tokens` ($W_{\text{rework}}$):** Additional input tokens injected during dynamic reflection rework loops ($P > 0$).
* **`output_tokens` ($O$):** Candidate tokens of the final accepted conforming Markdown output.
* **`thinking_tokens` ($T$):** Cumulative model reasoning/thinking tokens generated across all attempts in the run.

---

## 3. Protocol Framing & Special Boundary Tokens

### 3.1 Why Raw Text Count $\ne$ API Prompt Tokens
If you run a local tokenizer on the bare strings:
$$\text{count}(\text{prompt}) = \text{instruction\_tokens} + \text{page\_tokens}$$
However, when submitted to the Google GenAI API endpoint, the reported `prompt_token_count` is higher by **$\approx 8$ tokens**. This difference represents **`framing_tokens` ($\epsilon$)**.

### 3.2 Chat Template Injection
LLMs are autoregressive next-token predictors that require special boundary tokens to distinguish conversational roles. The API server automatically injects these boundary markers when serializing JSON messages:

```text
[System/Protocol Boundary] ──> <|turn_start|>user
[Instruction + Source Text] ──> Extract the core analytical synthesis...
[Turn Delimiter]           ──> <|turn_end|>
[Model Generation Header]  ──> <|turn_start|>model
```

These structural delimiter tokens ($\approx 8$ tokens per turn) constitute protocol overhead. The engine calculates this dynamically on Attempt 0:
$$\text{framing\_tokens} = \max(0, \text{initial\_prompt\_tokens} - (\text{context\_tokens} + \text{instruction\_tokens} + \text{page\_tokens}))$$

### 3.3 End-of-Turn Preemption (EOS / Stop Tokens)
When the model concludes its generation:
1. It generates a reserved End-of-Sequence token (e.g., `<|eot_id|>` or `EOS`).
2. The server-side inference engine halts decoding immediately upon encountering this token.
3. The server sets `finish_reason = "STOP"` in the response metadata and **strips the stop token from the returned output string**.
4. The client receives clean Markdown text. No raw control tokens are ever persisted into `.cache/session_cache.json` or `data/outputs/`.

---

## 4. Thinking Tokens: Live Chat vs. Cache Persistence

Models equipped with extended reasoning (such as `gemini-3.5-flash` or `gemini-3.8-flash`) generate internal thinking traces (`thoughts_token_count`) prior to producing output text.

### 4.1 Live In-Memory Accumulation (During Rework)
During an active transformation with rework loops ($P \ge 1$):
* **Attempt 0:** Model generates Thinking Trace 0 ($T_0$) + Draft Output 0.
* **Attempt 1:** When the rework prompt is sent inside the live Python `chat` session, the API server retains Attempt 0's thinking trace in its active session context. Consequently, Attempt 1's reported `prompt_tokens` includes $T_0$.
* This behavior mirrors real-world web chats and IDE agents during an active multi-turn session.

### 4.2 Discarding Thinking Tokens on Persistence
Once a run completes (producing a conforming artifact):
1. Only the clean conversational text turns (user prompt text + model Markdown output) are committed to `.cache/session_cache.json`.
2. **All internal thinking traces are discarded.**

**Why Thinking Tokens Are Discarded from History:**
1. **Context Bloat Prevention:** Thinking traces range from 800 to 4,000+ tokens per attempt. Preserving them in cache would exhaust the context window and trigger exponential cost and latency penalties.
2. **Preventing Reasoning Anchoring:** Retaining discarded intermediate hypotheses from previous turns can bias or confuse subsequent model transformations.
3. **Industry Standard:** All major LLM interfaces (ChatGPT, Claude Web, Cursor, Copilot) discard ephemeral scratchpads from multi-turn history.

---

## 5. End-to-End Concrete Accounting Walkthrough

The following table traces the real data logged between Run #001 (with 1 rework) and Run #002 (first-pass conforming):

| Metric | Run #001 (page_016.pdf) | Run #002 (page_017.pdf) | Mathematical Origin |
| :--- | :---: | :---: | :--- |
| **Context Tokens ($X_1$)** | `0` | `1,646` | Clean text of Run 1 turns re-tokenized from cache |
| **Instruction Tokens ($X_2$)** | `20` | `20` | Bare prompt instructions |
| **Page Tokens ($I$)** | `404` | `660` | Extracted page content |
| **Framing Tokens ($\epsilon$)** | `8` | `8` | API protocol delimiters |
| **Rework Tokens ($W_{\text{rework}}$)** | `1,640` | `0` | Added input tokens from Attempt 0's draft + rework prompt |
| **Prompt Tokens ($W$)** | **`2,072`** | **`2,334`** | $W = X_1 + X_2 + I + \epsilon + W_{\text{rework}}$ |
| **Output Tokens ($O$)** | `362` | `523` | Clean Markdown response tokens |
| **Thinking Tokens ($T$)** | **`1,659`** | **`1,136`** | Cumulative reasoning tokens ($789 + 870 = 1,659$) |
| **Total Tokens Processed** | **`4,093`** | **`3,993`** | $\text{Total} = W + O + T$ |
| **Active Cache Size (Next Run)** | `1,646` tokens (4 turns) | `2,858` tokens (6 turns) | Clean text re-tokenized (thinking discarded) |
