import json
from datetime import datetime
from typing import List, Dict, Any
from google import genai
from google.genai import types
from app.services.glossary_manager import GlossaryManager

class GeminiService:
    def __init__(self, glossary_manager: GlossaryManager, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-3-flash-preview" # Otimizado para STT robusto
        self.glossary_manager = glossary_manager

    def analyze_meeting_notes(self, text: str, meeting_date: datetime, custom_instructions: str = "") -> List[Dict]:
        """Extract tasks from meeting notes using Gemini, consolidating multiple contexts."""
        
        # Get dynamic rules from Glossary
        glossary_rules = self.glossary_manager.get_prompt_rules()

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
