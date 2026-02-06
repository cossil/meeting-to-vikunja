from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import AnalysisResponse, SyncRequest, SyncResponse, SyncDetail
from app.services.task_processor import TaskProcessor
from app.services.vikunja_service import VikunjaService

router = APIRouter()
processor = TaskProcessor()
vikunja_service = VikunjaService()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_meeting(file: UploadFile = File(...)):
    """
    Analyze a meeting transcript/notes file and extract tasks.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
            
        result = await processor.process_file(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync", response_model=SyncResponse)
async def sync_tasks(request: SyncRequest):
    """
    Sync a list of tasks to Vikunja.
    """
    success_count = 0
    failed_count = 0
    details = []

    for task in request.tasks:
        try:
            result = await vikunja_service.create_task(task)
            if result:
                success_count += 1
                details.append(SyncDetail(title=task.title, status="success"))
            else:
                failed_count += 1
                details.append(SyncDetail(title=task.title, status="error", error="Failed to create task"))
        except Exception as e:
            failed_count += 1
            details.append(SyncDetail(title=task.title, status="error", error=str(e)))

    return SyncResponse(
        total=len(request.tasks),
        success=success_count,
        failed=failed_count,
        details=details
    )
