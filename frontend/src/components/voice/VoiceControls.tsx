import { useState, useRef } from 'react';
import { useVoiceStore } from '../../store/useVoiceStore';
import { Button } from '../ui/button';
import { Mic, Square, AudioWaveform, Send } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Input } from '../ui/input';

export function VoiceControls() {
    const { isRecording, setIsRecording, processUserAudio, sendTextMessage, isProcessing, isPlaying } = useVoiceStore();
    const [inputValue, setInputValue] = useState('');
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
                processUserAudio(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Error accessing microphone:", err);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const handleSend = () => {
        if (inputValue.trim()) {
            sendTextMessage(inputValue);
            setInputValue('');
        }
    };

    return (
        <div className="p-6 border-t border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-950/95 backdrop-blur-sm z-10">
            <div className="flex flex-col items-center gap-4">
                {/* Text Fallback */}
                <div className="w-full relative">
                    <Input
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Digite uma mensagem..."
                        className="pl-4 pr-12 py-6 rounded-xl bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700"
                        disabled={isRecording}
                    />
                    <Button
                        size="icon"
                        variant="ghost"
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary"
                        onClick={handleSend}
                    >
                        <Send className="w-5 h-5" />
                    </Button>
                </div>

                {/* Mic Button */}
                <div className="relative group cursor-pointer">
                    {isRecording && (
                        <div className="absolute inset-0 bg-red-500/20 rounded-full animate-ping" />
                    )}
                    <Button
                        size="lg"
                        variant="ghost"
                        className={cn(
                            "relative flex items-center justify-center w-16 h-16 rounded-full shadow-lg transition-all hover:scale-105",
                            isRecording ? "!bg-red-500 hover:!bg-red-600 animate-pulse" : "!bg-red-500 hover:!bg-red-600"
                        )}
                        onClick={isRecording ? stopRecording : startRecording}
                        disabled={isProcessing || isPlaying}
                    >
                        {isRecording ? (
                            <Square className="w-8 h-8 fill-white text-white" />
                        ) : (
                            <Mic className="w-8 h-8 text-white" />
                        )}
                    </Button>
                </div>

                <p className="text-xs text-gray-400 font-medium h-4">
                    {isRecording ? "Ouvindo..." : isProcessing ? "Processando..." : "Toque para falar"}
                </p>
            </div>
        </div>
    );
}
