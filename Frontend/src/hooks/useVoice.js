import { useState, useRef, useCallback } from 'react';

const useVoice = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);

    const wsRef = useRef(null);
    const audioContextRef = useRef(null);
    const audioQueueRef = useRef([]);
    const isPlayingRef = useRef(false);

    // Initialize Audio Context on user gesture or mount (must be resumed later)
    const initAudio = () => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
        }
    };

    const connect = useCallback((sessionId) => {
        if (!sessionId) return;
        initAudio();

        // Connect WS
        const ws = new WebSocket(`ws://localhost:8000/ws/monica/${sessionId}`);
        ws.binaryType = "arraybuffer";

        ws.onopen = () => {
            console.log("Connected to Monica Live");
            setIsConnected(true);
            startRecording(ws);
        };

        ws.onmessage = async (event) => {
            const data = event.data;

            if (data instanceof ArrayBuffer) {
                queueAudio(data);
            } else {
                try {
                    const msg = JSON.parse(data);
                    if (msg.type === "stage_update") {
                        window.dispatchEvent(
                            new CustomEvent("monica-stage", { detail: msg.stage })
                        );
                    }
                } catch { }
            }
        };


        ws.onclose = () => setIsConnected(false);
        wsRef.current = ws;

    }, []);

    const startRecording = async (ws) => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const context = audioContextRef.current;
            const source = context.createMediaStreamSource(stream);

            // Use ScriptProcessor for legacy support or AudioWorklet for modern
            const processor = context.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                if (ws.readyState === WebSocket.OPEN) {
                    const inputData = e.inputBuffer.getChannelData(0);

                    // Downsample/Convert to PCM 16/24kHz INT16 if needed
                    // Gemini supports raw PCM. Let's send raw float32 or convert to int16.
                    // Sending Int16 is standard.
                    const pcm16 = convertFloat32ToInt16(inputData);

                    // Decode int16 to base64 for JSON transport or send raw bytes
                    // The backend expects {"bytes": "base64..."} JSON for simplicity in the impl plan
                    // But sending generic binary is more efficient. Backend monica_service handles {"bytes": ...}
                    // Let's send JSON with base64 encoded bytes for now as per my backend logic
                    // Bytes in JSON:

                    const base64 = btoa(String.fromCharCode(...new Uint8Array(pcm16.buffer)));
                    ws.send(JSON.stringify({ bytes: base64 }));
                }
            };

            source.connect(processor);
            processor.connect(context.destination); // Mute locally if needed? Usually bad for echo cancel.
            // Better: source.connect(processor); processor.connect(context.destination); 
            // But we don't want to hear ourselves. 
            // Just connect processor to destination to keep it alive, but zero gain.
        } catch (err) {
            console.error("Mic Error:", err);
        }
    };

    const convertFloat32ToInt16 = (float32Array) => {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            let s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    };

    const queueAudio = (arrayBuffer) => {
        audioQueueRef.current.push(arrayBuffer);
        playNext();
    };

    const playNext = async () => {
        if (isPlayingRef.current || audioQueueRef.current.length === 0) return;

        isPlayingRef.current = true;
        setIsPlaying(true);

        const chunk = audioQueueRef.current.shift();
        const ctx = audioContextRef.current;

        // Decode raw PCM? Gemini sends raw PCM. AudioContext.decodeAudioData expects headers (WAV).
        // We need to play raw PCM.
        // Create buffer manually.
        // Assuming 24kHz (Gemini default) mono.

        try {
            // If Gemini sends raw PCM bytes (Int16/Float), we must know format.
            // Bidi API sends: "Linear 16-bit PCM (little-endian) audio samples at 24kHz."

            const int16 = new Int16Array(chunk);
            const float32 = new Float32Array(int16.length);
            for (let i = 0; i < int16.length; i++) {
                float32[i] = int16[i] / 32768.0;
            }

            const buffer = ctx.createBuffer(1, float32.length, 24000);
            buffer.getChannelData(0).set(float32);

            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);
            source.start();

            source.onended = () => {
                isPlayingRef.current = false;
                setIsPlaying(false);
                playNext();
            };
        } catch (e) {
            console.error("Audio Playback Error:", e);
            isPlayingRef.current = false;
        }
    };

    const disconnect = () => {
        if (wsRef.current) wsRef.current.close();
        if (audioContextRef.current) audioContextRef.current.close();
    };

    return { isConnected, isPlaying, connect, disconnect };
};

export default useVoice;
