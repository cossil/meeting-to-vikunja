import os
import json
import docx
import shutil
import time
from typing import List, Dict, Optional, Any
from datetime import datetime
from google import genai
from google.genai import types
from thefuzz import process
from fastapi import UploadFile
from app.core.config import settings
from app.models.schemas import AnalysisResponse, TaskBase

class GlossaryManager:
    """Gerencia o glossário de termos para correção de STT."""
    def __init__(self, file_path: str = "data/glossary.json"):
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
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
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

def get_system_prompt(meeting_date_str: str, custom_instructions: str, glossary_rules: str) -> str:
    return f"""Você é um Analista Sênior de Projetos e Atas.
        Sua missão é transformar uma transcrição crua (que pode ser a união de vários arquivos de áudio contendo erros de digitação, gírias e conversas paralelas) em tarefas profissionais e acionáveis.

        CONTEXTO DE ENTRADA:
        1. Data da Reunião: {meeting_date_str}
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
        """

class TaskProcessor:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-3-flash-preview"
        self.glossary_manager = GlossaryManager()

    async def extract_text_from_upload(self, file: UploadFile) -> str:
        ext = os.path.splitext(file.filename)[1].lower()
        
        # Save temp file to read
        temp_path = f"temp_{int(time.time())}_{file.filename}"
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            text = ""
            if ext == ".docx":
                doc = docx.Document(temp_path)
                text = "\n".join([p.text for p in doc.paragraphs])
            elif ext in [".txt", ".md"]:
                with open(temp_path, "r", encoding="utf-8") as f:
                    text = f.read()
            return text
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimation of token count (approx 4 chars/token)."""
        return len(text) // 4

    async def process_file(self, file: UploadFile, meeting_date: datetime = datetime.now(), custom_instructions: str = "") -> AnalysisResponse:
        start_time = time.time()
        text = await self.extract_text_from_upload(file)
        
        glossary_rules = self.glossary_manager.get_prompt_rules()
        meeting_date_str = meeting_date.strftime('%d/%m/%Y (%A)')
        
        system_instructions = get_system_prompt(meeting_date_str, custom_instructions, glossary_rules)
        
        prompt = f"""
        {system_instructions}

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
            data = json.loads(response.text)
            
            # Ensure data is a list
            if not isinstance(data, list):
                if isinstance(data, dict):
                     # Handle case where LLM might return a wrapper object
                     data = data.get('tasks', [data])
                else:
                    data = []

            tasks = []
            for item in data:
                try:
                    tasks.append(TaskBase(**item))
                except Exception as e:
                    print(f"Skipping invalid task: {item} - {e}")
            
            processing_time = time.time() - start_time
            return AnalysisResponse(
                tasks=tasks,
                token_count=self.estimate_tokens(text),
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"Erro na análise do Gemini: {e}")
            raise e
