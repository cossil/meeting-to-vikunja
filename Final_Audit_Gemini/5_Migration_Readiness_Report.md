# 5) Migration Readiness Report (React/FastAPI V2)

> **Audit Date:** 2026-02-04
> **Status:** [Active] Assessment for moving from Streamlit to React + FastAPI

## 1. Executive Summary

| Component | Portability | Effort to Migrate | Verdict |
| :--- | :--- | :--- | :--- |
| **Backend Logic** (`logic.py`) | ✅ **High** | Low | Pure Python, `requests`/`google-genai` based. |
| **Voice Core** (`voice_core.py`) | ✅ **High** | Low | Pydantic models & Service pattern are ready. |
| **Frontend UI** (`app.py`, `voice_ui.py`) | ❌ **None** | High | **Complete Rewrite Required**. Tightly coupled to Streamlit. |
| **State Management** | ⚠️ **Medium** | Medium | `st.session_state` must move to WebSocket/DB. |

**Overall Assessment**: The "Business Logic" is well-isolated and can be ported to FastAPI with near-zero changes. The "Application Layer" (UI & State) requires a full re-architecture from Streamlit's rerun loop to a reactive Event-Driven model (React + WebSockets).

---

## 2. Logic Portability Analysis

### 2.1 `logic.py` (Batch & Vikunja)
*   **Status**: **100% Portable**.
*   **Dependencies**: `requests`, `pandas`, `google-genai`, `python-docx`, `python-dotenv`.
*   **No Streamlit Imports**: Verified.
*   **Migration Actions**:
    *   Remove global `load_dotenv()` side-effect; move to `core/config.py`.
    *   Add validation to `VikunjaClient` (currently fails silently on missing env vars).
    *   Convert `print()` error logging to structured logging (e.g., `structlog`).

### 2.2 `voice_core.py` (Voice Agent Service)
*   **Status**: **High Portability**.
*   **Dependencies**: `google-genai`, `pydantic`.
*   **Architecture**: Already follows a Service-Repository pattern.
*   **Migration Actions**:
    *   **Audio Interface**: Currently accepts raw bytes (`mime_type="audio/wav"`). V2 should enforce strict content-type validation at the API layer.
    *   **Logging**: `BenchmarkLogger` writes to local JSONL. In V2, redirect to standard out or metrics collector (Prometheus/OpenTelemetry).

---

## 3. State Management Migration

### 3.1 Current State (`st.session_state`)
Streamlit persists these objects between reruns:
1.  `voice_service` (Singleton)
2.  `voice_task_state` (Pydantic Dict)
3.  `voice_agent_history` (List)
4.  `last_audio_hash` (Deduplication)

### 3.2 V2 Strategy (FastAPI + WebSocket)
Instead of implicit session state, V2 requires explicit session management.

**Recommended Architecture:**
*   **Protocol**: WebSocket (`/ws/voice`) for low-latency audio/text turns.
*   **Session Store**:
    *   **In-Memory (MVP)**: Dictionary mapping `client_id` -> `VoiceSession`.
    *   **Redis (Production)**: Persist `VoiceTaskState` and history to Redis.

**FastAPI Example:**
```python
@router.websocket("/ws/voice")
async def voice_endpoint(websocket: WebSocket, service: VoiceAgentService = Depends(get_service)):
    await websocket.accept()
    # Initialize Session
    state = VoiceTaskState()
    
    while True:
        # Receive Audio Chunk
        data = await websocket.receive_bytes()
        
        # Process Turn
        response = service.process_audio_turn(data, state.dict(by_alias=True))
        
        # Update State
        state = response.updated_task
        
        # Send Audio + JSON back
        await websocket.send_json({"text": response.reply_text, "state": state.dict()})
        # (Send audio bytes separately)
```

---

## 4. Critical Blockers & React Replacements

The Streamlit UI relies on primitives that have no direct drop-in replacement in React.

| Streamlit Primitive | Function | React Replacement | Complexity |
| :--- | :--- | :--- | :--- |
| `st.audio_input` | Records mic, handles encoding | **MediaRecorder API** (Custom Hook required) | High |
| `st.rerun` | Updates UI after interaction | **React State** (`useState`, `useEffect`) | Medium |
| `st.chat_input` | Text entry | `<input>` + State | Low |
| `st.markdown(html=True)` | Custom Bubble CSS | **JSX + CSS Modules / Tailwind** | Low |
| `st.data_editor` | Review Tasks | **TanStack Table** or **AG Grid** | Medium |
| Local File Cache | `welcome_fixed.wav` | Static Asset / CDN | Low |

### 4.1 Audio Recording Implementation
In Streamlit, this is one line. In React, you must implement:
1.  Browser permission handling (`navigator.mediaDevices.getUserMedia`).
2.  `MediaRecorder` lifecycle (start/stop/dataavailable).
3.  Blob creation (`audio/wav`) and WebSocket transmission.

---

## 5. Proposed V2 Architecture

### 5.1 Backend Structure (FastAPI)
```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── tasks.py       # Batch Upload & Sync
│   │   │   └── voice.py       # WebSocket Endpoint
│   │   └── deps.py            # Dependency Injection
│   ├── core/
│   │   └── config.py          # Env Vars
│   ├── services/
│   │   ├── gemini.py          # Ported from logic.py
│   │   └── voice_agent.py     # Ported from voice_core.py
│   └── schemas/               # Pydantic Models
└── main.py
```

### 5.2 Frontend Structure (React/Vite)
```
frontend/
├── src/
│   ├── components/
│   │   ├── audio/
│   │   │   └── AudioRecorder.tsx  # MediaRecorder Hook
│   │   ├── chat/
│   │   │   └── ChatBubble.tsx
│   │   └── task/
│   │       └── TaskCard.tsx       # JSON Visualization
│   ├── hooks/
│   │   └── useVoiceAgent.ts       # WebSocket Logic
│   └── pages/
│       ├── FileUploadPage.tsx
│       └── VoiceAgentPage.tsx
```

---

## 6. Migration Roadmap

### Phase 1: Backend Lift & Shift (Days 1-3)
1.  Initialize FastAPI project.
2.  Copy `logic.py` and `voice_core.py` to `services/`.
3.  Create REST endpoint `POST /analyze` for file uploads.
4.  Create REST endpoint `POST /sync` for Vikunja.

### Phase 2: Voice WebSocket (Days 4-6)
1.  Implement `WebSocket` endpoint in FastAPI.
2.  Wire up `VoiceAgentService.process_audio_turn`.
3.  Validate audio format compatibility (frontend blob vs backend pcm/wav).

### Phase 3: React Frontend (Days 7-14)
1.  Scaffold Vite + Tailwind + shadcn/ui.
2.  Implement `AudioRecorder` hook.
3.  Build Chat Interface.
4.  Connect to WebSocket.

### Phase 4: Integration & Polish (Days 15-20)
1.  Replace local file caches (`welcome_fixed.wav`, `glossary.json`) with proper storage/DB.
2.  Add Error Handling (Toast notifications).
3.  Deploy (Docker).

---

## 7. Effort Estimate
**Total Estimated Effort**: ~20 Person-Days

*   **Backend**: 5 Days (High reuse of existing logic).
*   **Frontend**: 10 Days (Complete rewrite of audio/chat mechanics).
*   **Integration/Testing**: 5 Days.
