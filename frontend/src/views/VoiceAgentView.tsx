
import { useEffect, useRef } from 'react';
import { Layout } from '../components/layout/Layout';
import { ChatInterface } from '../components/voice/ChatInterface';
import { VoiceControls } from '../components/voice/VoiceControls';
import { TaskDraftCard } from '../components/voice/TaskDraftCard';
import { useVoiceStore } from '../store/useVoiceStore';
import { AudioWaveform } from 'lucide-react';
import { Button } from '../components/ui/button';

export function VoiceAgentView() {
    const { initSession } = useVoiceStore();
    const hasInitialized = useRef(false);

    useEffect(() => {
        // Initialize session (warmup, load greeting) on mount
        if (!hasInitialized.current) {
            initSession();
            hasInitialized.current = true;
        }
    }, [initSession]);

    return (
        <Layout>
            <div className="flex h-full overflow-hidden">
                {/* Left Panel: Conversation & Controls */}
                <section className="flex-1 flex flex-col min-w-[400px] border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 relative">
                    {/* Header */}
                    <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center shrink-0">
                        <h3 className="text-lg font-bold tracking-tight">Conversa</h3>
                        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-full p-1 pl-3 pr-1">
                            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Padrão (Ativo)</span>
                            <Button
                                variant="secondary"
                                size="sm"
                                className="h-7 rounded-full text-xs font-bold gap-1 shadow-sm opacity-50 cursor-not-allowed"
                            >
                                <AudioWaveform className="w-3 h-3" /> Tempo Real (Em Breve)
                            </Button>
                        </div>
                    </div>

                    {/* Chat Area */}
                    <ChatInterface />

                    {/* Controls */}
                    <VoiceControls />
                </section>

                {/* Right Panel: Live Draft */}
                <TaskDraftCard />
            </div>
        </Layout>
    );
}
