import React from "react";

const stages = [
    "SETUP",
    "RCPA",
    "INTELLIGENCE",
    "DOCTOR",
    "OBJECTION",
    "KNOWLEDGE",
    "END",
];

export default function StageIndicator({ current }) {
    const idx = stages.indexOf(current);

    return (
        <div className="flex justify-between w-full max-w-3xl mx-auto mb-6">
            {stages.map((s, i) => (
                <div key={s} className="flex flex-col items-center">
                    <div
                        className={`w-4 h-4 rounded-full ${i <= idx ? "bg-indigo-500" : "bg-gray-600"
                            }`}
                    />
                    <span className="text-xs mt-1 text-gray-400">{s}</span>
                </div>
            ))}
        </div>
    );
}
