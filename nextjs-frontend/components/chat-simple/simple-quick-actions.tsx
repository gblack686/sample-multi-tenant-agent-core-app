'use client';

const quickActions = [
    { emoji: '🆕', label: 'New Intake', command: 'I need to start a new acquisition intake for procuring a CT scanner for NCI.' },
    { emoji: '📄', label: 'Generate SOW', command: 'Generate a Statement of Work for a new IT services contract at NCI.' },
    { emoji: '📚', label: 'Search FAR', command: 'Search FAR/DFARS for simplified acquisition procedures and thresholds.' },
    { emoji: '💰', label: 'Cost Estimate', command: 'Create a cost estimate for procuring medical imaging equipment for NCI.' },
    { emoji: '🏢', label: 'Small Business', command: 'What are the small business set-aside requirements for a $500K procurement?' },
];

interface SimpleQuickActionsProps {
    onAction: (text: string) => void;
}

export default function SimpleQuickActions({ onAction }: SimpleQuickActionsProps) {
    return (
        <div className="flex items-center gap-2 px-6 py-2.5 bg-white border-b border-[#E8ECF1] flex-wrap shrink-0">
            {quickActions.map((action) => (
                <button
                    key={action.label}
                    onClick={() => onAction(action.command)}
                    className="px-3.5 py-1.5 text-xs font-medium text-[#003366] bg-[#EEF2F7] border border-[#D8DEE6] rounded-full whitespace-nowrap transition-all hover:bg-[#003366] hover:text-white hover:border-[#003366]"
                >
                    {action.emoji} {action.label}
                </button>
            ))}
        </div>
    );
}
