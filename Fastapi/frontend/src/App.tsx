import { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import AdminPage from "./pages/AdminPage";
import ChatbotPage from "./pages/ChatbotPage";
import { initSession } from "./api/chatApi";

function App() {
  useEffect(() => {
    initSession();
  }, []);
  return (
    <Router>
      <div className="app-nav-buttons">
        <Link to="/admin">
          <button className="app-nav-btn app-nav-btn-admin">Admin</button>
        </Link>
        <Link to="/chatbot" className="app-nav-link-chatbot">
          <button className="app-nav-btn app-nav-btn-chatbot">Chatbot</button>
        </Link>
      </div>
      <Routes>
        <Route path="/" element={<ChatbotPage />} />
        <Route path="/chatbot" element={<ChatbotPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  );
}

export default App;
