// ===========================================
// Gestionnaire des appels API pour le chatbot
// ===========================================

import type { Message, ChatRequest, ChatResponse } from "../types/chatTypes";

/* URL de l'API backend */
const API_URL = import.meta.env.VITE_BACKEND_URL;

/* Vérifie la présence du cookie de session */
export function hasSessionCookie() {
  return document.cookie
    .split(";")
    .some((c) => c.trim().startsWith("polybot_session_id="));
}

/* Initialise la session côté backend (cookie HttpOnly) */
export async function initSession() {
  if (!hasSessionCookie()) {
    await fetch(`${API_URL}/init-session`, { credentials: "include" });
  }
}

/* Récupère l'historique des messages d'un utilisateur */
export async function fetchHistory(): Promise<Message[]> {
  const res = await fetch(`${API_URL}/history`, {
    method: "GET",
    credentials: "include",
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
  const payload: ChatRequest = { prompt: input, chat_history };
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  return await res.json();
}
