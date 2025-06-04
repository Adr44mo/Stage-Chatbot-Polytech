export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string;
  loading?: boolean; 
}

export interface ChatRequest {
  prompt: string;
  chat_history: Message[];
}

export interface ChatResponse {
  answer: string;
  sources: string;
}
