/*
 * =============================================================================================
 * Composant Chat
 * Conteneur principal du chatbot : affiche l'en-tête, la liste des messages et la barre d'input
 * =============================================================================================
 */

import { useState, useEffect } from "react";
import type { Message } from "../types";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";
import { fetchHistory, sendMessage } from "../chatApi";

/* Message d'introduction */
const INTRO_MESSAGE: Message = {
  role: "assistant",
  content:
    "👋 Bonjour, je suis le chatbot représentant Polytech Sorbonne. Posez-moi vos questions sur l'école, je vous répondrai avec plaisir !",
};

/* Composant principal du chat */
export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  /* Récupère l'historique d'un utilisateur depuis le backend au chargement */
  useEffect(() => {
    fetchHistory()
      .then((history) => {
        if (Array.isArray(history) && history.length > 0) {
          setMessages(history);
        } else {
          setMessages([INTRO_MESSAGE]);
        }
      })
      .catch(() => setMessages([INTRO_MESSAGE]));
  }, []);

  /* Gère l'envoi d'un message utilisateur et la réponse du bot */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    /* Crée un nouveau message utilisateur et l'ajoute à la liste des messages */
    const newUserMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendMessage(input, [...messages, newUserMessage]);
      const botMessage: Message = {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      };
      /* Ajoute la réponse du bot à la liste des messages */
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      /* Optionnel : gestion d'erreur utilisateur */
    } finally {
      setLoading(false);
    }
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
