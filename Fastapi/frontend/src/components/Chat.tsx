/*
 * =============================================================================================
 * Composant Chat
 * Conteneur principal du chatbot : affiche l'en-tête, la liste des messages et la barre d'input
 * =============================================================================================
 */

import { useState } from "react";
import type { Message, ChatRequest, ChatResponse } from "../types";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  /* Gère l'envoi d'un message utilisateur et la réponse du bot */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    /* Crée un nouveau message utilisateur et l'ajoute à la liste des messages */
    const newUserMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
    setLoading(true);

    /* Prépare la requête pour l'API du backend */
    const payload: ChatRequest = {
      prompt: input,
      chat_history: messages,
    };

    /* Envoie la requête au backend pour obtenir la réponse du bot */
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

    /* Ajoute la réponse du bot à la liste des messages */
    setMessages((prev) => [...prev, botMessage]);
    setLoading(false);
  };

  return (
    /* Conteneur principal du chat */
    <div className="chat-container">
      <h1 className="chat-title">PolyChat</h1>
      <div className="chat-subtitle">
        Le chatbot de Polytech Sorbonne qui répond à toutes vos questions !
      </div>
      <div className="chat-messages-container">
        <ChatMessages messages={messages} isLoading={loading} />
      </div>
      <ChatInput
        input={input}
        setInput={setInput}
        onSubmit={handleSubmit}
        disabled={loading}
      />
    </div>
  );
}
