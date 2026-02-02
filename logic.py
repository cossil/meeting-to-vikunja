import os
import requests
import pandas as pd
from typing import List, Dict, Optional, Any
from thefuzz import process
from google import genai
from google.genai import types
from dotenv import load_dotenv
import docx
from datetime import datetime

load_dotenv()

class VikunjaClient:
    def __init__(self):
        self.api_url = os.getenv("VIKUNJA_API_URL", "").rstrip("/")
        self.token = os.getenv("VIKUNJA_API_TOKEN")
        self.project_id = os.getenv("TARGET_PROJECT_ID", "2")
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

import json

class GlossaryManager:
    """Gerencia o glossário de termos para correção de STT."""
    def __init__(self, file_path: str = "glossary.json"):
        self.file_path = file_path
        self.seed_data = {
            "Hankell": ["Rankel", "Ranquel", "Hanke", "Rank", "Hankel", "Hanquel"],
            "Cenize": ["Senize", "Semize", "Zenize"],
            "Roquelina": ["Rock", "Roque", "Roc", "Hock"],
            "APN": ["PN", "A pena", "Apn", "A.P.N."],
            "Intelbras": ["Inteoubras", "Intel", "Inteobras"],
            "Datatem": ["Data tem", "Dataten", "Data ten"],
            "Odoo": ["Odo", "Hoodoo", "Odum"]
        }
        if not os.path.exists(self.file_path):
            self.save(self.seed_data)

    def load(self) -> Dict:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar glossário: {e}")
            return self.seed_data

    def save(self, data: Dict):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar glossário: {e}")

    def get_prompt_rules(self) -> str:
        data = self.load()
        rules = []
        for correct, variations in data.items():
            vars_str = ", ".join(variations)
            rules.append(f"- Se ouvir: {vars_str} -> Escreva: {correct}")
        return "\n".join(rules)

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-3-flash-preview" # Otimizado para STT robusto

    def analyze_meeting_notes(self, text: str, meeting_date: datetime, custom_instructions: str = "") -> List[Dict]:
        """Extract tasks from meeting notes using Gemini, consolidating multiple contexts."""
        
        # Get dynamic rules from Glossary
        glossary_rules = GlossaryManager().get_prompt_rules()

        prompt = f"""Você é um Analista Sênior de Projetos e Atas.
        Sua missão é transformar uma transcrição crua (que pode ser a união de vários arquivos de áudio contendo erros de digitação, gírias e conversas paralelas) em tarefas profissionais e acionáveis.

        CONTEXTO DE ENTRADA:
        1. Data da Reunião: {meeting_date.strftime('%d/%m/%Y (%A)')}
        2. Instruções do Usuário: "{custom_instructions}"
        3. Origem: Consolidação de segmentos da MESMA reunião.

        DIRETRIZES DE PROCESSAMENTO (PRIORIDADE MÁXIMA = EXAUSTIVIDADE):
        1. FILTRO DE RUÍDO: Identifique e exclua agressivamente vícios de linguagem ("né", "aham" , "sim mas"), conversas pessoais (almoço, banheiro, família, filhos, clima), pensamentos incompletos e digressões irrelevantes.
        2. NORMALIZAÇÃO 1: Corrija a gramática do STT. Transforme "eu vô vê isso" em "Analisar tópico X" ou "eu vô enviá o e-mail" em "Enviar e-mail".
        3. NORMALIZAÇÃO 2: Use as regras do glossário abaixo para corrigir nomes e termos técnicos:
        {glossary_rules}

        4. TAREFAS IMPLÍCITAS: Identifique compromissos ocultos (Ex: "Deixa que eu vejo isso" -> Tarefa: "Analisar tópico X").
        5. EXAUSTIVIDADE (CRÍTICO): Não deixe NENHUMA tarefa para trás. Se um assunto foi discutido e gerou uma ação, ele DEVE virar uma tarefa, mesmo que pareça menor. É melhor pecar pelo excesso do que pela falta.
        6. CONSOLIDAÇÃO INTELIGENTE: Identifique itens sobrepostos, e apenas unifique tarefas se elas forem ESTRITAMENTE sobre a mesma entrega.
        7. CONTINUIDADE: Trate o texto como um fluxo contínuo. Mesmo se o texto mudar de assunto bruscamente, continue a análise lógica.

        FORMATO DE SAÍDA (JSON):
        - title (string): Verbo + Objeto (Use termos corrigidos).
        - description (string): Contexto completo (Use termos corrigidos).
        - assignee_name (string): Nome corrigido.
        - priority (int): 1-5.
        - due_date (string): YYYY-MM-DD ou null.

        TRANSCRICÃO:
        ---
        {text}
        ---
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Erro na análise do Gemini: {e}")
            return []

class TaskProcessor:
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".docx":
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimation of token count (approx 4 chars/token)."""
        return len(text) // 4

    @staticmethod
    def match_assignee(name: str, users: List[Dict], threshold: int = 80) -> Optional[int]:
        if not name or not users:
            return None
        
        # users format: [{"id": 1, "name": "User Name", "username": "user"}, ...]
        user_names = [u.get("name") or u.get("username") for u in users]
        matches = process.extractOne(name, user_names)
        
        if matches and matches[1] > threshold:
            matched_name = matches[0]
            for u in users:
                if u.get("name") == matched_name or u.get("username") == matched_name:
                    return u.get("id")
        return None
