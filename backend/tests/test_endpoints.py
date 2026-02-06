from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.models.schemas import TaskBase

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_analyze_endpoint():
    with patch("app.api.v1.endpoints.analysis.GeminiService") as mock_gemini, \
         patch("app.api.v1.endpoints.analysis.VikunjaClient") as mock_vikunja:
        
        # Mocking GeminiService behavior
        mock_gemini_instance = mock_gemini.return_value
        mock_gemini_instance.analyze_meeting_notes.return_value = [
            {
                "title": "Update migration plan",
                "description": "Review and update the V2 migration doc.",
                "assignee_name": "Alex",
                "priority": 5,
                "due_date": "2023-10-27"
            }
        ]

        # Mocking VikunjaClient behavior (fetch_users)
        mock_vikunja_instance = mock_vikunja.return_value
        mock_vikunja_instance.fetch_users.return_value = [
            {"id": 1, "name": "Alex", "username": "alex"}
        ]

        # Create a dummy file
        files = {'files': ('test.txt', b'Action Item: Update the migration plan. Assignee: Alex.', 'text/plain')}
        
        response = client.post("/api/v1/analyze", files=files)
        
        print("\n--- Raw Analysis Response ---")
        print(json.dumps(response.json(), indent=2))
        print("-----------------------------")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Update migration plan"
        assert data["tasks"][0]["assignee_id"] == 1 # Verified matching logic works

def test_sync_endpoint():
    with patch("app.api.v1.endpoints.vikunja.VikunjaClient") as mock_vikunja:
        mock_vikunja_instance = mock_vikunja.return_value
        mock_vikunja_instance.create_task.return_value = True

        tasks = [
            {
                "title": "Test Task",
                "priority": 1
            }
        ]

        response = client.post("/api/v1/sync", json=tasks)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["success"] == 1
        assert data["failed"] == 0

if __name__ == "__main__":
    # Manually run tests if executed as script
    try:
        test_health_check()
        print("✅ Health Check Passed")
        
        test_analyze_endpoint()
        print("✅ Analysis Endpoint Passed")
            
        test_sync_endpoint()
        print("✅ Sync Endpoint Passed")
            
    except AssertionError as e:
        print(f"❌ Test Failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
