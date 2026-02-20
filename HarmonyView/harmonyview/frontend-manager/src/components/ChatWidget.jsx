import React, { useState, useRef, useEffect } from 'react';
import './ChatWidget.css'; // We'll create this CSS file next

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const toggleChat = () => {
        setIsOpen(!isOpen);
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return;

        const userMessage = { text: inputValue, sender: 'user' };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8001/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage.text }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            const botMessage = { text: data.response, sender: 'bot' };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = { text: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', sender: 'bot', isError: true };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    };

    return (
        <div className={`chat-widget ${isOpen ? 'open' : ''}`}>
            {!isOpen && (
                <button className="chat-toggle-btn" onClick={toggleChat}>
                    💬 HarmonyAI
                </button>
            )}

            {isOpen && (
                <div className="chat-window">
                    <div className="chat-header">
                        <div className="chat-title">
                            <h3>HarmonyAI Asistan</h3>
                            <span className="online-status">● Çevrimiçi</span>
                        </div>
                        <button className="close-btn" onClick={toggleChat}>×</button>
                    </div>

                    <div className="chat-messages">
                        {messages.length === 0 && (
                            <div className="welcome-message">
                                <p>Merhaba! Ben HarmonyAI.</p>
                                <p>Lojistik verileri hakkında bana soru sorabilirsin.</p>
                                <p className="example-query">"Bugün V710 hattından kaç dolly sevk edildi?"</p>
                            </div>
                        )}

                        {messages.map((msg, index) => (
                            <div key={index} className={`message ${msg.sender} ${msg.isError ? 'error' : ''}`}>
                                <div className="message-content">{msg.text}</div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="message bot loading">
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-input-area">
                        <input
                            type="text"
                            placeholder="Bir soru sorun..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={isLoading}
                        />
                        <button onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()}>
                            ➤
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatWidget;
