// =====================================
// Composant ChatMessages
// Affiche la liste des messages du chat
// =====================================

import Markdown from "react-markdown";
import useAutoScroll from "../hooks/useAutoScroll";
import Spinner from "./Spinner";
import type { Message } from "../types";
import userIcon from "../assets/user.svg";
import { renderSources } from "../utils";

interface ChatMessagesProps {
  messages: Message[] /* Liste des messages à afficher */;
  isLoading: boolean /* Indique si le chat est en cours de chargement */;
}

export default function ChatMessages({
  messages,
  isLoading,
}: ChatMessagesProps) {
  const scrollContentRef = useAutoScroll(isLoading);

  return (
    /* Conteneur principal des messages */
    <div ref={scrollContentRef} className="chat-messages-list">
      {messages.map((msg, idx) => {
        const isUser = msg.role === "user";
        const isLastAssistantMsg =
          idx === messages.length - 1 &&
          msg.role === "assistant" &&
          !msg.content &&
          isLoading;

        return (
          /* Ligne de message */
          <div
            key={idx}
            className={
              isUser
                ? "chat-message-row chat-message-user"
                : "chat-message-row chat-message-assistant"
            }
          >
            <div
              className={isUser ? "chat-bubble-user user-bubble-with-icon" : ""}
            >
              {isUser && (
                <img
                  className="chat-user-icon-inside"
                  src={userIcon}
                  alt="user"
                />
              )}
              {isLastAssistantMsg ? (
                <Spinner />
              ) : msg.role === "assistant" ? (
                <div className="markdown-container">
                  <Markdown>{msg.content}</Markdown>
                </div>
              ) : (
                <div className="chat-message-user-content">
                  {msg.content.trimEnd()}
                </div>
              )}

              {/* Affichage des sources pour les messages de l'assistant */}
              {msg.role === "assistant" && msg.sources && (
                <div className="chat-message-sources">
                  <strong>Sources :</strong>
                  <br />
                  {renderSources(msg.sources)}
                </div>
              )}
            </div>
          </div>
        );
      })}
      {/* Spinner pendant le chargement */}
      {isLoading && (
        <div className="chat-messages-spinner-row">
          <Spinner />
        </div>
      )}
    </div>
  );
}
