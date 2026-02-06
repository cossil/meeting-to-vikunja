import httpx
from typing import List, Dict, Optional, Any
from app.core.config import settings
from app.models.schemas import TaskBase
import pandas as pd 
from thefuzz import process

class VikunjaService:
    def __init__(self):
        self.api_url = settings.VIKUNJA_API_URL.rstrip("/")
        self.token = settings.VIKUNJA_API_TOKEN
        self.project_id = 2 
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        self.timeout = 10.0
        self._users_cache = None

    async def _fetch_users(self) -> List[Dict]:
        """Busca usuários do projeto para matching."""
        if self._users_cache is not None:
            return self._users_cache
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            users_dict = {}
            # 1. Self
            try:
                resp = await client.get(f"{self.api_url}/user", headers=self.headers)
                if resp.status_code == 200:
                    u = resp.json()
                    users_dict[u['id']] = u
            except: pass
            
            # 2. Project Members
            try:
                resp = await client.get(f"{self.api_url}/projects/{self.project_id}/users", headers=self.headers)
                if resp.status_code == 200:
                    for u in resp.json():
                        users_dict[u['id']] = u
            except: pass
            
            self._users_cache = list(users_dict.values())
            return self._users_cache

    async def _resolve_assignee(self, name: str) -> Optional[int]:
        """Resolve nome para ID usando logic fuzzy."""
        if not name:
            return None
            
        users = await self._fetch_users()
        if not users:
            return None
            
        choices = []
        user_map = {}
        for u in users:
            choice = u.get("name") or u.get("username")
            if choice:
                choices.append(choice)
                user_map[choice] = u["id"]
        
        if not choices:
            return None
            
        result = process.extractOne(name, choices)
        if result and result[1] >= 80:
            return user_map[result[0]]
        return None

    async def create_task(self, task_data: TaskBase) -> bool:
        """
        Cria uma tarefa no projeto alvo.
        Async port of V1 create_task logic.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # --- ETAPA 1: Criar a Tarefa ---
            endpoint = f"{self.api_url}/projects/{self.project_id}/tasks"
            
            # Saneamento (Logic Port)
            title = task_data.title
            if not title:
                title = "Sem título"
                
            description = task_data.description
            if not description:
                description = ""
                
            priority = task_data.priority
            # Logic.py had complex priority logic, but Pydantic handles int validation.
            
            payload = {
                "title": title.strip(),
                "description": description.strip(),
                "priority": priority
            }

            # Data de vencimento
            due_date = task_data.due_date
            if due_date:
                due_str = str(due_date).strip()
                if len(due_str) == 10:
                    due_str += "T23:59:59Z"
                elif " " in due_str and "T" not in due_str:
                    due_str = due_str.replace(" ", "T") + "Z"
                
                payload["due_date"] = due_str

            try:
                response = await client.put(endpoint, headers=self.headers, json=payload)
                
                if response.status_code not in [200, 201]:
                    print(f"Erro API (Etapa 1 - Criação): {response.status_code} - {response.text}")
                    return False
                
                new_task = response.json()
                task_id = new_task.get("id")
                
                if not task_id:
                    print(f"Erro: API não retornou ID para a tarefa '{payload['title']}'")
                    return False

                # --- ETAPA 2: Atribuir Responsável ---
                assignee_id = task_data.assignee_id
                
                # Se não tem ID mas tem nome, tenta resolver
                if not assignee_id and task_data.assignee_name:
                    assignee_id = await self._resolve_assignee(task_data.assignee_name)
                
                if assignee_id:
                    try:
                        aidInt = int(assignee_id)
                        assign_endpoint = f"{self.api_url}/tasks/{task_id}/assignees"
                        assign_payload = {"user_id": aidInt}
                        
                        assign_response = await client.put(assign_endpoint, headers=self.headers, json=assign_payload)
                        
                        if assign_response.status_code not in [200, 201]:
                            print(f"Aviso: Tarefa criada (ID: {task_id}), mas falha ao atribuir usuário {aidInt}.")
                            print(f"Erro API (Etapa 2): {assign_response.text}")
                    except Exception as e:
                        print(f"Falha ao tentar atribuir usuário: {e}")
                
                return True

            except Exception as e:
                print(f"Falha crítica no processamento: {e}")
                return False
