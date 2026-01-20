import React from "react";

export default function MessageList({ messages }) {
    return (
        <div className="flex-1 w-full max-w-2xl mx-auto overflow-y-auto space-y-3 p-4">
            {messages.map((m, i) => (
                <div
                    key={i}
                    className={`p-3 rounded-lg max-w-[80%] ${m.role === "user"
                            ? "ml-auto bg-indigo-600"
                            : "mr-auto bg-gray-800"
                        }`}
                >
                    {m.content}
                </div>
            ))}
        </div>
    );
}
