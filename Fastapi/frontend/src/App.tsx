// ==============================================================================
// App principale
// Gère le routing, l'authentification admin, et la navigation globale du chatbot
// ==============================================================================

import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ChatbotPage from "./pages/ChatbotPage";
import LoginPage from "./pages/LoginPage";
import AdminPage from "./pages/AdminPage";
import ProtectedRoute from "./auth/ProtectedRoute";
import { AdminAuthProvider } from "./auth/AdminAuthContext";
import { initSession } from "./api/chatApi";
import { ScrapingProvider } from "./contexts/ScrapingContext";

function App() {
  // On initialise la session utilisateur au montage de l'app
  useEffect(() => {
    initSession();
  }, []);

  return (
    // On fournit le contexte d'authentification admin à toute l'application
    <ScrapingProvider>
      <AdminAuthProvider>
        <Router>
          {/* Définition des routes principales de l'application */}
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminPage />
                </ProtectedRoute>
              }
            />
            <Route path="/chatbot" element={<ChatbotPage />} />
            <Route path="/" element={<ChatbotPage />} />
          </Routes>
        </Router>
      </AdminAuthProvider>
    </ScrapingProvider>
  );
}

export default App;
