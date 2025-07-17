// =====================================
// Hook pour gérer la validation captcha
// =====================================

import { useState, useRef, useCallback, useEffect } from "react";
import ReCAPTCHA from "react-google-recaptcha";

const CAPTCHA_VALID_KEY = "captcha_validated_until";
const CAPTCHA_VALID_DURATION = 60 * 60 * 1000; // 1 heure en ms

const useRecaptcha = () => {
  const [isValid, setIsValid] = useState<boolean>(false);
  const [token, setToken] = useState<string>("");
  const recaptchaRef = useRef<ReCAPTCHA | null>(null);

  // Vérifier au démarrage s'il y a une validation récente
  useEffect(() => {
    const validUntil = localStorage.getItem(CAPTCHA_VALID_KEY);

    if (validUntil && Date.now() < parseInt(validUntil, 10)) {
      setIsValid(true);
    } else {
      setIsValid(false);
      setToken("");
      localStorage.removeItem(CAPTCHA_VALID_KEY);
    }
  }, []);

  // On vérifie périodiquement si la validation captcha est encore valide
  useEffect(() => {
    const interval = setInterval(() => {
      const validUntil = localStorage.getItem(CAPTCHA_VALID_KEY);
      if (validUntil && Date.now() < parseInt(validUntil, 10)) {
        if (!isValid) {
          setIsValid(true);
        }
      } else {
        if (isValid) {
          setIsValid(false);
          setToken("");
          localStorage.removeItem(CAPTCHA_VALID_KEY);
        }
      }
    }, 1000); // vérifie toutes les secondes

    return () => clearInterval(interval);
  }, [isValid]);

  const handleCaptchaChange = useCallback((token: string | null) => {
    if (token) {
      setToken(token);
      setIsValid(true);
      const validUntil = Date.now() + CAPTCHA_VALID_DURATION;
      localStorage.setItem(CAPTCHA_VALID_KEY, validUntil.toString());
    } else {
      setToken("");
      setIsValid(false);
      localStorage.removeItem(CAPTCHA_VALID_KEY);
    }
  }, []);

  const resetCaptcha = useCallback(() => {
    // @ts-ignore
    recaptchaRef.current?.reset();
    setToken("");
    setIsValid(false);
    localStorage.removeItem(CAPTCHA_VALID_KEY);
  }, []);

  // On affiche le widget reCAPTCHA seulement si pas de token
  const RecaptchaComponent = !isValid ? (
    <ReCAPTCHA
      ref={recaptchaRef}
      sitekey={import.meta.env.VITE_RECAPTCHA_SITE_KEY}
      onChange={handleCaptchaChange}
      onExpired={() => handleCaptchaChange(null)}
    />
  ) : null;

  return {
    isValid,
    token,
    RecaptchaComponent,
    resetCaptcha,
  };
};

export default useRecaptcha;
