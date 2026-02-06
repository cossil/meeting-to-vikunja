import client from './client';
import type { VoiceState, VoiceTurnResponse } from '../types/schema';

export const voiceApi = {
    warmup: async (): Promise<void> => {
        await client.get('/voice/warmup');
    },

    getGreeting: async (): Promise<string> => {
        const response = await client.get('/voice/greeting', {
            responseType: 'blob',
        });
        return URL.createObjectURL(response.data);
    },

    sendTurn: async (audioBlob: Blob, currentState: VoiceState): Promise<{ updatedState: VoiceState; audioUrl: string }> => {
        const formData = new FormData();
        formData.append('file', audioBlob, 'input.wav');
        formData.append('state', JSON.stringify(currentState));

        const response = await client.post<VoiceTurnResponse>('/voice/turn', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        // Convert Base64 reply to Blob URL
        const byteCharacters = atob(response.data.reply_audio);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const audioUrl = URL.createObjectURL(new Blob([byteArray], { type: 'audio/wav' }));

        return {
            updatedState: response.data.updated_state,
            audioUrl,
        };
    },

    sendTextTurn: async (text: string, currentState: VoiceState): Promise<{ updatedState: VoiceState; audioUrl: string }> => {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('state', JSON.stringify(currentState));

        const response = await client.post<VoiceTurnResponse>('/voice/turn', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });

        // Convert Base64 reply to Blob URL
        const byteCharacters = atob(response.data.reply_audio);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const audioUrl = URL.createObjectURL(new Blob([byteArray], { type: 'audio/wav' }));

        return {
            updatedState: response.data.updated_state,
            audioUrl,
        };
    },
};
