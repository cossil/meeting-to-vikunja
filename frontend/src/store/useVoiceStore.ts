import { create } from 'zustand';
import { voiceApi } from '../api/voice';
import type { VoiceState } from '../types/schema';

interface Message {
    role: 'user' | 'agent';
    content: string | null; // Text transcript if available, or just placeholder
    audioUrl?: string; // For playback history
}

interface VoiceStoreState {
    isRecording: boolean;
    isProcessing: boolean;
    isPlaying: boolean;
    messages: Message[];
    currentTask: VoiceState;
    error: string | null;

    // Actions
    setIsRecording: (isRecording: boolean) => void;
    initSession: () => Promise<void>;
    processUserAudio: (audioBlob: Blob) => Promise<void>;
    sendTextMessage: (text: string) => Promise<void>;
    playAudio: (url: string) => Promise<void>;
    reset: () => void;
    updateCurrentTask: (updates: Partial<VoiceState>) => void;
    resetCurrentTask: () => void;
    syncToVikunja: () => Promise<void>;
}

const INITIAL_TASK_STATE: VoiceState = {
    title: null,
    description: null,
    dueDate: null,
    assignee: null,
    status: 'draft',
    priority: 3
};

export const useVoiceStore = create<VoiceStoreState>((set, get) => ({
    isRecording: false,
    isProcessing: false,
    isPlaying: false,
    messages: [],
    currentTask: INITIAL_TASK_STATE,
    error: null,

    setIsRecording: (isRecording) => set({ isRecording }),

    playAudio: async (url: string) => {
        set({ isPlaying: true });
        const audio = new Audio(url);

        audio.onended = () => {
            set({ isPlaying: false });
        };

        audio.onerror = () => {
            set({ isPlaying: false, error: "Failed to play audio" });
        };

        try {
            await audio.play();
        } catch (e) {
            console.error("Audio playback failed", e);
            set({ isPlaying: false });
        }
    },

    initSession: async () => {
        set({ isProcessing: true, error: null, messages: [] });
        try {
            await voiceApi.warmup();
            const greetingUrl = await voiceApi.getGreeting();

            set((state) => ({
                messages: [...state.messages, { role: 'agent', content: "Olá! Sou o assistente de tarefas do Vikunja. Como posso ajudar você hoje?", audioUrl: greetingUrl }],
                isProcessing: false
            }));

            await get().playAudio(greetingUrl);

        } catch (err: any) {
            set({ error: err.message || "Failed to initialize voice session", isProcessing: false });
        }
    },

    processUserAudio: async (audioBlob: Blob) => {
        set({ isProcessing: true, error: null });
        const { currentTask } = get();

        // Add user turn placeholder (we don't have transcript yet immediately, typically)
        const userAudioUrl = URL.createObjectURL(audioBlob);
        set((state) => ({
            messages: [...state.messages, { role: 'user', content: "Audio Input", audioUrl: userAudioUrl }]
        }));

        try {
            const { updatedState, audioUrl } = await voiceApi.sendTurn(audioBlob, currentTask);

            set((state) => ({
                currentTask: updatedState,
                messages: [...state.messages, { role: 'agent', content: "Response", audioUrl }],
                isProcessing: false
            }));

            await get().playAudio(audioUrl);

        } catch (err: any) {
            set({ error: err.message || "Failed to process audio", isProcessing: false });
        }
    },

    sendTextMessage: async (text: string) => {
        if (!text.trim()) return;
        set({ isProcessing: true, error: null });
        const { currentTask } = get();

        // Add user text message
        set((state) => ({
            messages: [...state.messages, { role: 'user', content: text }]
        }));

        try {
            const { updatedState, audioUrl } = await voiceApi.sendTextTurn(text, currentTask);

            set((state) => ({
                currentTask: updatedState,
                messages: [...state.messages, { role: 'agent', content: updatedState._reply_text || "Response", audioUrl }],
                isProcessing: false
            }));

            await get().playAudio(audioUrl);

        } catch (err: any) {
            set({ error: err.message || "Failed to process message", isProcessing: false });
        }
    },



    resetCurrentTask: () => {
        set({ currentTask: INITIAL_TASK_STATE });
    },

    updateCurrentTask: (updates) => {
        set((state) => ({
            currentTask: { ...state.currentTask, ...updates }
        }));
    },

    syncToVikunja: async () => {
        const { currentTask } = get();
        if (!currentTask.title) return;

        set({ isProcessing: true, error: null });
        try {
            // Map VoiceState to Task schema for the API
            const taskToSync = {
                title: currentTask.title,
                description: currentTask.description,
                assignee_name: currentTask.assignee,
                assignee_id: null, // Let backend resolve
                priority: currentTask.priority || 3,
                due_date: currentTask.dueDate
            };

            const { batchApi } = await import('../api/batch');
            const result = await batchApi.syncTasks([taskToSync]);

            if (result.success > 0) {
                set({
                    isProcessing: false,
                    messages: [...get().messages, { role: 'agent', content: "Tarefa enviada com sucesso para o Vikunja!" }]
                });
                get().resetCurrentTask();
            } else {
                throw new Error(result.details[0]?.error || "Erro ao sincronizar");
            }

        } catch (err: any) {
            set({ error: err.message || "Falha ao sincronizar", isProcessing: false });
        }
    },

    reset: () => {
        set({
            isRecording: false,
            isProcessing: false,
            isPlaying: false,
            messages: [],
            currentTask: INITIAL_TASK_STATE,
            error: null
        });
    }
}));
