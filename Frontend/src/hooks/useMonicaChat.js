import { useState } from "react";

export default function useMonicaChat() {
    const [session, setSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [stage, setStage] = useState("SETUP");
    const [loading, setLoading] = useState(false);

    const startSession = async () => {
        const res = await fetch("http://localhost:8000/monica/session", {
            method: "POST",
        });
        const data = await res.json();
        setSession(data);
        setStage(data.current_stage || "SETUP");
        setMessages([]);
    };

    const sendMessage = async (text) => {
        if (!session) return;
        setLoading(true);

        setMessages((m) => [...m, { role: "user", content: text }]);

        const res = await fetch("http://localhost:8000/monica/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: session.id,
                text,
            }),
        });

        const data = await res.json();

        setMessages((m) => [...m, { role: "assistant", content: data.reply }]);

        if (data.advance_stage) {
            setStage((prev) => prev); // backend controls real stage; indicator updates on refresh
        }

        setLoading(false);
    };

    return {
        session,
        messages,
        stage,
        loading,
        startSession,
        sendMessage,
    };
}
