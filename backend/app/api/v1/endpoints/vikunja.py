from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import logging

from app.core.config import settings
from app.models.schemas import TaskBase
from app.services.vikunja_client import VikunjaClient

router = APIRouter()

@router.post("/sync")
async def sync_tasks_to_vikunja(tasks: List[TaskBase]):
    """
    Sync approved list of tasks to Vikunja.
    """
    try:
        vikunja_client = VikunjaClient(settings.VIKUNJA_API_URL, settings.VIKUNJA_API_TOKEN, settings.TARGET_PROJECT_ID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize Vikunja client: {str(e)}")

    results = {
        "total": len(tasks),
        "success": 0,
        "failed": 0,
        "details": []
    }

    for task in tasks:
        # Prepare dictionary for VikunjaClient.create_task
        task_data = task.model_dump()
        
        # Ensure dates are strings if they are date objects
        if task_data.get("due_date"):
            task_data["due_date"] = str(task_data["due_date"])

        try:
            success = vikunja_client.create_task(task_data)
            if success:
                results["success"] += 1
                results["details"].append({"title": task.title, "status": "success"})
            else:
                results["failed"] += 1
                results["details"].append({"title": task.title, "status": "failed", "error": "Vikunja API returned false"})
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"title": task.title, "status": "error", "error": str(e)})

    return results
