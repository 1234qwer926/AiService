// src/components/TextPanel.jsx
import React, { useState } from "react";

const TextPanel = ({ sessionId, onStageUpdate }) => {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([]);

    const send = async () => {
        if (!input.trim()) return;

        const userMsg = { role: "user", content: input };
        setMessages((m) => [...m, userMsg]);

        const res = await fetch("http://localhost:8000/monica/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                text: input,
            }),
        });

        const data = await res.json();

        const botMsg = { role: "assistant", content: data.reply };
        setMessages((m) => [...m, botMsg]);

        setInput("");
    };

    return (
        <div className="w-full max-w-2xl mx-auto flex flex-col h-[70vh] bg-gray-900/40 rounded-2xl border border-gray-800 p-4">
            <div className="flex-1 overflow-y-auto space-y-3">
                {messages.map((m, i) => (
                    <div
                        key={i}
                        className={`p-3 rounded-xl max-w-[80%] ${m.role === "user"
                            ? "ml-auto bg-indigo-600"
                            : "mr-auto bg-gray-800"
                            }`}
                    >
                        {m.content}
                    </div>
                ))}
            </div>

            <div className="mt-3 flex gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && send()}
                    className="flex-1 bg-black/40 border border-gray-700 rounded-xl px-4 py-2 outline-none"
                    placeholder="Type your response…"
                />
                <button
                    onClick={send}
                    className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default TextPanel;
