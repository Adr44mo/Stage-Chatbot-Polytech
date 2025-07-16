// =======================================================
// Page de connexion admin
// Affiche le formulaire de connexion et gère l'état local
// =======================================================

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAdminAuth } from "../auth/AdminAuthContext";
import { loginAdmin } from "../api/authApi";
import useRecaptcha from "../hooks/useRecaptcha";

const LoginPage: React.FC = () => {
  // États locaux pour le formulaire et l'affichage
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { refreshAuth } = useAdminAuth();
  const { token: recaptchaToken, RecaptchaComponent } = useRecaptcha();

  // Gère la soumission du formulaire de login
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!recaptchaToken) {
      setError("Veuillez valider le reCAPTCHA");
      return;
    }

    setLoading(true);
    setError("");
    const result = await loginAdmin(username, password, recaptchaToken);
    if (result.ok) {
      // On met à jour l'état d'auth global et on redirige vers la page admin si succès
      await refreshAuth();
      navigate("/admin");
    } else {
      setError(result.error || "Erreur d'authentification");
    }
    setLoading(false);
  };

  return (
    <div className="login-page-container">
      <h2>Connexion admin</h2>
      <form onSubmit={handleSubmit} className="login-form">
        <div className="login-form-group">
          <input
            type="text"
            placeholder="Nom d'utilisateur"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="login-input"
          />
        </div>
        <div className="login-form-group">
          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="login-input"
          />
        </div>
        {error && <div className="login-error-message">{error}</div>}
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            margin: "1rem 0",
          }}
        >
          {RecaptchaComponent}
        </div>
        <button type="submit" disabled={loading} className="login-submit-btn">
          {loading ? "Connexion..." : "Se connecter"}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
