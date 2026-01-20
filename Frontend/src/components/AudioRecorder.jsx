import React, { useEffect } from 'react';
import { Mic, MicOff } from 'lucide-react';

const AudioRecorder = ({ isListening, startListening, stopListening, disabled }) => {
    return (
        <div className="flex justify-center items-center mt-8">
            <button
                onClick={isListening ? stopListening : startListening}
                disabled={disabled}
                className={`
          relative w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300
          ${disabled ? 'bg-gray-600 opacity-50 cursor-not-allowed' :
                        isListening ? 'bg-red-500 hover:bg-red-600 shadow-[0_0_30px_rgba(239,68,68,0.6)] animate-pulse' :
                            'bg-indigo-600 hover:bg-indigo-500 shadow-[0_0_20px_rgba(79,70,229,0.4)]'}
        `}
            >
                {isListening ? (
                    <MicOff className="w-8 h-8 text-white" />
                ) : (
                    <Mic className="w-8 h-8 text-white" />
                )}

                {/* Ripple effect rings when listening */}
                {isListening && (
                    <>
                        <span className="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-20 animate-ping"></span>
                        <span className="absolute inline-flex h-[140%] w-[140%] rounded-full border border-red-500 opacity-30 animate-pulse delay-75"></span>
                    </>
                )}
            </button>
            <div className="absolute mt-32 text-gray-400 font-light text-sm tracking-widest uppercase">
                {isListening ? "Listening..." : "Tap to Speak"}
            </div>
        </div>
    );
};

export default AudioRecorder;
