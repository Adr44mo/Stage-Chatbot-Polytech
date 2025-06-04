/*
 * =======================================================================================
 * Composant ChatInput
 * Permet à l'utilisateur de saisir une question et de l'envoyer via un formulaire de chat
 * =======================================================================================
 */

/* Import des dépendances nécessaires */
import { useEffect } from "react";
import useAutosize from "../hooks/useAutosize";

/* Paramètres du composant ChatInput */
interface ChatInputProps {
  input: string /* Texte actuellement saisi par l'utilisateur */;
  setInput: (
    val: string
  ) => void /* Fonction pour mettre à jour la valeur de l'input */;
  onSubmit: (
    e: React.FormEvent
  ) => void /* Fonction appelée lors de la soumission du formulaire */;
  disabled: boolean /* Indique si l'input et le bouton d'envoi sont désactivés */;
}

/* Retourne un formulaire de saisie de message avec la zone de texte et le bouton d'envoi */
export default function ChatInput({
  input,
  setInput,
  onSubmit,
  disabled,
}: ChatInputProps) {
  const textareaRef = useAutosize(input);

  /* Remet le focus sur la zone de texte après l'envoi d'un message */
  useEffect(() => {
    if (input === "" && textareaRef.current && !disabled) {
      textareaRef.current.focus();
    }
  }, [input, textareaRef, disabled]);

  /* Permet d'envoyer une question avec Entrée */
  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !disabled) {
      e.preventDefault();
      if (input.trim().length > 0) {
        onSubmit(e as unknown as React.FormEvent);
      }
    }
  }

  return (
    /* Formulaire d'entrée du chat */
    <form className="chat-input-form" onSubmit={onSubmit}>
      {/* Zone de texte pour saisir la question */}
      <textarea
        className="chat-input-textarea"
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder="Posez votre question ici..."
        onKeyDown={handleKeyDown}
      />
      {/* Bouton d'envoi avec icône */}
      <button
        className="chat-input-send-btn"
        type="submit"
        disabled={disabled || input.trim() === ""}
        aria-label="Envoyer"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill={disabled || input.trim() === "" ? "#aaa" : "#007bff"}
          viewBox="0 0 24 24"
          width="24"
          height="24"
        >
          <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
        </svg>
      </button>
    </form>
  );
}
