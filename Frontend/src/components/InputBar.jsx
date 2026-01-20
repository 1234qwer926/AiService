import React, { useState } from "react";

export default function InputBar({ onSend, disabled }) {
    const [text, setText] = useState("");

    const submit = () => {
        if (!text.trim()) return;
        onSend(text);
        setText("");
    };

    return (
        <div className="w-full max-w-2xl mx-auto flex gap-2 p-4">
            <input
                className="flex-1 bg-gray-800 rounded px-3 py-2 outline-none"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Type your response..."
                onKeyDown={(e) => e.key === "Enter" && submit()}
            />
            <button
                onClick={submit}
                disabled={disabled}
                className="px-4 py-2 bg-indigo-600 rounded"
            >
                Send
            </button>
        </div>
    );
}
