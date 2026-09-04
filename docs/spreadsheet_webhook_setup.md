# Google Sheets Webhook Setup Guide

This guide walks through configuring a Google Sheets webhook endpoint to capture real-time experimental transformation telemetry emitted by the SPC engine.

---

## 1. Architectural Overview

During experimental execution (`spc run`), the `TransformationExecutor` passes each finalized `RunRecord` to `WebhookClient.dispatch()`. If `SHEET_WEBHOOK_URL` is set in `.env`, a JSON payload containing all 20 standardized metrics is dispatched via HTTP POST to a Google Apps Script Web App, which appends the row to a Google Sheet.

```
[spc run] ──> [TransformationExecutor] ──> [WebhookClient]
                                                 │ (HTTP POST JSON)
                                                 ▼
                                     [Google Apps Script]
                                                 │
                                                 ▼
                                     [Google Sheets Ledger]
```

---

## 2. Step 1: Create Spreadsheet & Open Script Editor

1. Open [Google Sheets](https://sheets.new) and create a new spreadsheet (e.g. `SPC_Transformation_Ledger`).
2. In the menu bar, navigate to **Extensions** > **Apps Script**.
3. Name the Apps Script project (e.g. `spc-telemetry-webhook`).

---

## 3. Step 2: Apps Script Implementation

Replace any default boilerplate in `Code.gs` with the following implementation:

```javascript
const HEADERS = [
  "run_id",
  "timestamp",
  "phase",
  "operator",
  "model_version",
  "input_file",
  "factor_x1",
  "factor_x2",
  "context_tokens",
  "instruction_tokens",
  "page_tokens",
  "framing_tokens",
  "rework_tokens",
  "prompt_tokens",
  "output_tokens",
  "thinking_tokens",
  "total_tokens",
  "conforming",
  "rework_cycles",
  "finish_reason",
  "cycle_time_sec",
  "assignable_cause"
];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.tryLock(10000);

  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // Automatically initialize headers if sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);
    }

    const data = JSON.parse(e.postData.contents);
    const row = HEADERS.map(header => (data[header] !== undefined ? data[header] : ""));

    sheet.appendRow(row);

    return ContentService.createTextOutput(
      JSON.stringify({ status: "success", run_id: data.run_id })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "error", message: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);

  } finally {
    lock.releaseLock();
  }
}
```

---

## 4. Step 3: Deploy as Web App

1. Click **Deploy** (blue button in top right) > **New deployment**.
2. Click the **Select type** gear icon and choose **Web app**.
3. Fill in deployment settings:
   - **Description**: `SPC Real-time Telemetry Receiver`
   - **Execute as**: **Me** (`your_google_account@gmail.com`)
   - **Who has access**: **Anyone** *(Mandatory: Allows unauthenticated HTTP POST requests from the engine)*
4. Click **Deploy**.
5. Grant required Google account authorizations if prompted.
6. Copy the generated **Web app URL** (`https://script.google.com/macros/s/.../exec`).

> **Note:** Whenever you update the Apps Script code in the future, you must create a **New Version** via Deploy > Manage deployments > Edit > Version > New version.

---

## 5. Step 4: Environment Variable Configuration

Add the webhook URL to your `.env` file at the root of the project:

```env
SHEET_WEBHOOK_URL="https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
```

If you do not have a `.env` file yet, duplicate `.env.example`:

```powershell
cp .env.example .env
```

---

## 6. Step 5: Verification & Testing

### Option A: PowerShell Test

Run the following command in PowerShell to send a synthetic test record:

```powershell
Invoke-RestMethod -Uri "YOUR_WEBHOOK_URL" -Method Post -ContentType "application/json" -Body '{"run_id": 0, "timestamp": "2026-09-03T00:00:00Z", "phase": "Test", "operator": "verify", "model_version": "test", "input_file": "none", "factor_x1": 0, "factor_x2": 0, "context_tokens": 0, "instruction_tokens": 0, "page_tokens": 0, "framing_tokens": 0, "rework_tokens": 0, "prompt_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "total_tokens": 0, "conforming": 1, "rework_cycles": 0, "finish_reason": "STOP", "cycle_time_sec": 1.2345, "assignable_cause": "NONE"}'
```

### Option B: Python Test

```python
import requests

url = "YOUR_WEBHOOK_URL"
payload = {"run_id": 0, "operator": "test", "phase": "Test", "cycle_time_sec": 1.5, "conforming": 1}
res = requests.post(url, json=payload, timeout=10)
print(res.status_code, res.json())
```

Verify that headers and the test row appear in the Google Sheet.
