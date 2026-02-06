import requests
import json
import pandas as pd
from typing import List, Dict, Optional

class VikunjaClient:
    def __init__(self, api_url: str, token: str, project_id: str):
        self.api_url = api_url.rstrip("/")
        self.token = token
        self.project_id = project_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def fetch_users(self) -> List[Dict]:
        """Fetch users who have access to the target project, ensuring the owner is included."""
        users_dict = {}
        
        # 1. Obter usuário autenticado (Owner/Admin)
        try:
            user_response = requests.get(f"{self.api_url}/user", headers=self.headers)
            user_response.raise_for_status()
            current_user = user_response.json()
            users_dict[current_user['id']] = current_user
        except Exception as e:
            print(f"Erro ao buscar perfil do usuário: {e}")

        # 2. Obter membros do projeto
        try:
            endpoint = f"{self.api_url}/projects/{self.project_id}/users"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            project_users = response.json()
            for u in project_users:
                users_dict[u['id']] = u
        except Exception as e:
            print(f"Erro ao buscar usuários do projeto: {e}")
            
        return list(users_dict.values())

    def create_task(self, task_data: Dict) -> bool:
        """
        Cria uma tarefa no projeto alvo.
        Implementa um processo de duas etapas para garantir conformidade com a API.
        """
        # --- ETAPA 1: Criar a Tarefa ---
        endpoint = f"{self.api_url}/projects/{self.project_id}/tasks"
        
        # Saneamento rigoroso do payload base
        title = task_data.get("title")
        if not title or pd.isna(title):
            title = "Sem título"
            
        description = task_data.get("description")
        if not description or pd.isna(description):
            description = ""
            
        priority = task_data.get("priority")
        if not priority or pd.isna(priority):
            priority = 1 # Default para Low
        else:
            try:
                priority = int(priority)
                if priority < 1: priority = 1
            except:
                priority = 1

        payload = {
            "title": str(title).strip(),
            "description": str(description).strip(),
            "priority": priority
        }

        # Data de vencimento formatada (Vikunja exige RFC3339 pleno: YYYY-MM-DDTHH:MM:SSZ)
        due_date = task_data.get("due_date")
        if due_date and pd.notna(due_date):
            due_str = str(due_date).strip()
            # Se for apenas data YYYY-MM-DD, adiciona o componente de tempo
            if len(due_str) == 10:
                due_str += "T23:59:59Z"
            # Se estiver no formato YYYY-MM-DD HH:MM:SS, troca espaço por 'T' e adiciona 'Z'
            elif " " in due_str and "T" not in due_str:
                due_str = due_str.replace(" ", "T") + "Z"
            
            payload["due_date"] = due_str

        try:
            # DEBUG: Opcional para ver o que está saindo exatamente
            # print(f"DEBUG Payload: {json.dumps(payload)}")
            
            response = requests.put(endpoint, headers=self.headers, json=payload)
            
            if response.status_code not in [200, 201]:
                print(f"Erro API (Etapa 1 - Criação): {response.status_code} - {response.text}")
                response.raise_for_status()
            
            new_task = response.json()
            task_id = new_task.get("id")
            
            if not task_id:
                print(f"Erro: API não retornou ID para a tarefa '{payload['title']}'")
                return False

            # --- ETAPA 2: Atribuir Responsável ---
            assignee_id = task_data.get("assignee_id")
            if assignee_id and pd.notna(assignee_id):
                try:
                    aidInt = int(assignee_id)
                    assign_endpoint = f"{self.api_url}/tasks/{task_id}/assignees"
                    assign_payload = {"user_id": aidInt}
                    
                    assign_response = requests.put(assign_endpoint, headers=self.headers, json=assign_payload)
                    
                    if assign_response.status_code not in [200, 201]:
                        print(f"Aviso: Tarefa criada (ID: {task_id}), mas falha ao atribuir usuário {aidInt}.")
                        print(f"Erro API (Etapa 2): {assign_response.text}")
                except Exception as e:
                    print(f"Falha ao tentar atribuir usuário: {e}")
            
            return True

        except Exception as e:
            print(f"Falha crítica no processamento: {e}")
            return False
