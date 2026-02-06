# 1) Architecture and Dependency Map

> **Audit Date:** 2026-02-04
> **Scope:** MeetingToVikunja v1.0 (Hybrid Streamlit Application)
> **Status:** [Active] Python/Streamlit Core | [Stub/POC] React `task_assistant`

## 1. High-Level Architecture Overview

The **MeetingToVikunja** application is currently a **hybrid Streamlit application** (`app.py`) serving as the production entry point. It supports two distinct operational modes for creating tasks in Vikunja:

1.  **File Upload Mode (Batch)**: Processes uploaded meeting transcripts (`.txt`, `.md`, `.docx`) to extract tasks in bulk.
2.  **Voice Agent Mode (Interactive)**: A conversational agent that captures tasks via voice/text turns and pushes them to Vikunja one by one.

**Note on `task_assistant/`**: The codebase contains a `task_assistant` directory with a React/Vite application. This appears to be a separate Proof of Concept (POC) or a future migration target. It is **not** integrated into the active `app.py` workflow. The analysis below focuses on the active Streamlit application.

### System Blueprint

```mermaid
graph TD
  User[User] -->|Streamlit Interface| App[app.py]
  
  subgraph "Frontend Layer"
    App -->|Mode: File Upload| BatchUI[Batch Processor UI]
    App -->|Mode: Voice Agent| VoiceUI[voice_ui.py]
  end

  subgraph "Logic Layer"
    BatchUI -->|Extract & Analyze| Logic[logic.py]
    VoiceUI -->|Session Management| VoiceService[voice_core.py]
    VoiceService -->|Glossary Rules| Glossary[logic.GlossaryManager]
  end

  subgraph "External Services"
    Logic -->|Batch Analysis| Gemini[Google Gemini API]
    VoiceService -->|Chat & TTS| Gemini
    Logic -->|Create Task| Vikunja[Vikunja API]
    VoiceService -->|Create Task (Adapter)| Vikunja
  end
```

---

## 2. Dependency Graph & Data Flow

### 2.1 Entry Points & Routing

| Component | Status | Description | Key File |
| :--- | :--- | :--- | :--- |
| **Main App** | [Active] | Streamlit entry point. Handles mode selection and global config. | `app.py` |
| **Batch Logic** | [Active] | Handles file parsing, token estimation, and batch Gemini calls. | `logic.py` |
| **Voice UI** | [Active] | Handles chat bubbles, audio input/output, and task card visualization. | `voice_ui.py` |
| **Voice Core** | [Active] | Handles STT, TTS, and conversational state management. | `voice_core.py` |
| **React App** | [Stub] | Standalone React application (Vite + TypeScript). Currently unused by `app.py`. | `task_assistant/` |

### 2.2 Mode 1: File Upload (Batch)

**Flow**: `app.py` -> `logic.py` -> External APIs

1.  **Input**: User uploads files (`.txt`, `.md`, `.docx`).
2.  **Processing**: `TaskProcessor.extract_text_from_file()` consolidates content.
3.  **Analysis**: `GeminiService.analyze_meeting_notes()` sends text to Gemini (`gemini-3-flash-preview`).
    *   *Constraint*: Uses `logic.GlossaryManager` to inject correction rules.
4.  **Review**: User reviews tasks in `st.data_editor`.
5.  **Sync**: `VikunjaClient.create_task()` pushes tasks to Vikunja.

### 2.3 Mode 2: Voice Agent (Interactive)

**Flow**: `app.py` -> `voice_ui.py` -> `voice_core.py` -> External APIs

1.  **Initialization**: `voice_ui.init_voice_state()` creates a singleton `VoiceAgentService` stored in `st.session_state`.
2.  **Interaction**:
    *   **Audio**: `st.audio_input` -> `VoiceAgentService.process_audio_turn()`.
    *   **Text**: `st.chat_input` -> `VoiceAgentService.process_text_turn()`.
3.  **Model Usage**:
    *   **Logic**: User selects model in Sidebar (`gemini-3-flash-preview` or `gemini-2.5-flash`).
    *   **TTS**: Hardcoded to `gemini-2.5-flash-preview-tts` in `voice_core.py`.
4.  **State Management**: `VoiceTaskState` (Pydantic model) tracks task fields across turns.
5.  **Sync**: `voice_ui.py` adapts `VoiceTaskState` to the `VikunjaClient` payload format.

---

## 3. Infrastructure & External Dependencies

### 3.1 External APIs

| Service | Purpose | Auth Method | Config Variable |
| :--- | :--- | :--- | :--- |
| **Vikunja API** | Task Management | Bearer Token | `VIKUNJA_API_URL`, `VIKUNJA_API_TOKEN` |
| **Google Gemini** | LLM & TTS | API Key | `GOOGLE_API_KEY` |

### 3.2 Local Assets & Persistence

| File | Purpose | Access |
| :--- | :--- | :--- |
| `glossary.json` | JSON store for STT correction rules (e.g., "Rankel" -> "Hankell"). | Read/Write by `logic.GlossaryManager`. |
| `welcome_fixed.wav` | Cached TTS audio for the agent's greeting. | Read/Write by `voice_ui.py`. |
| `latency_logs.jsonl` | Append-only log for performance benchmarking. | Write by `voice_core.BenchmarkLogger`. |
| `requirements.txt` | Python dependency manifest. | Static. |

### 3.3 Python Libraries
*   **Core**: `streamlit`, `pandas`, `requests`
*   **AI/ML**: `google-genai` (Official SDK), `thefuzz` (String matching)
*   **Utils**: `python-dotenv`, `python-docx`, `pydantic`

---

## 4. Cross-Module Coupling & Invariants

*   **Shared Logic**: `voice_core.py` imports `GlossaryManager` from `logic.py`. Changes to the glossary logic affect both Batch and Voice modes.
*   **Session Persistence**: The Voice Agent relies heavily on `st.session_state` to persist the `VoiceAgentService` instance across Streamlit reruns.
*   **Model Selection**: The specific Gemini model for the Voice Agent is selected in `app.py` and passed down to `voice_ui.py`, which passes it to `process_audio_turn`.
*   **Vikunja Adapter**: The Voice Agent does not use `VikunjaClient` directly for state management, only for the final transmission. It maintains its own Pydantic state (`VoiceTaskState`) which must be mapped to `VikunjaClient`'s expected input dictionary.
