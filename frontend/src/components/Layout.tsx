import { LayoutDashboard, Mic, Bot } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { cn } from '../lib/utils';

interface LayoutProps {
    children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
    return (
        <div className="flex h-screen bg-background">
            {/* Sidebar */}
            <div className="w-64 border-r bg-card flex flex-col">
                <div className="p-6 flex items-center gap-2 border-b">
                    <Bot className="w-6 h-6 text-primary" />
                    <h1 className="font-bold text-lg">Vikunja AI</h1>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    <NavLink
                        to="/batch"
                        className={({ isActive }) => cn(
                            "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                            isActive ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted"
                        )}
                    >
                        <LayoutDashboard className="w-5 h-5" />
                        Batch Upload
                    </NavLink>

                    <NavLink
                        to="/voice"
                        className={({ isActive }) => cn(
                            "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                            isActive ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-muted"
                        )}
                    >
                        <Mic className="w-5 h-5" />
                        Voice Agent
                        <span className="ml-auto text-xs bg-muted-foreground/20 px-1.5 py-0.5 rounded text-muted-foreground">Beta</span>
                    </NavLink>
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 border-b flex items-center px-6">
                    <h2 className="font-semibold text-lg">Batch Processing</h2>
                </header>
                <main className="flex-1 overflow-auto p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
