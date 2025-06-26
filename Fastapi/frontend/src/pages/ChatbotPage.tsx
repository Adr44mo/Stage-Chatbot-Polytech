import { useState } from "react";
import Chat from "../components/Chatbot/Chat";
import ReCAPTCHA from "react-google-recaptcha";

// Utilisation de la clé reCAPTCHA
const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY;

export default function ChatbotPage() {
  const [captchaValid, setCaptchaValid] = useState(false);

  // Callback appelé quand l'utilisateur valide le captcha
  const handleCaptcha = (token: string | null) => {
    if (token) setCaptchaValid(true);
  };

  return (
    <div>
      {!captchaValid ? (
        <div className="chatbot-captcha-container">
          <h2>Vérification anti-robot</h2>
          <p>Merci de valider le captcha pour accéder au chatbot.</p>
          <ReCAPTCHA sitekey={RECAPTCHA_SITE_KEY} onChange={handleCaptcha} />
        </div>
      ) : (
        <Chat />
      )}
    </div>
  );
}
