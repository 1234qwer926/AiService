import React, { useState, useEffect, useRef } from 'react';
import './MonicaChat.css';

const MonicaChat = () => {
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [stage, setStage] = useState('SETUP');
    const [persona, setPersona] = useState('COACH');
    const chatEndRef = useRef(null);

    const API_BASE = 'http://localhost:8000';

    useEffect(() => {
        // Scroll to bottom whenever messages change
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const startNewSession = async () => {
        try {
            const resp = await fetch(`${API_BASE}/monica/session`, { method: 'POST' });
            const data = await resp.json();
            setSessionId(data.id);
            setStage(data.current_stage);
            setPersona(data.current_persona);
            setMessages([]);
        } catch (err) {
            console.error('Failed to start session', err);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || !sessionId) return;

        const userMsg = { role: 'user', content: input, persona: persona };
        setMessages([...messages, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const resp = await fetch(`${API_BASE}/monica/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, text: input })
            });
            const data = await resp.json();

            setMessages(prev => [...prev, { role: 'assistant', content: data.reply, persona: persona }]);

            // Fetch session state to update stage/persona
            const sessionResp = await fetch(`${API_BASE}/monica/session/${sessionId}`);
            const sessionData = await sessionResp.json();
            setStage(sessionData.current_stage);
            setPersona(sessionData.current_persona);

        } catch (err) {
            console.error('Failed to send message', err);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Connection lost. Please try again.', persona: 'COACH' }]);
        } finally {
            setLoading(false);
        }
    };

    if (!sessionId) {
        return (
            <div className="monica-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div className="agent-avatar" style={{ width: 80, height: 80, fontSize: '2em', margin: '0 auto 20px' }}>007</div>
                    <h2 style={{ color: '#fff' }}>Agent Monica 007</h2>
                    <p style={{ color: '#888', marginBottom: 30 }}>Sales Coaching Intelligence System</p>
                    <button className="send-button" style={{ height: 50 }} onClick={startNewSession}>INITIALIZE AGENT</button>
                </div>
            </div>
        );
    }

    return (
        <div className="monica-container">
            <div className="monica-header">
                <div className="agent-info">
                    <div className="agent-avatar">M</div>
                    <div className="agent-status">
                        <span className="agent-name">Monica 007</span>
                        <span className="agent-role">{persona} Persona</span>
                    </div>
                </div>
                <div className="stage-badge">STAGE: {stage}</div>
            </div>

            <div className="chat-history">
                {messages.map((msg, i) => (
                    <div key={i} className={`message-bubble message-${msg.role}`}>
                        {msg.role === 'assistant' && <div className="persona-label">{msg.persona}</div>}
                        {msg.content}
                    </div>
                ))}
                {loading && (
                    <div className="message-bubble message-assistant">
                        <div className="persona-label">{persona}</div>
                        <span className="typing-dots">Thinking...</span>
                    </div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div className="input-area">
                <input
                    type="text"
                    className="chat-input"
                    placeholder="Type your response..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    disabled={loading}
                />
                <button className="send-button" onClick={handleSend} disabled={loading || !input.trim()}>
                    SEND
                </button>
            </div>
        </div>
    );
};

export default MonicaChat;
