
import { Sidebar } from './Sidebar';

interface LayoutProps {
    children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
    return (
        <div className="flex h-screen w-full bg-gray-50 dark:bg-gray-950 font-sans text-gray-900 dark:text-gray-50">
            <Sidebar />
            <main className="flex-1 flex flex-col min-w-0 h-full relative overflow-hidden">
                {children}
            </main>
        </div>
    );
}
