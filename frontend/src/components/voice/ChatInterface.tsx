
import { useEffect, useRef } from 'react';
import { useVoiceStore } from '../../store/useVoiceStore';
import { ScrollArea } from '../ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { cn } from '../../lib/utils';
import { Bot, User, Volume2 } from 'lucide-react';

export function ChatInterface() {
    const { messages, playAudio } = useVoiceStore();
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    return (
        <ScrollArea className="flex-1 p-6">
            <div className="flex flex-col gap-6">
                <div className="flex justify-center">
                    <span className="text-xs font-medium text-gray-400 dark:text-gray-500 bg-gray-50 dark:bg-gray-800 px-3 py-1 rounded-full">
                        Hoje
                    </span>
                </div>

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            "flex items-end gap-3 max-w-[80%]",
                            msg.role === 'user' ? "self-end flex-row-reverse" : "self-start"
                        )}
                    >
                        <Avatar className="w-8 h-8 shrink-0">
                            {msg.role === 'agent' ? (
                                <>
                                    <AvatarImage src="https://ui-avatars.com/api/?name=Vikunja+Bot&background=e5e7eb&color=374151" />
                                    <AvatarFallback><Bot className="w-4 h-4" /></AvatarFallback>
                                </>
                            ) : (
                                <>
                                    <AvatarImage src="https://github.com/shadcn.png" />
                                    <AvatarFallback><User className="w-4 h-4" /></AvatarFallback>
                                </>
                            )}
                        </Avatar>

                        <div className="flex flex-col gap-1">
                            <span className={cn(
                                "text-xs font-semibold",
                                msg.role === 'user' ? "text-right" : "text-left"
                            )}>
                                {msg.role === 'user' ? "Você" : "Vikunja Bot"}
                            </span>

                            <div className={cn(
                                "p-4 rounded-2xl shadow-sm text-sm leading-relaxed relative group",
                                msg.role === 'user'
                                    ? "bg-primary text-primary-foreground rounded-br-sm"
                                    : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm"
                            )}>
                                {msg.content || (msg.audioUrl ? "Mensagem de Áudio" : "...")}

                                {msg.audioUrl && (
                                    <button
                                        onClick={() => playAudio(msg.audioUrl!)}
                                        className="absolute -right-10 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
                                    >
                                        <Volume2 className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {/* Invisible ref for scrolling */}
                <div ref={scrollRef} />
            </div>
        </ScrollArea>
    );
}
