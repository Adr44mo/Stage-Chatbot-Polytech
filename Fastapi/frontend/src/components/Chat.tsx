import { useState } from "react";
import type { Message, ChatRequest, ChatResponse } from "../types";

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newUserMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
    setLoading(true);

    const payload: ChatRequest = {
      prompt: input,
      chat_history: messages,
    };

    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data: ChatResponse = await response.json();

    const botMessage: Message = {
      role: "assistant",
      content: data.answer,
      sources: data.sources,
    };

    setMessages((prev) => [...prev, botMessage]);
    setLoading(false);
  };

  return (
    <div className="chat-container" style={{ maxWidth: "600px", margin: "auto" }}>
      <h1>PolyChat</h1>
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.role}>
            <strong>{msg.role === "user" ? "Vous" : "Assistant"}:</strong> {msg.content}
            {msg.role === "assistant" && msg.sources && (
              <div className="sources">
                <small><strong>Sources :</strong><br />{msg.sources}</small>
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          placeholder="Posez une question..."
          style={{ width: "100%", padding: "8px" }}
        />
      </form>
    </div>
  );
}
