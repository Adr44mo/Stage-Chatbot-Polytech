// =====================================
// Hook pour gérer la validation captcha
// =====================================

import { useState, useRef, useCallback, useEffect } from "react";
import ReCAPTCHA from "react-google-recaptcha";

const useRecaptcha = () => {
  const [isValid, setIsValid] = useState<boolean>(false);
  const [token, setToken] = useState<string>("");
  const recaptchaRef = useRef<ReCAPTCHA | null>(null);

  // Vérifier au démarrage s'il y a une validation récente (1 heure)
  useEffect(() => {
    const lastValidation = localStorage.getItem("captcha_validated");

    if (lastValidation) {
      const validatedAt = parseInt(lastValidation, 10);
      const oneHour = 60 * 60 * 1000; // 1 heure en ms

      if (Date.now() - validatedAt < oneHour) {
        setIsValid(true);
      } else {
        localStorage.removeItem("captcha_validated");
        setToken("");
      }
    }
  }, []);

  const handleCaptchaChange = useCallback((token: string | null) => {
    if (token) {
      setToken(token);
      setIsValid(true);
      localStorage.setItem("captcha_validated", Date.now().toString());
    } else {
      setToken("");
      setIsValid(false);
      localStorage.removeItem("captcha_validated");
    }
  }, []);

  const resetCaptcha = useCallback(() => {
    // @ts-ignore
    recaptchaRef.current?.reset();
    setToken("");
    setIsValid(false);
    localStorage.removeItem("captcha_validated");
  }, []);

  const RecaptchaComponent = token ? null : (
    <ReCAPTCHA
      ref={recaptchaRef}
      sitekey={import.meta.env.VITE_RECAPTCHA_SITE_KEY}
      onChange={handleCaptchaChange}
      onExpired={() => handleCaptchaChange(null)}
    />
  );

  return {
    isValid,
    token,
    RecaptchaComponent,
    resetCaptcha,
  };
};

export default useRecaptcha;
