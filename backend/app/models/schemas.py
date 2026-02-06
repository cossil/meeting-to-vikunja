from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# --- Common Models ---

class TaskBase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    title: str = Field(..., description="Actionable title (Verb + Object)")
    description: Optional[str] = Field(None, description="Full context/description")
    assignee_name: Optional[str] = Field(None, description="Raw name extracted from text")
    assignee_id: Optional[int] = Field(None, description="Vikunja User ID (resolved)")
    priority: int = Field(1, ge=1, le=5, description="Priority level 1-5")
    due_date: Optional[str] = Field(None, description="ISO Format YYYY-MM-DD")

# --- Response Models ---

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    tasks: List[TaskBase]
    token_count: int
    processing_time: float

# --- Sync Models ---

class SyncRequest(BaseModel):
    tasks: List[TaskBase]

class SyncDetail(BaseModel):
    title: str
    status: str # 'success' or 'error'
    error: Optional[str] = None

class SyncResponse(BaseModel):
    total: int
    success: int
    failed: int
    details: List[SyncDetail]
