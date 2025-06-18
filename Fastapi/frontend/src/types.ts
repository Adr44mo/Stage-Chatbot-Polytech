// =================================================
// Types pour la gestion des messages et du chat RAG
// =================================================

// Représente un message individuel échangé dans la conversation
export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  loading?: boolean;
}

// Structure de la requête envoyée à l'API /chat
export interface ChatRequest {
  prompt: string;
  chat_history: Message[];
}

// Structure de la réponse renvoyée par l'API /chat
export interface ChatResponse {
  answer: string;
  sources: string[];
}
