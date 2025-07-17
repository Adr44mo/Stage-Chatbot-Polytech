// ==========================
// Page principale du chatbot
//  =========================

import Chat from "../components/Chatbot/Chat";
import useRecaptcha from "../hooks/useRecaptcha";

export default function ChatbotPage() {
  const { isValid, RecaptchaComponent } = useRecaptcha();
  const isCaptchaValidated = isValid;

  return (
    <div className="chatbot-page">
      <div className={`chat-wrapper ${!isCaptchaValidated ? "disabled" : ""}`}>
        <Chat />
      </div>

      {/* On affiche le widget de validation captcha s'il n'a pas été validé récemment*/}
      {!isCaptchaValidated && (
        <div className="captcha-overlay">
          <div className="captcha-modal">
            <div className="captcha-header">
              <h3>Bienvenue sur PolyBot</h3>
              <p>
                Votre assistant virtuel Polytech Sorbonne vous attend ! <br />
                Complétez la vérification pour commencer à discuter.
              </p>
            </div>
            <div className="captcha-widget">{RecaptchaComponent}</div>
          </div>
        </div>
      )}
    </div>
  );
}
