/*
 * =============================================================================================
 * Page Chat pour intégration iframe
 * Version identique à ChatbotPage mais optimisée pour iframe
 * =============================================================================================
 */

import { useEffect } from "react";
import Chat from "../components/Chatbot/Chat";
import { initSession } from "../api/chatApi";
import "../index.css";

/* Page de chat pour iframe - IDENTIQUE au site principal */
export default function ChatIframePage() {
  // Initialisation de session identique au site principal
  useEffect(() => {
    const initSessionForIframe = async () => {
      try {
        console.log("🔄 [IFRAME] Initialisation session...");
        await initSession();
        console.log("✅ [IFRAME] Session initialisée avec succès");
        
        // Debug spécifique iframe
        console.log("📍 [IFRAME] Location:", window.location.href);
        console.log("🖼️ [IFRAME] Dans iframe:", window !== window.parent);
        console.log("🔑 [IFRAME] reCAPTCHA key:", import.meta.env.VITE_RECAPTCHA_SITE_KEY);
        console.log("🌐 [IFRAME] API URL:", import.meta.env.VITE_BACKEND_URL);
        
        // Vérifier si reCAPTCHA peut se charger
        if (typeof (window as any).grecaptcha !== 'undefined') {
          console.log("✅ [IFRAME] reCAPTCHA script chargé");
        } else {
          console.log("❌ [IFRAME] reCAPTCHA script NON chargé");
        }
      } catch (error) {
        console.error("❌ [IFRAME] Erreur initialisation session:", error);
      }
    };
    
    initSessionForIframe();
  }, []);

  return (
    <div className="iframe-chat-wrapper">
      {/* Composant Chat IDENTIQUE au site principal */}
      <div className="chat-page">
        <Chat />
      </div>
    </div>
  );
}
