from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, date
import logging
import time

from app.core.config import settings
from app.models.schemas import AnalysisResponse, TaskBase
from app.services.task_processor import TaskProcessor
from app.services.gemini_service import GeminiService
from app.services.glossary_manager import GlossaryManager
from app.services.vikunja_client import VikunjaClient

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_file(
    files: List[UploadFile] = File(...),
    instructions: Optional[str] = Form(None),
    meeting_date: Optional[date] = Form(None),
):
    """
    Analyze uploaded meeting notes and extract tasks using Gemini.
    """
    start_time = time.time()
    
    # Defaults
    if not meeting_date:
        meeting_date = date.today()
    # Convert date to datetime as expected by GeminiService
    meeting_datetime = datetime.combine(meeting_date, datetime.min.time())
    
    if not instructions:
        instructions = ""

    # Initialize Services
    try:
        glossary_manager = GlossaryManager(settings.GLOSSARY_PATH)
        gemini_service = GeminiService(glossary_manager, settings.GOOGLE_API_KEY)
        vikunja_client = VikunjaClient(settings.VIKUNJA_API_URL, settings.VIKUNJA_API_TOKEN, settings.TARGET_PROJECT_ID)
        
        # Prefetch users for assignee matching
        # Note: In a production app, this should be cached or managed solely by ID if possible
        # But to replicate V1 logic of matching by name, we need the list.
        users_list = vikunja_client.fetch_users()
        
    except Exception as e:
        logging.error(f"Service initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")

    combined_text = ""
    token_count = 0

    try:
        for file in files:
            content = await file.read()
            text = TaskProcessor.extract_text_from_file(content, file.filename)
            if text:
               combined_text += f"\n\n--- INÍCIO DO ARQUIVO: {file.filename} ---\n{text}\n--- FIM DO ARQUIVO: {file.filename} ---\n"
        
        token_count = TaskProcessor.estimate_tokens(combined_text)
        
        if not combined_text.strip():
             raise HTTPException(status_code=400, detail="No content extracted from uploaded files.")

        # Analyze
        tasks_data = gemini_service.analyze_meeting_notes(combined_text, meeting_datetime, instructions)
        
        # Process Tasks (Match Assignees)
        processed_tasks = []
        for task in tasks_data:
             assignee_name = task.get("assignee_name")
             assignee_id = TaskProcessor.match_assignee(assignee_name, users_list, threshold=80) # Using V1 default threshold
             
             # Create TaskBase object
             task_obj = TaskBase(
                 title=task.get("title", "Sem título"),
                 description=task.get("description", ""),
                 assignee_name=assignee_name,
                 assignee_id=assignee_id,
                 priority=int(task.get("priority", 1)),
                 due_date=task.get("due_date")
             )
             processed_tasks.append(task_obj)
             
        processing_time = time.time() - start_time
        
        return AnalysisResponse(
            tasks=processed_tasks,
            token_count=token_count,
            processing_time=processing_time
        )

    except Exception as e:
        logging.error(f"Analysis processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
