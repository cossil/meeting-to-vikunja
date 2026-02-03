import React, { useEffect, useRef } from 'react';
import { ChatMessage } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isProcessing: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, isProcessing }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isProcessing]);

  return (
    <div className="flex-1 relative bg-slate-100 overflow-hidden flex flex-col">
      <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        
        {isProcessing && (
          <div className="flex justify-start animate-fade-in">
             <div className="bg-white p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center space-x-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};

const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isAgent = message.role === 'agent';
  const audioRef = useRef<HTMLAudioElement>(null);

  const playAudio = () => {
    if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play();
    }
  };

  return (
    <div className={`flex w-full ${isAgent ? 'justify-start' : 'justify-end'}`}>
      <div className={`max-w-[85%] md:max-w-[70%] flex gap-3 ${isAgent ? 'flex-row' : 'flex-row-reverse'}`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
            isAgent ? 'bg-indigo-600 text-white' : 'bg-slate-400 text-white'
        }`}>
            {isAgent ? 'AT' : 'VC'}
        </div>

        {/* Bubble */}
        <div className={`
            p-4 rounded-2xl shadow-sm text-sm leading-relaxed
            ${isAgent ? 'bg-white text-slate-800 rounded-tl-none' : 'bg-indigo-600 text-white rounded-tr-none'}
        `}>
           <p>{message.text}</p>
           
           {/* Audio Player Controls */}
           {message.audioUrl && (
             <div className="mt-3 pt-3 border-t border-opacity-10 border-black flex items-center gap-2">
                <button 
                    onClick={playAudio}
                    className={`flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded transition-colors ${
                        isAgent ? 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100' : 'bg-indigo-700 text-white hover:bg-indigo-800'
                    }`}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                    Reproduzir Áudio
                </button>
                <audio ref={audioRef} src={message.audioUrl} className="hidden" />
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;