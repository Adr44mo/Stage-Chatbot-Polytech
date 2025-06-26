// =================================================================
// Composant de protection de route :
// Renvoie vers la page enfant uniquement si l'admin est authentifié
// =================================================================

import React from "react";
import { Navigate } from "react-router-dom";
import { useAdminAuth } from "./AdminAuthContext";

interface Props {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<Props> = ({ children }) => {
  const { isAuth, isLoading } = useAdminAuth();

  // On affiche la page protégée seulement si l'utilisateur est authentifié
  if (isLoading) return <div>Chargement...</div>;
  if (!isAuth) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

export default ProtectedRoute;
