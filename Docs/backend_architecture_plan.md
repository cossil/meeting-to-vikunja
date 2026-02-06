# Backend Architecture Plan - Phase 1: Foundation & Batch Porting

## 1. Directory Structure

The new backend will utilize a standard FastAPI structure, clearly separating configuration, data models, business logic (services), and API routing.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point & FastAPI app definition
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Environment variables (VIKUNJA_API_TOKEN, etc.)
│   │   └── exceptions.py       # Custom error handling
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models (Input/Output definitions)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vikunja_client.py   # Ported VikunjaClient (from logic.py)
│   │   ├── gemini_service.py   # Ported GeminiService (from logic.py)
│   │   ├── glossary_manager.py # Ported GlossaryManager (from logic.py)
│   │   └── task_processor.py   # Ported TaskProcessor (from logic.py)
│   └── api/
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── endpoints/
│               ├── __init__.py
│               └── analysis.py     # Endpoint definition for /analyze-file
├── .env                        # Local environment variables
└── requirements.txt            # Project dependencies
```

## 2. Dependencies

We will retain existing logic dependencies and add FastAPI requirements.

**New Dependencies:**
*   `fastapi`: Web framework.
*   `uvicorn[standard]`: ASGI server.
*   `python-multipart`: Required for handling form data and file uploads.
*   `pydantic-settings`: For robust configuration management.

**Retained Dependencies (from V1):**
*   `requests`: For Vikunja API calls.
*   `pandas`: Used in `TaskProcessor` and data handling (preserved per "Strict Porting").
*   `thefuzz`: For fuzzy matching assignees.
*   `google-genai`: For Gemini API.
*   `python-docx`: For parsing .docx files.
*   `python-dotenv`: For loading .env files.

## 3. API Schema Draft (Pydantic Models)

These models will reside in `app/models/schemas.py`.

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- Common Models ---

class TaskBase(BaseModel):
    title: str = Field(..., description="Actionable title (Verb + Object)")
    description: Optional[str] = Field(None, description="Full context/description")
    assignee_name: Optional[str] = Field(None, description="Raw name extracted from text")
    assignee_id: Optional[int] = Field(None, description="Vikunja User ID (resolved)")
    priority: int = Field(1, ge=1, le=5, description="Priority level 1-5")
    due_date: Optional[str] = Field(None, description="ISO Format YYYY-MM-DD")

# --- Response Models ---

class AnalysisResponse(BaseModel):
    tasks: List[TaskBase]
    token_count: int
    processing_time: float

# --- Request Models ---
# Note: Input parameters for /analyze-file will be Form fields to support File Upload
# The main input is 'files': List[UploadFile]
# Metadata:
# - meeting_date: date
# - custom_instructions: Optional[str]
```

## 4. Migration Strategy

We will migrate logical components one by one, ensuring they function identically to V1 but with necessary adjustments for the stateless web context.

**Step 1: Environmental Setup**
*   Create `app/core/config.py` using `pydantic-settings` to load `VIKUNJA_API_TOKEN`, `VIKUNJA_API_URL`, `TARGET_PROJECT_ID`, and `GOOGLE_API_KEY`.
*   Establish `app/main.py` with the FastAPI app instance and CORS middleware.

**Step 2: Porting `GlossaryManager`**
*   **Source:** `logic.py` -> `GlossaryManager`
*   **Destination:** `app/services/glossary_manager.py`
*   **Changes:**
    *   Ensure file paths are absolute or relative to the app root (not CWD dependent if possible).
    *   Mark file I/O operations with `# TODO: V2_RESILIENCE` if they block the event loop (though acceptable for Phase 1).

**Step 3: Porting `TaskProcessor`**
*   **Source:** `logic.py` -> `TaskProcessor`
*   **Destination:** `app/services/task_processor.py`
*   **Changes:**
    *   Adapt `extract_text_from_file` to handle `UploadFile` (bytes) from FastAPI instead of local file paths.
    *   Preserve `match_assignee` logic exactly.

**Step 4: Porting `VikunjaClient`**
*   **Source:** `logic.py` -> `VikunjaClient`
*   **Destination:** `app/services/vikunja_client.py`
*   **Changes:**
    *   Inject `token` and `api_url` from `app.core.config` settings instead of `os.getenv` directly within the class.
    *   Convert `fetch_users` to a cached method or dependency if needed (keep simple for Phase 1).

**Step 5: Porting `GeminiService`**
*   **Source:** `logic.py` -> `GeminiService`
*   **Destination:** `app/services/gemini_service.py`
*   **Changes:**
    *   Inject `GlossaryManager` as a dependency rather than instantiating it inside.
    *   Maintain the prompt structure exactly.

**Step 6: Endpoint Implementation**
*   Create `app/api/v1/endpoints/analysis.py`.
*   Define `POST /analyze`.
*   **Logic Flow:**
    1.  Receive `files`, `date`, `instructions`.
    2.  Instantiate `TaskProcessor` to read file content from memory.
    3.  Load `GlossaryManager`.
    4.  Call `GeminiService.analyze_meeting_notes` with combined text.
    5.  Call `TaskProcessor.match_assignee` using cached user list from `VikunjaClient`.
    6.  Return JSON response matching `AnalysisResponse`.

**Step 7: Verification**
*   Verify the endpoint returns JSON structure identical to the internal dictionary used in the V1 Streamlit app.
