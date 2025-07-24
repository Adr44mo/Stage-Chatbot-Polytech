// ==============================================================================
// App principale
// Gère le routing, l'authentification admin, et la navigation globale du chatbot
// ==============================================================================

import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import ChatbotPage from "./pages/ChatbotPage";
import ChatIframePage from "./pages/ChatIframePage";
import LoginPage from "./pages/LoginPage";
import AdminPage from "./pages/AdminPage";
import ProtectedRoute from "./auth/ProtectedRoute";
import { AdminAuthProvider } from "./auth/AdminAuthContext";
import { initSession } from "./api/chatApi";

function App() {
  // On initialise la session utilisateur au montage de l'app
  useEffect(() => {
    initSession();
  }, []);

  return (
    // On fournit le contexte d'authentification admin à toute l'application
    <AdminAuthProvider>
      <Router>
        <div className="app-nav-buttons">
          <Link to="/admin">
            <button className="app-nav-btn app-nav-btn-admin">Admin</button>
          </Link>
          <Link to="/chatbot" className="app-nav-link-chatbot">
            <button className="app-nav-btn app-nav-btn-chatbot">Chatbot</button>
          </Link>
        </div>
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
          <Route path="/iframe" element={<ChatIframePage />} />
          <Route path="/" element={<ChatbotPage />} />
        </Routes>
      </Router>
    </AdminAuthProvider>
  );
}

export default App;
