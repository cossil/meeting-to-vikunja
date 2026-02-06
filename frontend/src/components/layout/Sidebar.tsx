
import { Link, useLocation } from 'react-router-dom';
import { cn } from "@/lib/utils";
import {
    CloudUpload,
    Mic,
    Settings,
    Wand2
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function Sidebar() {
    const location = useLocation();

    const isActive = (path: string) => location.pathname === path;

    return (
        <aside className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col justify-between shrink-0 h-screen transition-all duration-300 ease-in-out">
            <div>
                <div className="h-16 flex items-center px-6 border-b border-gray-100 dark:border-gray-800">
                    <div className="flex items-center gap-3">
                        <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                            <Wand2 className="h-5 w-5" />
                        </div>
                        <span className="font-bold text-lg tracking-tight">MeetingToVikunja</span>
                    </div>
                </div>
                <div className="p-4 flex flex-col gap-1">
                    {[
                        { icon: CloudUpload, label: 'Importar Tarefas', href: '/batch' },
                        { icon: Mic, label: 'Agente de Voz', href: '/voice' },
                        { icon: Settings, label: 'Configurações', href: '/settings' },
                    ].map((item) => (
                        <Link
                            key={item.href}
                            to={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors",
                                isActive(item.href)
                                    ? "bg-primary/10 text-primary"
                                    : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white"
                            )}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.label}
                        </Link>
                    ))}
                </div>
            </div>

            <div className="p-4 border-t border-gray-100 dark:border-gray-800">
                <div className="flex items-center gap-3 px-3 py-2">
                    <Avatar className="h-8 w-8">
                        <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
                        <AvatarFallback>CN</AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col overflow-hidden">
                        <p className="text-sm font-medium truncate">Alex Morgan</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">v1.0.4</p>
                    </div>
                </div>
            </div>
        </aside >
    );
}
