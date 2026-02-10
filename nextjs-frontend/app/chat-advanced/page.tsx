import ChatInterface from '@/components/chat/chat-interface';
import TopNav from '@/components/layout/top-nav';
import AuthGuard from '@/components/auth/auth-guard';

export default function ChatAdvanced() {
    return (
        <AuthGuard>
            <div className="flex flex-col h-screen bg-gray-50">
                <TopNav />
                <main className="flex-1 overflow-hidden">
                    <ChatInterface />
                </main>
            </div>
        </AuthGuard>
    );
}
