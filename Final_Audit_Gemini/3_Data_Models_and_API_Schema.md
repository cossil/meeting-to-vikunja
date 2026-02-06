# 3) Data Models and API Schema

> **Audit Date:** 2026-02-04
> **Status:** [Active] Pydantic Models, JSON Schemas, and API Payloads

## 1. Internal Data Models (Voice Agent)

These models are defined in `voice_core.py` using **Pydantic** and enforce the state of the conversational agent.

### 1.1 `VoiceTaskState`
**Location:** `voice_core.py:68`
**Purpose:** Represents the draft state of a task being collected via voice.

| Field | Type | Alias | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `title` | `str \| None` | - | `None` | Max 6 words. |
| `description` | `str \| None` | - | `None` | Max 150 chars. |
| `due_date` | `str \| None` | `dueDate` | `None` | Format: `YYYY-MM-DD`. |
| `assignee` | `str \| None` | - | `None` | Name (string), not ID. |
| `status` | `str` | - | `"Em Progresso"` | Internal status. |
| `missing_info` | `list[str]` | `missingInfo` | `['title', 'description', 'dueDate', 'assignee']` | Fields pending collection. |
| `clarification_strikes` | `list` | `clarificationStrikes` | `[]` | List of `ClarificationStrike` objects. |

### 1.2 `VoiceGeminiResponse`
**Location:** `voice_core.py:77`
**Purpose:** Structured output enforced on the Gemini API response.

| Field | Type | Alias | Description |
| :--- | :--- | :--- | :--- |
| `reply_text` | `str` | `replyText` | The text the agent will speak via TTS. |
| `updated_task` | `VoiceTaskState` | `updatedTask` | The new state of the task after the turn. |

---

## 2. Gemini JSON Schemas

### 2.1 Batch Mode (File Upload)
**Location:** `logic.py:207` (Prompt Definition)
**Format:** JSON Array of Objects
**Implicit Schema:**
```json
[
  {
    "title": "string (Verb + Object)",
    "description": "string (Context)",
    "assignee_name": "string (Corrected Name)",
    "priority": "integer (1-5)",
    "due_date": "string (YYYY-MM-DD) or null"
  }
]
```

### 2.2 Voice Mode (Interactive)
**Location:** `voice_core.py:173` (Config)
**Format:** Single JSON Object
**Enforced Schema:** Matches `VoiceGeminiResponse` (see 1.2).
```json
{
  "replyText": "...",
  "updatedTask": { ... }
}
```

---

## 3. Vikunja API Payload Mapping

### 3.1 Task Creation (Step 1)
**Endpoint:** `PUT /projects/{project_id}/tasks`
**Source:** `VikunjaClient.create_task` in `logic.py`

| Payload Field | Source Data | Transformation/Default |
| :--- | :--- | :--- |
| `title` | Input `title` | Stripped. Default: `"Sem título"`. |
| `description` | Input `description` | Stripped. Default: `""`. |
| `priority` | Input `priority` | Cast to int. Default: `1`. |
| `due_date` | Input `due_date` | **RFC3339 Normalization**: <br> `YYYY-MM-DD` -> `YYYY-MM-DDT23:59:59Z` <br> `YYYY-MM-DD HH:MM:SS` -> `...T...Z` |

### 3.2 Assignment (Step 2)
**Endpoint:** `PUT /tasks/{task_id}/assignees`
**Source:** `VikunjaClient.create_task` in `logic.py`

| Payload Field | Source Data | Condition |
| :--- | :--- | :--- |
| `user_id` | Input `assignee_id` | Must be non-null and castable to int. |

---

## 4. Glossary Schema
**File:** `glossary.json`
**Managed By:** `logic.GlossaryManager`

**Schema:**
```json
{
  "CorrectTerm": ["Variation1", "Variation2", "Error1"],
  "AnotherTerm": ["Alias1"]
}
```
*   **Key**: The canonical term to use in `title`, `description`, and `assignee`.
*   **Value**: List of strings that should be mapped to the key.

---

## 5. Persistence Schemas

### 5.1 Latency Log (`latency_logs.jsonl`)
**Managed By:** `voice_core.BenchmarkLogger`
**Format:** JSONL
```json
{
  "timestamp": "ISO8601 String",
  "event_type": "String",
  "duration_ms": "Float",
  "status": "String (optional)",
  "error": "String (optional)",
  "details": "Object (optional)"
}
```

### 5.2 User Cache (Session State)
**Source:** `VikunjaClient.fetch_users()`
**Structure:**
```json
{
  "id": 1,
  "username": "user",
  "name": "Display Name",
  "email": "email@example.com",
  "status": "active" (if available)
}
```
