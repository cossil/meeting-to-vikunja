# Backend Phase 4 Report - Live Mode (WebSocket Proxy)

## Overview
Implemented the **WebSocket Proxy** pattern to enable low-latency, full-duplex voice interaction with Google's Gemini Multimodal Live API (`gemini-2.0-flash-exp`).

## Architecture
1.  **Endpoints**: `ws://localhost:8000/api/v1/voice/live`
2.  **Proxy Logic** (`app/services/live_session.py`):
    *   Acts as a bridge between the Client and `wss://generativelanguage.googleapis.com`.
    *   **Handshake**: Sends `BidiGenerateContentSetup` with system prompt and tools.
    *   **Loop**: Streams audio bytes bidirectionally.
    *   **Tool Interception**: Detects `update_task_draft` calls from Gemini and emits a `task_update` event JSON to the client, allowing the Frontend UI to update in real-time.

## Implemented Components
1.  **Refactored System Prompt**: Extracted `get_system_prompt` in `task_processor.py` to ensure the Live Agent behaves exactly like the Batch Processor.
2.  **Tools**: Defined `update_task_draft` (JSON Schema) for the Live session.
3.  **Endpoint**: Registered `/api/v1/voice/live`.

## Dependencies
*   `websockets`: Added for upstream connection.

## Next Steps
*   Frontend integration (connecting `AudioRecorder` to this WebSocket).
