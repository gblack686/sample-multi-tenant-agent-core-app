'use client';

import { useState, useEffect } from 'react';
import { checkBackendHealth } from '@/hooks/use-agent-stream';

export default function SimpleHeader() {
    const [backendConnected, setBackendConnected] = useState<boolean | null>(null);

    useEffect(() => {
        checkBackendHealth().then(setBackendConnected);
        const interval = setInterval(() => {
            checkBackendHealth().then(setBackendConnected);
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <header
            className="bg-[#003366] text-white px-6 flex items-center justify-between shrink-0 z-10"
            style={{ height: 56, boxShadow: '0 2px 8px rgba(0,51,102,0.3)' }}
        >
            <div className="flex items-center gap-3">
                <span className="text-[28px] leading-none" style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))' }}>
                    🦅
                </span>
                <div>
                    <h1 className="text-lg font-bold tracking-wider">EAGLE</h1>
                    <p className="text-[11px] text-white/70 tracking-wide">Acquisition Assistant &middot; Powered by Claude</p>
                </div>
            </div>
            <div className="flex items-center gap-1.5">
                <span
                    className={`inline-block w-2 h-2 rounded-full ${
                        backendConnected === null
                            ? 'bg-[#D4A843] animate-pulse'
                            : backendConnected
                                ? 'bg-[#4CAF50]'
                                : 'bg-[#E53935]'
                    }`}
                    style={backendConnected ? { boxShadow: '0 0 6px rgba(76,175,80,0.6)' } : {}}
                />
                <span className="text-xs text-white/85">
                    {backendConnected === null ? 'Connecting\u2026' : backendConnected ? 'Connected' : 'Offline'}
                </span>
            </div>
        </header>
    );
}
