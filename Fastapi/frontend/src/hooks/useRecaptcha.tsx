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
    const storedToken = localStorage.getItem("captcha_token");

    if (lastValidation && storedToken) {
      const validatedAt = parseInt(lastValidation, 10);
      const oneHour = 60 * 60 * 1000; // 1 heure en ms

      if (Date.now() - validatedAt < oneHour) {
        setIsValid(true);
        setToken(storedToken);
      } else {
        localStorage.removeItem("captcha_validated");
        localStorage.removeItem("captcha_token");
        setToken("");
      }
    }
  }, []);

  const handleCaptchaChange = useCallback((token: string | null) => {
    if (token) {
      setToken(token);
      setIsValid(true);
      // On stocke la validation et le token pendant 1 heure
      localStorage.setItem("captcha_validated", Date.now().toString());
      localStorage.setItem("captcha_token", token);
    } else {
      setToken("");
      setIsValid(false);
      localStorage.removeItem("captcha_validated");
      localStorage.removeItem("captcha_token");
    }
  }, []);

  const resetCaptcha = useCallback(() => {
    // @ts-ignore
    recaptchaRef.current?.reset();
    setToken("");
    setIsValid(false);
    localStorage.removeItem("captcha_validated");
    localStorage.removeItem("captcha_token");
  }, []);

  const RecaptchaComponent = isValid ? null : (
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
