
import os
import json
import base64
import wave
import io
import time
from datetime import datetime
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from logic import GlossaryManager
from dotenv import load_dotenv

load_dotenv()

# Ported from constants.ts with modification for dynamic glossary
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

class BenchmarkLogger:
    def __init__(self, filepath="latency_logs.jsonl"):
        self.filepath = filepath

    def log(self, event_type: str, duration_ms: float, details: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "duration_ms": round(duration_ms, 2),
            **(details or {})
        }
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

class VoiceAgentService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API Key not found in environment variables")
        self.client = genai.Client(api_key=api_key)
        self.glossary_manager = GlossaryManager()
        self.logger = BenchmarkLogger()

    def warmup_tts(self):
        """Sends a silent request to initialize the TTS model connection."""
        print("🔥 Starting TTS Warmup...")
        try:
            start = time.time()
            # Send a short valid word to wake up the model (avoiding 500 errors on empty/symbol inputs)
            self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents="Oi",
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
            duration = (time.time() - start) * 1000
            print(f"✅ TTS Warmup Complete in {duration:.2f}ms")
            self.logger.log("TTS Warmup", duration, {"status": "success"})
        except Exception as e:
            print(f"⚠️ TTS Warmup Failed: {e}")
            self.logger.log("TTS Warmup", 0, {"status": "failed", "error": str(e)})

    def process_audio_turn(self, audio_bytes: bytes, current_task: dict, model_name: str = "gemini-3-flash-preview") -> VoiceGeminiResponse:
        start_time = time.time()
        current_date = datetime.now().strftime('%d/%m/%Y')
        glossary_rules = self.glossary_manager.get_prompt_rules()
        
        # Inject glossary rules into system instruction
        system_instruction_with_glossary = SYSTEM_INSTRUCTION.replace("{glossary_rules}", glossary_rules)

        prompt_context = f"""
            Data de hoje: {current_date}.
            Estado atual da Tarefa (JSON): {json.dumps(current_task)}.
            
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
            # We need to encode bytes to base64 string for the API if passing as inline data
            # However, google-genai client handles bytes if we pass it correctly or as Part.
            # Using inline data with base64 string is the safest mirror of the TS implementation.
            b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            
            gemini_start = time.time()
            response = self.client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part(text=prompt_context),
                    types.Part(inline_data=types.Blob(data=audio_bytes, mime_type="audio/wav"))
                ],
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
            gemini_duration = (time.time() - gemini_start) * 1000
            self.logger.log("Gemini Logic Processing", gemini_duration, {"model": model_name, "input_type": "audio"})

            if response.parsed:
                total_duration = (time.time() - start_time) * 1000
                self.logger.log("Total Turn Time", total_duration, {"step": "process_audio_turn"})
                return response.parsed
            else:
                 raise ValueError("Gemini returned no parsed data.")

        except Exception as e:
            print(f"Gemini Interaction Error: {e}")
            # Return a fallback response so the UI doesn't crash
            return VoiceGeminiResponse(
                replyText="Desculpe, tive um pequeno problema técnico. Pode repetir o que precisa?",
                updatedTask=VoiceTaskState(**current_task)
            )

    def process_text_turn(self, text: str, current_task: dict, model_name: str = "gemini-3-flash-preview") -> VoiceGeminiResponse:
        start_time = time.time()
        current_date = datetime.now().strftime('%d/%m/%Y')
        glossary_rules = self.glossary_manager.get_prompt_rules()
        
        system_instruction_with_glossary = SYSTEM_INSTRUCTION.replace("{glossary_rules}", glossary_rules)

        prompt_context = f"""
            Data de hoje: {current_date}.
            Estado atual da Tarefa (JSON): {json.dumps(current_task)}.
            
            INSTRUÇÕES:
            1. Analise o TEXTO do usuário (em português): "{text}"
            2. Atualize a "updatedTask". 
               - "title": MÁXIMO 6 PALAVRAS. Nunca repita palavras. NÃO USE CÓDIGOS TÉCNICOS.
               - "description": Resumo do contexto (Max 150 caracteres).
               - Se um campo não mudou, mantenha o valor anterior.
            3. Gere "replyText": Resposta curta (max 1 frase) na persona "Assistente de Tarefas".
            4. RETORNE APENAS JSON VÁLIDO.
        """

        try:
            gemini_start = time.time()
            response = self.client.models.generate_content(
                model=model_name,
                contents=[types.Part(text=prompt_context)],
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
            gemini_duration = (time.time() - gemini_start) * 1000
            self.logger.log("Gemini Logic Processing", gemini_duration, {"model": model_name, "input_type": "text"})

            if response.parsed:
                total_duration = (time.time() - start_time) * 1000
                self.logger.log("Total Turn Time", total_duration, {"step": "process_text_turn"})
                return response.parsed
            else:
                 raise ValueError("Gemini returned no parsed data.")

        except Exception as e:
            print(f"Gemini Interaction Error: {e}")
            return VoiceGeminiResponse(
                replyText="Desculpe, tive um pequeno problema técnico. Pode repetir o que precisa?",
                updatedTask=VoiceTaskState(**current_task)
            )

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
            
    def generate_speech(self, text: str) -> bytes | None:
        clean_text = text.replace('\n', ' ').strip()
        if not clean_text:
            return None
        
        print(f"🎤 TTS Request: '{clean_text[:20]}...'")

        try:
            tts_start = time.time()
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
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
            
            # The python SDK returns audio in parts
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                # print(f"🔊 TTS Response Parts: {len(response.candidates[0].content.parts)}")
                audio_bytes = part.inline_data.data
                # print(f"✅ TTS Audio Bytes: {len(audio_bytes)}")
                
                # Wrap PCM in WAV container
                wav_bytes = self._pcm_to_wav(audio_bytes)
                # print(f"📦 WAV Container Bytes: {len(wav_bytes)}")
                
                tts_duration = (time.time() - tts_start) * 1000
                self.logger.log("TTS Generation", tts_duration, {"char_count": len(clean_text)})

                return wav_bytes # WAV formatted bytes
            
            print("⚠️ TTS Response had no parts")
            return None

        except Exception as e:
            print(f"TTS Error: {e}")
            return None
