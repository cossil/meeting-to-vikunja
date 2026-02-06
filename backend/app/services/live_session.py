import json
import asyncio
import websockets
import base64
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from app.core.config import settings
from app.services.task_processor import get_system_prompt, GlossaryManager

GLOSSARY = GlossaryManager()

# Tool Definition
update_task_draft_tool = {
    "function_declarations": [
        {
            "name": "update_task_draft",
            "description": "Updates the current draft of the task based on user voice input.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING", "description": "The title of the task."},
                    "description": {"type": "STRING", "description": "The description or notes for the task."},
                    "assignee": {"type": "STRING", "description": "Who is responsible for the task."},
                    "dueDate": {"type": "STRING", "description": "Due date in YYYY-MM-DD format."},
                    "priority": {"type": "INTEGER", "description": "Priority from 1 (Low) to 5 (Critical)."}
                },
                "required": ["title"]
            }
        }
    ]
}

class GeminiLiveSession:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.model = "gemini-2.0-flash-exp"
        self.host = "generativelanguage.googleapis.com"
        self.uri = f"wss://{self.host}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"

    async def start(self, client_ws: WebSocket):
        await client_ws.accept()
        
        # Prepare System Prompt
        glossary_rules = GLOSSARY.get_prompt_rules()
        meeting_date = datetime.now().strftime('%d/%m/%Y')
        system_instruction = get_system_prompt(meeting_date, "Voice Interaction Mode", glossary_rules)
        
        # Connect to Google
        try:
            async with websockets.connect(self.uri) as google_ws:
                # 1. Send Setup Message
                setup_msg = {
                    "setup": {
                        "model": f"models/{self.model}",
                        "tools": [update_task_draft_tool],
                        "system_instruction": {
                            "parts": [{"text": system_instruction}]
                        }
                    }
                }
                await google_ws.send(json.dumps(setup_msg))
                
                # 2. Handshake response (initial config)
                first_msg = await google_ws.recv()
                # print(f"Google Handshake: {first_msg}") # Debug

                # 3. Start Bidirectional Loop
                await asyncio.gather(
                    self.client_to_google(client_ws, google_ws),
                    self.google_to_client(google_ws, client_ws)
                )
        except Exception as e:
            print(f"Session Error: {e}")
            await client_ws.close()

    async def client_to_google(self, client_ws: WebSocket, google_ws: websockets.WebSocketClientProtocol):
        try:
            while True:
                # Receive raw bytes (audio) or text (control) from Client
                data = await client_ws.receive()
                
                if "bytes" in data:
                    # Forward audio
                    realtime_input = {
                        "realtime_input": {
                            "media_chunks": [{
                                "mime_type": "audio/pcm",
                                "data": base64.b64encode(data["bytes"]).decode("utf-8")
                            }]
                        }
                    }
                    await google_ws.send(json.dumps(realtime_input))
                
                elif "text" in data:
                    # Handle text control messages if needed (e.g. stop generation)
                    pass

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error reading from client: {e}")

    async def google_to_client(self, google_ws: websockets.WebSocketClientProtocol, client_ws: WebSocket):
        try:
            async for raw_msg in google_ws:
                msg = json.loads(raw_msg)
                
                # Check for Tool Calls
                server_content = msg.get("serverContent")
                if server_content:
                    model_turn = server_content.get("modelTurn")
                    if model_turn:
                        parts = model_turn.get("parts", [])
                        for part in parts:
                            
                            # Handle Audio Response
                            if "inlineData" in part:
                                # Send audio bytes directly to client
                                audio_b64 = part["inlineData"]["data"]
                                await client_ws.send_bytes(base64.b64decode(audio_b64))
                            
                            # Handle Tool Call (Task Update)
                            if "functionCall" in part:
                                fn = part["functionCall"]
                                if fn["name"] == "update_task_draft":
                                    args = fn["args"]
                                    # Send event to Client frontend
                                    await client_ws.send_json({
                                        "type": "task_update",
                                        "data": args
                                    })
                                    
                                    # We must respond to the tool call to keep the turn going
                                    tool_response = {
                                        "tool_response": {
                                            "function_responses": [{
                                                "name": "update_task_draft",
                                                "response": {"status": "ok", "ack": True},
                                                "id": fn.get("id", "unk") # Important if IDs are used
                                            }]
                                        }
                                    }
                                    await google_ws.send(json.dumps(tool_response))

        except Exception as e:
            print(f"Error reading from Google: {e}")
