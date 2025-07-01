// ========================================================
// Composant AdminLogoutButton
// Permet de se déconnecter de l'interface d'administration
// ========================================================

import React from "react";
import { useNavigate } from "react-router-dom";
import { logoutAdmin } from "../../api/authApi";
import { useAdminAuth } from "../../auth/AdminAuthContext";

const AdminLogoutButton: React.FC = () => {
  const navigate = useNavigate();
  const { refreshAuth } = useAdminAuth();

  const handleLogout = async () => {
    await logoutAdmin(); // On supprime le cookie de session côté backend
    await refreshAuth(); // On rafraîchit l'état d'authentification côté frontend
    navigate("/login"); // On redirige vers la page de login
  };

  return (
    <button onClick={handleLogout} className="admin-logout-btn">
      Déconnexion
    </button>
  );
};

export default AdminLogoutButton;
