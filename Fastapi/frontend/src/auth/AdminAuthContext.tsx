// ==========================================================
// Contexte d'authentification admin
// Donne l'état d'authentification (isAuth, isLoading, error)
// ==========================================================

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { checkAdminAuth } from "../api/adminApi";

// Données fournies par le contexte d'authentification admin
interface AdminAuthContextType {
  isAuth: boolean | null; // indique si l'admin est connecté (true/false) ou en cours de chargement (null)
  isLoading: boolean; // indique si la vérification d'auth est en cours
  error: string; // message d'erreur réseau éventuel
  refreshAuth: () => void; // permet de relancer la vérification d'auth
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(
  undefined
);

export const AdminAuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isAuth, setIsAuth] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  // Fonction qui vérifie l'auth admin auprès du backend (cookie JWT)
  const checkAuth = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const ok = await checkAdminAuth(); // Appel API : /auth/me
      setIsAuth(ok);
      if (ok) {
        console.log("[AdminAuth] Auth OK (cookie présent)");
      } else {
        console.log("[AdminAuth] Auth FAIL (pas de cookie ou 401)");
      }
    } catch (e) {
      setIsAuth(false);
      setError("Erreur réseau");
      console.log("[AdminAuth] Erreur réseau", e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Fournit l'état d'auth et la fonction de refresh à tous les enfants
  return (
    <AdminAuthContext.Provider
      value={{ isAuth, isLoading, error, refreshAuth: checkAuth }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
};

//Permet d'accéder à l'état d'auth admin dans tout le frontend
export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext);
  if (!ctx)
    throw new Error("useAdminAuth must be used within AdminAuthProvider");
  return ctx;
}
