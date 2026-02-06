import { useRef } from 'react';
import { useVoiceStore } from '../../store/useVoiceStore';
import { Button } from '../ui/button';
import { Mic, Square } from 'lucide-react';
import { cn } from '../../lib/utils';

export function AudioRecorder() {
    const { isRecording, setIsRecording, processUserAudio, isProcessing, isPlaying } = useVoiceStore();
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

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Error accessing microphone:", err);
            // Handle error state in store if needed
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    return (
        <div className="flex justify-center p-4 bg-muted/20 border-t">
            <Button
                size="lg"
                variant={isRecording ? "destructive" : "default"}
                className={cn(
                    "rounded-full w-16 h-16 shadow-lg transition-all transform hover:scale-105",
                    isRecording && "animate-pulse ring-4 ring-destructive/30"
                )}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing || isPlaying}
            >
                {isRecording ? (
                    <Square className="w-8 h-8 fill-current" />
                ) : (
                    <Mic className="w-8 h-8" />
                )}
            </Button>
            {isProcessing && (
                <span className="absolute mt-16 text-xs text-muted-foreground animate-pulse">Processing...</span>
            )}
        </div>
    );
}
