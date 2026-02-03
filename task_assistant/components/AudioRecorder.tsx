import React, { useState, useRef, useEffect } from 'react';

interface AudioRecorderProps {
  onAudioRecorded: (blob: Blob) => void;
  disabled: boolean;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onAudioRecorded, disabled }) => {
  const [isRecording, setIsRecording] = useState(false);
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
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        onAudioRecorded(blob);
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
      alert("Não foi possível acessar o microfone.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="flex justify-center items-center w-full p-4 bg-white border-t border-slate-200">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        className={`
            relative flex items-center justify-center w-16 h-16 rounded-full transition-all duration-300 shadow-lg
            ${disabled ? 'bg-slate-300 cursor-not-allowed' : isRecording ? 'bg-red-500 hover:bg-red-600 scale-110' : 'bg-indigo-600 hover:bg-indigo-700'}
        `}
      >
        {isRecording ? (
            <div className="w-6 h-6 bg-white rounded-sm animate-pulse" />
        ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
        )}
        
        {/* Recording Ring Animation */}
        {isRecording && (
             <span className="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75 animate-ping"></span>
        )}
      </button>
      
      <span className={`absolute mt-24 text-sm font-medium ${isRecording ? 'text-red-500 animate-pulse' : 'text-slate-400'}`}>
        {isRecording ? 'Gravando...' : 'Toque para falar'}
      </span>
    </div>
  );
};

export default AudioRecorder;
