// =====================================
// Composant ChatMessages
// Affiche la liste des messages du chat
// =====================================

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import useAutoScroll from "../../hooks/useAutoScroll";
import Spinner from "./Spinner";
import type { Message } from "../../types/chatTypes";
import userIcon from "../../assets/user.svg";
import { renderSources } from "../../utils/chatUtils";

interface ChatMessagesProps {
  messages: Message[] /* Liste des messages à afficher */;
  isLoading: boolean /* Indique si le chat est en cours de chargement */;
}

export default function ChatMessages({
  messages,
  isLoading,
}: ChatMessagesProps) {
  const scrollContentRef = useAutoScroll(messages.length);

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
                /* Message de l'assistant */
                <div className="markdown-container">
                  <Markdown remarkPlugins={[remarkGfm]}>{msg.content}</Markdown>
                </div>
              ) : (
                /* Message utilisateur */
                <div className="chat-message-user-content">
                  {msg.content.trimEnd()}
                </div>
              )}

              {/* Affichage des sources pour les messages de l'assistant */}
              {msg.role === "assistant" &&
                msg.sources &&
                msg.sources.length > 0 && (
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
