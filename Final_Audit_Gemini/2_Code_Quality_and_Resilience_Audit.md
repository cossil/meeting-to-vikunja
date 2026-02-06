# 2) Code Quality and Resilience Audit

> **Audit Date:** 2026-02-04
> **Status:** [Active] Audit of `app.py`, `logic.py`, `voice_ui.py`, `voice_core.py`

## 1. Resilience & Error Handling Analysis

### 1.1 Critical Failure Modes

| Component | Scenario | Behavior | Verdict |
| :--- | :--- | :--- | :--- |
| **TTS Warmup** | `warmup_tts()` fails (e.g. API 500) | **Safe**: Logged to console/JSONL. App continues. | ✅ Resilient (Silent Failure) |
| **Glossary Load** | `glossary.json` malformed | **Safe**: Falls back to seed data. | ✅ Resilient (Silent Fallback) |
| **File Processing** | Corrupted `.docx` upload | **Fragile**: `TaskProcessor.extract_text_from_file` has no `try/except`. Will crash the Streamlit script for that run. | ❌ Critical Gap |
| **Gemini Interaction** | API Error mid-conversation | **Safe**: Returns fallback "polite error" response. State preserved. | ✅ Resilient |
| **Vikunja Sync** | API reachable, but Assignment fails | **Partial**: Task created, assignment skipped. User not notified of partial failure. | ⚠️ Logic Gap |

### 1.2 Exception Safety Evidence

*   **`voice_core.py`**:
    *   `process_audio_turn`: Wraps entire logic in `try/except`. Returns `updatedTask` unchanged on error to prevent state loss.
    *   `warmup_tts`: Swallows exceptions. Logs to `latency_logs.jsonl`.
*   **`logic.py`**:
    *   `VikunjaClient.create_task`: Implements 2-step process (Create -> Assign). Step 2 failure is non-fatal (`return True`).
    *   `GlossaryManager.load`: Returns `seed_data` on `json.JSONDecodeError`.
*   **`app.py`**:
    *   `init_services`: Returns `(None, None)` on failure. Downstream checks for `vikunja` existence are present but inconsistent.

---

## 2. Security Audit

### 2.1 Secrets & Configuration
*   **Env Vars**: Loaded via `python-dotenv`. No hardcoded secrets in code.
*   **Validation**:
    *   `VoiceAgentService`: **Good**. Validates `GOOGLE_API_KEY` on init.
    *   `GeminiService` (`logic.py`): **Weak**. No validation; fails only when calling API.
    *   `VikunjaClient`: **Weak**. No validation of `VIKUNJA_API_URL` or `VIKUNJA_API_TOKEN`.

### 2.2 Injection Risks
*   **HTML Injection (`voice_ui.py`)**: ⚠️ **High Risk**
    *   Code: `st.markdown(f'<div class="user-bubble">{text}</div>', unsafe_allow_html=True)`
    *   Issue: User input `text` is inserted directly into HTML. If `text` contains `<script>` or other tags, they will render.
*   **File Path Traversal (`app.py`)**: ⚠️ **Medium Risk**
    *   Code: `temp_path = f"temp_{uploaded_file.name}"`
    *   Issue: Uses unsanitized filename from user upload. While Streamlit usually handles this, explicit sanitization is recommended.

---

## 3. Code Smells & Refactoring Targets

### 3.1 Dead Code & Redundancy
*   **Unused Variable (`voice_core.py:157`)**: `b64_audio` is calculated but `audio_bytes` is passed to the API.
    ```python
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8') # Calculated
    # ...
    types.Part(inline_data=types.Blob(data=audio_bytes, ...)) # audio_bytes used instead
    ```
*   **Import Placement (`logic.py:135`)**: `import json` is hidden in the middle of the file.

### 3.2 Magic Numbers & Hardcoded Constants

| Value | Location | Recommendation |
| :--- | :--- | :--- |
| `C:\Ai\meeting_to_vikunja\Docs` | `app.py` | Use relative path or config |
| `30000` (Token Limit) | `app.py` | Extract to constant |
| `1500` (Max Tokens) | `voice_core.py` | Extract to constant |
| `0.6` (Temperature) | `voice_core.py` | Extract to constant |
| `width="stretch"` | `app.py` | Deprecated. Use `use_container_width=True` |

### 3.3 Architecture Observations
*   **State coupling**: `voice_ui.py` relies on `st.session_state` to treat `VoiceAgentService` as a singleton. This is idiomatic for Streamlit but makes unit testing the UI logic difficult.
*   **Logic Duplication**: Gemini configuration params are repeated in `process_audio_turn` and `process_text_turn`.

---

## 4. Recommendations

1.  **Fix HTML Injection**: Escape user text before rendering in `voice_ui.py`.
    ```python
    import html
    safe_text = html.escape(text)
    st.markdown(f'<div class="user-bubble">{safe_text}</div>', ...)
    ```
2.  **Sanitize File Uploads**: Wrap `TaskProcessor.extract_text_from_file` in `try/except` inside the loop in `app.py`.
3.  **Clean Up Code**: Remove unused `b64_audio` calculation in `voice_core.py` and move `import json` to top of `logic.py`.
4.  **Validate Config**: Add fail-fast checks in `VikunjaClient` and `GeminiService` constructors.
