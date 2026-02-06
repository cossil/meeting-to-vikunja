# 4) Voice Agent Mechanics (V1 Implementation)

> **Audit Date:** 2026-02-04
> **Status:** [Active] Deep Dive into `voice_ui.py` and `voice_core.py`

## 1. Latency Optimization Strategy

The V1 Voice Agent employs a multi-layered strategy to mask the inherent latency of LLM and TTS APIs.

### 1.1 Connection Warmup (`warmup_tts`)
**Goal:** Eliminate the SSL/TCP handshake and model loading overhead for the first TTS call.
**Mechanism:**
*   **Trigger:** Called once during `VoiceAgentService` initialization in `voice_ui.py`.
*   **Payload:** Sends a silent request with text `"Oi"` to `gemini-2.5-flash-preview-tts`.
*   **Behavior:**
    *   Wrapped in `try/except` (non-blocking).
    *   Failures are logged to `latency_logs.jsonl` but do not alert the user.
    *   **Evidence:** Logs show average successful warmup takes ~1.5s - 3s. Failures (500 Internal) are observed but rare.

### 1.2 Greeting Cache (`welcome_fixed.wav`)
**Goal:** Zero-latency startup for the user session.
**Mechanism:**
*   **Check:** `voice_ui.py` checks for local file `welcome_fixed.wav`.
*   **Hit:** Loads bytes directly (< 50ms).
*   **Miss:** Generates speech via API, saves to disk for future runs.
*   **Impact:** Reduces initial "time-to-first-sound" from ~3s to ~0.05s.

### 1.3 Audio Deduplication (`last_audio_hash`)
**Goal:** Prevent infinite processing loops caused by Streamlit's "sticky" widget state.
**Mechanism:**
*   Computes MD5 hash of `audio_input` bytes.
*   Compares with `st.session_state['last_audio_hash']`.
*   Only processes if hash differs; otherwise, treats as a UI refresh.

---

## 2. Conversation & State Loop

### 2.1 The Turn Cycle
1.  **Input**: User speaks (`st.audio_input`) or types (`st.chat_input`).
2.  **Processing**: `VoiceAgentService` sends input + `current_task` JSON to Gemini.
3.  **State Update**: Gemini returns `VoiceGeminiResponse` containing:
    *   `updatedTask`: Pydantic model (`VoiceTaskState`) updates fields.
    *   `replyText`: Text for the agent to speak.
4.  **TTS**: `generate_speech` converts `replyText` to WAV (PCM wrapped in WAV container).
5.  **Render**: UI appends to history and calls `st.rerun()` to update the chat view.

### 2.2 Task State Machine
The agent maintains a structured state object (not just conversation history) to drive the task towards completion.

| State Stage | Condition | Behavior |
| :--- | :--- | :--- |
| **Initial** | `missingInfo` has all fields. | Agent asks open-ended question. |
| **Partial** | User provides some info (e.g., "Buy milk"). | Gemini updates `title`, removes `title` from `missingInfo`. |
| **Clarification** | `missingInfo` not empty. | Agent asks for specific missing field (e.g., "When is it due?"). |
| **Two-Strike** | `clarificationStrikes` count == 2 for a field. | Agent stops asking and marks field "To Review". |
| **Complete** | `missingInfo` is empty. | Agent confirms readiness to submit. |

---

## 3. Streamlit Implementation Details

### 3.1 Custom Chat UI
**Technique:** HTML/CSS Injection via `st.markdown(..., unsafe_allow_html=True)`.
**Styles:**
*   `.user-bubble`: WhatsApp-style green, right-aligned.
*   `.agent-bubble`: White, left-aligned, containing audio player.
**Risk:** **High**. Input text is interpolated directly into HTML `div`s without sanitization, posing an XSS risk.

### 3.2 Layout Strategy
*   **Split View**: `st.columns([1, 1])`.
    *   **Left**: Chat interface (History + Inputs).
    *   **Right**: Live "Task Card" (JSON debug view) + Submit Button.
*   **Scroll**: `st.container(height=500)` ensures the chat window stays fixed-size while history grows.

### 3.3 Model Switching
**Control:** `app.py` Sidebar (`st.radio`).
**Effect:**
*   Passes `model_name` string to `process_audio_turn`/`process_text_turn`.
*   **Logic Model**: Switches between `gemini-3-flash-preview` (Smart) and `gemini-2.5-flash` (Fast).
*   **TTS Model**: **Static**. Always uses `gemini-2.5-flash-preview-tts` regardless of selection.

---

## 4. Performance & Logging

### 4.1 Benchmarking (`latency_logs.jsonl`)
The system creates a structured JSONL audit trail for every interaction.

| Event Type | Metrics | Source |
| :--- | :--- | :--- |
| `TTS Warmup` | `duration_ms`, `status` | Init |
| `Gemini Logic Processing` | `duration_ms`, `model`, `input_type` | Turn |
| `TTS Generation` | `duration_ms`, `char_count` | Turn |
| `Total Turn Time` | `duration_ms` | Turn |

### 4.2 Observed Latencies
*   **Logic (Gemini 3)**: ~7s - 12s (High latency).
*   **Logic (Gemini 2.5)**: ~4s - 5s.
*   **TTS Generation**: ~2.5s - 5s (Non-streaming).

---

## 5. Limitations (V1)
*   **No Streaming**: User must wait for full audio generation before playback starts.
*   **Blocking UI**: Streamlit reruns block interaction until the turn completes.
*   **Sample Rate**: Hardcoded to 24kHz; may cause playback artifacts on mismatched hardware.
*   **Single-Turn Memory**: Gemini prompt receives only the *current* task state, not the full conversation transcript (though `VoiceTaskState` acts as the accumulator).
