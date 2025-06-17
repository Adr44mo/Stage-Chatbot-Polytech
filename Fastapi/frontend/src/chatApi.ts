/*
 * ===========================================
 * Gestionnaire des appels API pour le chatbot
 * ===========================================
 */

import type { Message, ChatRequest, ChatResponse } from "./types";

/* Gère/génère un id de session unique pour un utilisateur anonyme */
export function getOrCreateSessionId() {
  let sessionId = localStorage.getItem("polybot_session_id");
  if (!sessionId) {
    if (window.crypto?.randomUUID) {
      sessionId = window.crypto.randomUUID();
    } else {
      /* Si randomUUID n'est pas supporté (anciens navigateurs) */
      sessionId =
        Math.random().toString(36).substring(2) + Date.now().toString(36);
    }
    localStorage.setItem("polybot_session_id", sessionId);
  }
  return sessionId;
}

/* URL de l'API backend */
const API_URL = import.meta.env.VITE_BACKEND_URL;

/* Récupère l'historique des messages d'un utilisateur */
export async function fetchHistory(): Promise<Message[]> {
  const sessionId = getOrCreateSessionId();
  const res = await fetch(`${API_URL}/history`, {
    method: "GET",
    headers: { "X-Session-Id": sessionId },
  });
  if (!res.ok) return [];
  const history = await res.json();
  return Array.isArray(history)
    ? history.map((m) => ({
        role: m.role,
        content: m.content,
        sources: m.sources,
      }))
    : [];
}

/* Envoie un message utilisateur et récupère la réponse du bot */
export async function sendMessage(
  input: string,
  chat_history: Message[]
): Promise<ChatResponse> {
  const sessionId = getOrCreateSessionId();
  const payload: ChatRequest = { prompt: input, chat_history };
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-Id": sessionId,
    },
    body: JSON.stringify(payload),
  });
  return await res.json();
}
