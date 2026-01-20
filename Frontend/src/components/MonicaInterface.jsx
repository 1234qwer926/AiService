import React from "react";
import useMonicaChat from "../hooks/useMonicaChat";
import StageIndicator from "./StageIndicator";
import MessageList from "./MessageList";
import InputBar from "./InputBar";

export default function MonicaInterface() {
    const {
        session,
        messages,
        stage,
        loading,
        startSession,
        sendMessage,
    } = useMonicaChat();

    if (!session) {
        return (
            <div className="h-screen flex flex-col items-center justify-center">
                <h1 className="text-4xl font-bold mb-6">Agent Monica 007</h1>
                <button
                    onClick={startSession}
                    className="px-6 py-3 bg-indigo-600 rounded"
                >
                    Start Session
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col">
            <StageIndicator current={stage} />
            <MessageList messages={messages} />
            <InputBar onSend={sendMessage} disabled={loading} />
        </div>
    );
}
