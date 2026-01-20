import React from 'react';
import { CheckCircle2, Circle } from 'lucide-react';
import { clsx } from 'clsx';

const stages = [
    { id: 'SETUP', label: 'Setup' },
    { id: 'RCPA', label: 'RCPA' },
    { id: 'INTELLIGENCE', label: 'Intelligence' },
    { id: 'DOCTOR', label: 'Pitch' },
    { id: 'OBJECTION', label: 'Objection' },
    { id: 'KNOWLEDGE', label: 'Knowledge' },
    { id: 'END', label: 'End' }
];

const StageIndicator = ({ currentStage }) => {
    const currentIndex = stages.findIndex(s => s.id === currentStage);

    return (
        <div className="w-full max-w-4xl mx-auto mb-12">
            <div className="flex justify-between items-center relative">
                {/* Progress Bar Background */}
                <div className="absolute top-1/2 left-0 w-full h-1 bg-gray-700 -z-10 transform -translate-y-1/2 rounded-full"></div>
                {/* Active Progress Bar */}
                <div
                    className="absolute top-1/2 left-0 h-1 bg-indigo-500 -z-10 transform -translate-y-1/2 rounded-full transition-all duration-500 ease-in-out"
                    style={{ width: `${(currentIndex / (stages.length - 1)) * 100}%` }}
                ></div>

                {stages.map((stage, index) => {
                    const isActive = stage.id === currentStage;
                    const isCompleted = index < currentIndex;
                    const isPending = index > currentIndex;

                    return (
                        <div key={stage.id} className="flex flex-col items-center">
                            <div
                                className={clsx(
                                    "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 border-2 bg-[#242424]",
                                    isActive ? "border-indigo-500 text-indigo-500 scale-125 shadow-[0_0_15px_rgba(99,102,241,0.6)]" :
                                        isCompleted ? "border-green-500 text-green-500" : "border-gray-600 text-gray-600"
                                )}
                            >
                                {isCompleted ? <CheckCircle2 size={16} /> : <Circle size={12} fill={isActive ? "currentColor" : "none"} />}
                            </div>
                            <span className={clsx(
                                "mt-2 text-xs font-medium tracking-wide transition-colors duration-300 absolute transform translate-y-8",
                                isActive ? "text-indigo-400" : isCompleted ? "text-green-500" : "text-gray-500"
                            )}>
                                {stage.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default StageIndicator;
