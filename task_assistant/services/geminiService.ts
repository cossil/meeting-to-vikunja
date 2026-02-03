import { GoogleGenAI, Type, Modality } from "@google/genai";
import { TaskState, GeminiResponse, Assignee } from "../types";
import { SYSTEM_INSTRUCTION } from "../constants";

// Helper to encode audio blob to base64
const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64String = (reader.result as string).split(',')[1];
      resolve(base64String);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

// Helper to decode base64 to Uint8Array
const base64ToUint8Array = (base64: string): Uint8Array => {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
};

// Helper to write string to DataView
const writeString = (view: DataView, offset: number, string: string) => {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
};

// Helper to create WAV header
const createWavHeader = (dataLength: number, sampleRate: number): Uint8Array => {
  const buffer = new ArrayBuffer(44);
  const view = new DataView(buffer);

  // RIFF identifier
  writeString(view, 0, 'RIFF');
  // file length
  view.setUint32(4, 36 + dataLength, true);
  // RIFF type
  writeString(view, 8, 'WAVE');
  // format chunk identifier
  writeString(view, 12, 'fmt ');
  // format chunk length
  view.setUint32(16, 16, true);
  // sample format (raw)
  view.setUint16(20, 1, true);
  // channel count
  view.setUint16(22, 1, true);
  // sample rate
  view.setUint32(24, sampleRate, true);
  // byte rate (sample rate * block align)
  view.setUint32(28, sampleRate * 2, true);
  // block align (channel count * bytes per sample)
  view.setUint16(32, 2, true);
  // bits per sample
  view.setUint16(34, 16, true);
  // data chunk identifier
  writeString(view, 36, 'data');
  // data chunk length
  view.setUint32(40, dataLength, true);

  return new Uint8Array(buffer);
};

// Helper to convert base64 raw PCM to WAV Blob
const pcmBase64ToWavBlob = (base64: string, sampleRate: number = 24000): Blob => {
  const pcmData = base64ToUint8Array(base64);
  const header = createWavHeader(pcmData.length, sampleRate);
  const wavData = new Uint8Array(header.length + pcmData.length);
  wavData.set(header);
  wavData.set(pcmData, header.length);
  return new Blob([wavData], { type: 'audio/wav' });
};

// Helper to clean JSON string from Markdown code blocks
const cleanJsonString = (text: string): string => {
  let cleaned = text.trim();
  // Remove markdown code blocks if present
  if (cleaned.startsWith('```json')) {
    cleaned = cleaned.replace(/^```json\s*/, '').replace(/\s*```$/, '');
  } else if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```\s*/, '').replace(/\s*```$/, '');
  }
  return cleaned;
};

// Initialize Gemini Client
// NOTE: API Key must be in process.env.API_KEY
const getClient = () => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) throw new Error("API Key not found in environment variables");
  return new GoogleGenAI({ apiKey });
};

export const processUserAudioTurn = async (
  audioBlob: Blob,
  currentTask: TaskState
): Promise<GeminiResponse> => {
  const ai = getClient();
  const base64Audio = await blobToBase64(audioBlob);

  const model = "gemini-3-flash-preview";
  
  const currentDate = new Date().toLocaleDateString('pt-BR');
  const promptContext = `
    Data de hoje: ${currentDate}.
    Estado atual da Tarefa (JSON): ${JSON.stringify(currentTask)}.
    
    INSTRUÇÕES:
    1. Analise o áudio do usuário (em português).
    2. Atualize a "updatedTask". 
       - "title": MÁXIMO 6 PALAVRAS. Nunca repita palavras. NÃO USE CÓDIGOS TÉCNICOS.
       - "description": Resumo do contexto (Max 150 caracteres).
       - Se um campo não mudou, mantenha o valor anterior.
    3. Gere "replyText": Resposta curta (max 1 frase) na persona "Assistente de Tarefas".
    4. RETORNE APENAS JSON VÁLIDO.
  `;

  try {
    const response = await ai.models.generateContent({
      model: model,
      contents: {
        parts: [
          { text: promptContext },
          {
            inlineData: {
              mimeType: audioBlob.type || 'audio/wav',
              data: base64Audio
            }
          }
        ]
      },
      config: {
        // Increased to avoid truncation, relying on prompt to prevent loops
        maxOutputTokens: 1500, 
        temperature: 0.6,
        topP: 0.95,
        topK: 40,
        systemInstruction: SYSTEM_INSTRUCTION,
        responseMimeType: "application/json"
        // removed responseSchema to prevent validation truncation
      }
    });

    const text = response.text;
    if (!text) throw new Error("Empty response from Gemini");
    
    const cleanedText = cleanJsonString(text);
    
    try {
        const data = JSON.parse(cleanedText) as GeminiResponse;
        return data;
    } catch (parseError) {
        console.error("JSON Parse Error:", parseError, "Raw Text:", text);
        throw new Error("Invalid JSON received from Gemini");
    }

  } catch (error) {
    console.error("Gemini Interaction Error:", error);
    return {
      replyText: "Desculpe, tive um pequeno problema técnico. Pode repetir o que precisa?",
      updatedTask: currentTask
    };
  }
};

export const generateSpeech = async (text: string): Promise<string | null> => {
  const ai = getClient();
  
  const cleanText = text?.replace(/[\r\n]+/g, ' ').trim();
  if (!cleanText) return null;

  try {
    const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-tts",
        contents: {
            parts: [{ text: cleanText }]
        },
        config: {
            responseModalities: [Modality.AUDIO], 
            speechConfig: {
                voiceConfig: {
                    prebuiltVoiceConfig: { voiceName: "Puck" }
                }
            }
        }
    });

    const audioData = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (audioData) {
        const wavBlob = pcmBase64ToWavBlob(audioData, 24000);
        return URL.createObjectURL(wavBlob);
    }
    
    return null;

  } catch (error) {
    console.error("TTS Error:", error);
    return null;
  }
};