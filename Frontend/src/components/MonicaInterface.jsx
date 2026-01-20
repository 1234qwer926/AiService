import React, { useEffect, useState } from "react";
import useVoice from "../hooks/useVoice";
import StageIndicator from "./StageIndicator";
import TextPanel from "./TextPanel";
import { Play, RotateCcw } from "lucide-react";

const MonicaInterface = () => {
    const { isConnected, isPlaying, connect, disconnect } = useVoice();
    const [session, setSession] = useState(null);
    const [mode, setMode] = useState("voice"); // "voice" | "text"
    const [stage, setStage] = useState("SETUP");

    useEffect(() => {
        const handler = (e) => setStage(e.detail);
        window.addEventListener("monica-stage", handler);
        return () => window.removeEventListener("monica-stage", handler);
    }, []);

    const startSession = async () => {
        const res = await fetch("http://localhost:8000/monica/session", {
            method: "POST",
        });
        const data = await res.json();
        setSession(data);
        setStage(data.current_stage);
        if (mode === "voice") connect(data.id);
    };

    const endSession = () => {
        disconnect();
        setSession(null);
    };

    if (!session) {
        return (
            <div className="h-screen flex flex-col items-center justify-center bg-[#0f0f0f] text-white">
                <h1 className="text-5xl mb-6">Monica 007</h1>
                <button
                    onClick={startSession}
                    className="px-8 py-4 bg-indigo-600 rounded-full"
                >
                    Start Session <Play className="inline ml-2" />
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f0f0f] text-white flex flex-col items-center pt-8">
            <StageIndicator currentStage={stage} />

            {/* Mode Toggle */}
            <div className="mb-6 flex gap-2 bg-gray-800 rounded-full p-1">
                <button
                    onClick={() => {
                        setMode("voice");
                        connect(session.id);
                    }}
                    className={`px-4 py-2 rounded-full ${mode === "voice" ? "bg-indigo-600" : ""
                        }`}
                >
                    Voice
                </button>
                <button
                    onClick={() => {
                        setMode("text");
                        disconnect();
                    }}
                    className={`px-4 py-2 rounded-full ${mode === "text" ? "bg-indigo-600" : ""
                        }`}
                >
                    Text
                </button>
            </div>

            {mode === "text" ? (
                <TextPanel sessionId={session.id} />
            ) : (
                <div className="text-gray-400 mt-20">
                    {isConnected ? "Monica is listening…" : "Connecting…"}
                </div>
            )}

            <button
                onClick={endSession}
                className="fixed top-4 right-4 text-gray-400"
            >
                <RotateCcw />
            </button>
        </div>
    );
};

export default MonicaInterface;
