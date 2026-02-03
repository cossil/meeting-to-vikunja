import React, { useState, useEffect } from 'react';
import DraftBoard from './components/DraftBoard';
import ChatInterface from './components/ChatInterface';
import AudioRecorder from './components/AudioRecorder';
import { TaskState, ChatMessage } from './types';
import { INITIAL_TASK_STATE } from './constants';
import { processUserAudioTurn, generateSpeech } from './services/geminiService';

export default function App() {
  const [taskState, setTaskState] = useState<TaskState>(INITIAL_TASK_STATE);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);

  // Initial welcome message
  useEffect(() => {
    // Only check key on first render to show modal if needed (simulated check)
    // In a real scenario we rely on process.env or user input.
    // For this prototype, we assume process.env.API_KEY is available or we show a message.
    
    // Add welcome message
    const welcomeMsg: ChatMessage = {
        id: 'welcome',
        role: 'agent',
        text: 'Olá! Sou seu Assistente de Tarefas. Precisa abrir alguma tarefa para o Alexandre, Pedro ou Roquelina?',
        timestamp: Date.now()
    };
    setMessages([welcomeMsg]);
  }, []);

  const handleAudioRecorded = async (blob: Blob) => {
    // 1. Add User Message (placeholder for audio)
    const userMsgId = Date.now().toString();
    const userAudioUrl = URL.createObjectURL(blob);
    const userMsg: ChatMessage = {
        id: userMsgId,
        role: 'user',
        text: '🎤 [Mensagem de Voz]',
        audioUrl: userAudioUrl,
        timestamp: Date.now()
    };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
        // 2. Process with Gemini (Audio -> Text + JSON)
        const geminiResponse = await processUserAudioTurn(blob, taskState);
        
        // 3. Update Task State
        setTaskState(geminiResponse.updatedTask);

        // 4. Generate TTS for Agent Reply
        let agentAudioUrl: string | undefined = undefined;
        const ttsDataUrl = await generateSpeech(geminiResponse.replyText);
        if (ttsDataUrl) {
            agentAudioUrl = ttsDataUrl;
        }

        // 5. Add Agent Message
        const agentMsg: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: 'agent',
            text: geminiResponse.replyText,
            audioUrl: agentAudioUrl,
            timestamp: Date.now()
        };
        setMessages(prev => [...prev, agentMsg]);

        // Auto-play agent response (optional UX choice, keeping it manual for politeness unless desired)
        if (agentAudioUrl) {
           const audio = new Audio(agentAudioUrl);
           audio.play().catch(e => console.log("Autoplay blocked:", e));
        }

    } catch (err) {
        console.error("Pipeline Error:", err);
        const errorMsg: ChatMessage = {
            id: Date.now().toString(),
            role: 'agent',
            text: 'Desculpe, tive um problema ao processar. Podemos tentar de novo?',
            timestamp: Date.now()
        };
        setMessages(prev => [...prev, errorMsg]);
    } finally {
        setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 relative">
      
      {/* Mobile Sidebar Toggle (Simplified for prototype: Sidebar is always visible on desktop) */}
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center px-6 justify-between flex-shrink-0 z-10">
            <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                <span className="text-2xl">🎓</span>
                Assistente de Tarefas
            </h1>
            <div className="text-xs text-slate-400 hidden sm:block">
                Powered by Gemini 2.5 Flash
            </div>
        </header>

        <ChatInterface messages={messages} isProcessing={isProcessing} />
        
        <div className="flex-shrink-0">
            <AudioRecorder onAudioRecorded={handleAudioRecorded} disabled={isProcessing} />
        </div>
      </div>

      {/* Sidebar - Hidden on small mobile, visible on md+ */}
      <div className="hidden md:block h-full">
        <DraftBoard task={taskState} />
      </div>

    </div>
  );
}