import os
import json
import base64
import wave
import io
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.task_processor import GlossaryManager
from pydantic import BaseModel, Field

# --- Pydantic Models for internal Logic ---

class ClarificationStrike(BaseModel):
    field: str
    count: int

class VoiceTaskState(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: str | None = Field(None, alias="dueDate")
    assignee: str | None = None
    status: str = "Em Progresso"
    missing_info: list[str] = Field(default_factory=lambda: ['title', 'description', 'dueDate', 'assignee'], alias="missingInfo")
    clarification_strikes: list[ClarificationStrike] = Field(default_factory=list, alias="clarificationStrikes")

class VoiceGeminiResponse(BaseModel):
    reply_text: str = Field(..., alias="replyText")
    updated_task: VoiceTaskState = Field(..., alias="updatedTask")


SYSTEM_INSTRUCTION = """
Você é o "Assistente de Tarefas". Sua missão é extrair informações de uma conversa para criar uma "Ficha de Tarefa".
Fale APENAS em Português do Brasil (pt-BR).

**Sua Persona:**
- Humilde, prestativo, ansioso para aprender.
- Use frases como "Desculpe, não entendi...", "Só para confirmar...", "Anotei aqui...".
- NUNCA diga apenas "OK". Sempre reflita o que entendeu.
- **Seja CONCISO. Use no máximo 2-3 frases curtas na resposta.**

**Regras de Negócio:**
1. **The Two-Strike Rule**: Se o usuário fornecer informações pouco claras sobre um campo específico duas vezes, pare de perguntar e marque o campo como "A Revisar".
2. **Escuta Reflexiva**: Resuma brevemente o que já foi coletado.
3. **Golden Record**: Colete: Título, Descrição, Data de Vencimento, Responsável.
4. **Glossário e Correção de Nomes**:
   Use as regras abaixo para identificar os nomes corretos dos responsáveis e termos técnicos:
   {glossary_rules}

**Saída JSON:**
Você deve retornar estritamente um JSON.

REGRAS ESTRITAS PARA PREVENIR ERROS DE REPETIÇÃO:
1. **NÃO** inclua explicações ou metadados nos valores.
2. **Título ("title")**:
   - MÁXIMO 6 PALAVRAS.
   - **PROIBIDO** repetir palavras consecutivas (Ex: "Rádio Rádio").
   - **PROIBIDO** gerar códigos ou sequências como "Ferbasa-BA-Ferbasa-BA".
   - Use APENAS linguagem natural simples.
   - Exemplo Bom: "Cotação de 10 Rádios".
3. **Descrição ("description")**: Resumo objetivo (Max 150 caracteres).

Formato esperado:
{
  "replyText": "Resposta curta aqui...",
  "updatedTask": {
    "title": "Titulo Curto",
    "description": "Descricao",
    "dueDate": "YYYY-MM-DD",
    "assignee": "Nome",
    "status": "Em Progresso",
    "missingInfo": ["campo1"],
    "clarificationStrikes": [{"field": "dueDate", "count": 1}]
  }
}
"""

class VoiceService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.glossary_manager = GlossaryManager()
        self.tts_model = "gemini-2.5-flash-preview-tts"
        # Using preview as per V1 logic
        self.nlu_model = "gemini-3-flash-preview" 

    def warmup_tts(self):
        """Sends a silent request to initialize the TTS model connection and ensures greeting exists."""
        print("🔥 Starting TTS Warmup...")
        try:
            # 1. Warmup Request
            self.client.models.generate_content(
                model=self.tts_model,
                contents="Warmup",
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.AUDIO],
                    speech_config=types.SpeechConfig(
                       voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Puck"
                            )
                        )
                    )
                )
            )
            print(f"✅ TTS Warmup Complete")

            # 2. Ensure Welcome File Exists
            if not os.path.exists("welcome_fixed.wav"):
                print("⚠️ Welcome file missing. Generating...")
                greeting_text = "Olá! Sou o assistente de tarefas do Vikunja. Como posso ajudar você hoje?"
                audio_bytes = self.generate_speech(greeting_text)
                if audio_bytes:
                    with open("welcome_fixed.wav", "wb") as f:
                        f.write(audio_bytes)
                    print("✅ Generated and saved welcome_fixed.wav")
                else:
                    print("❌ Failed to generate greeting audio")

        except Exception as e:
            print(f"⚠️ TTS Warmup Failed: {e}")

    @staticmethod
    def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
        """Wraps raw PCM data in a valid WAV header (16-bit, Mono)."""
        with io.BytesIO() as wav_io:
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)       # Mono
                wav_file.setsampwidth(2)       # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_bytes)
            return wav_io.getvalue()

    def generate_speech(self, text: str) -> Optional[bytes]:
        """Generates audio for the given text using Gemini TTS."""
        clean_text = text.replace('\n', ' ').strip()
        if not clean_text:
            return None
        
        try:
            response = self.client.models.generate_content(
                model=self.tts_model,
                contents=[types.Part(text=clean_text)],
                config=types.GenerateContentConfig(
                    response_modalities=[types.Modality.AUDIO],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Puck"
                            )
                        )
                    )
                )
            )
            
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                audio_bytes = part.inline_data.data
                # Convert PCM to WAV
                return self._pcm_to_wav(audio_bytes)
            
            return None

        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    async def process_turn(self, audio_bytes: Optional[bytes], current_state: Dict[str, Any], user_text: Optional[str] = None) -> Tuple[Dict[str, Any], Optional[bytes]]:
        """
        Process a single turn of conversation statelessly.
        
        Args:
            audio_bytes: The user's speech audio (optional).
            current_state: The current JSON state of the task being gathered.
            user_text: The user's text input (optional).
            
        Returns:
            Tuple of (updated_state_dict, reply_audio_wav_bytes)
        """
        current_date = datetime.now().strftime('%d/%m/%Y')
        glossary_rules = self.glossary_manager.get_prompt_rules()
        
        system_instruction_with_glossary = SYSTEM_INSTRUCTION.replace("{glossary_rules}", glossary_rules)

        prompt_context = f"""
            Data de hoje: {current_date}.
            Estado atual da Tarefa (JSON): {json.dumps(current_state)}.
            
            INSTRUÇÕES:
            1. Analise o áudio do usuário (em português).
            2. Atualize a "updatedTask". 
               - "title": MÁXIMO 6 PALAVRAS. Nunca repita palavras. NÃO USE CÓDIGOS TÉCNICOS.
               - "description": Resumo do contexto (Max 150 caracteres).
               - Se um campo não mudou, mantenha o valor anterior.
            3. Gere "replyText": Resposta curta (max 1 frase) na persona "Assistente de Tarefas".
            4. RETORNE APENAS JSON VÁLIDO.
        """

        try:
            # Prepare contents
            contents = [types.Part(text=prompt_context)]
            
            if user_text:
                contents.append(types.Part(text=f"Entrada de texto do usuário: {user_text}"))
            
            if audio_bytes:
                contents.append(types.Part(inline_data=types.Blob(data=audio_bytes, mime_type="audio/wav")))

            # Call Gemini with Input + Context
            response = self.client.models.generate_content(
                model=self.nlu_model,
                contents=contents,
                config=types.GenerateContentConfig(
                     max_output_tokens=1500,
                     temperature=0.6,
                     top_p=0.95,
                     top_k=40,
                     system_instruction=system_instruction_with_glossary,
                     response_mime_type="application/json",
                     response_schema=VoiceGeminiResponse
                )
            )
            
            if not response.parsed:
                raise ValueError("Gemini returned no parsed data.")
                
            parsed_response: VoiceGeminiResponse = response.parsed
            
            # Generate TTS for the reply
            reply_audio = self.generate_speech(parsed_response.reply_text)
            
            # Convert updated task to dict for return
            updated_state = parsed_response.updated_task.model_dump(by_alias=True)
            
            # Helper to attach reply text if needed by frontend (though audio is primary)
            updated_state['_reply_text'] = parsed_response.reply_text
            
            return updated_state, reply_audio

        except Exception as e:
            print(f"Gemini Interaction Error: {e}")
            # Fallback logic
            fallback_text = "Desculpe, tive um problema técnico. Pode repetir?"
            fallback_audio = self.generate_speech(fallback_text)
            return current_state, fallback_audio
