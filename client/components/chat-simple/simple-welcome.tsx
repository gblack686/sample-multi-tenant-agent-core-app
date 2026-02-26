'use client';

interface SimpleWelcomeProps {
    onAction?: (text: string) => void;
}

const features = [
    { emoji: '📋', label: 'Acquisition Intake', command: '/acquisition-package ' },
    { emoji: '📝', label: 'Document Generation', command: '/document ' },
    { emoji: '📚', label: 'FAR/DFARS Search', command: '/research ' },
    { emoji: '💰', label: 'Cost Estimation', command: '/igce ' },
];

export default function SimpleWelcome({ onAction }: SimpleWelcomeProps) {
    return (
        <div className="flex-1 flex flex-col items-center justify-center p-5 gap-4 text-center">
            {/* Eagle emoji */}
            <div className="text-[64px] leading-none">🦅</div>

            {/* Title */}
            <h2 className="text-2xl font-bold text-[#003366]">Welcome to EAGLE</h2>

            {/* Subtitle */}
            <p className="text-sm text-[#4A5568] max-w-[520px] leading-relaxed">
                Your AI-powered NCI Acquisition Assistant. I help contracting officers,
                program managers, and acquisition professionals with federal procurement tasks.
            </p>

            {/* Feature cards — 4 in a row */}
            <div className="flex gap-4 flex-wrap justify-center mt-2">
                {features.map((f) => (
                    <button
                        key={f.label}
                        onClick={() => onAction?.(f.command)}
                        className="bg-white border border-[#D8DEE6] rounded-xl p-4 w-[180px] text-center cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md"
                    >
                        <div className="text-[28px] mb-1.5">{f.emoji}</div>
                        <div className="text-xs font-semibold text-[#003366]">{f.label}</div>
                    </button>
                ))}
            </div>
        </div>
    );
}
