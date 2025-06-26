// ================================
// Page d'administration principale
// ================================

import { useState } from "react";
import AdminScraping from "../components/Admin/AdminScraping";
import AdminUploadPDF from "../components/Admin/AdminUploadPDF";
import AdminLogoutButton from "../components/Admin/AdminLogoutButton";

export default function AdminPage() {
  // État local pour savoir quelle section afficher ("corpus" ou "scraping")
  const [section, setSection] = useState<"corpus" | "scraping">("corpus");

  return (
    <div className="admin-page-layout">
      {/* Barre de navigation admin pour changer de section */}
      <aside className="admin-sidebar">
        <nav>
          <ul>
            <li>
              {/* Section corpus PDF */}
              <button
                className={
                  section === "corpus"
                    ? "admin-sidebar-btn active"
                    : "admin-sidebar-btn"
                }
                onClick={() => setSection("corpus")}
              >
                Corpus PDF
              </button>
            </li>
            <li>
              {/* Section scraping web */}
              <button
                className={
                  section === "scraping"
                    ? "admin-sidebar-btn active"
                    : "admin-sidebar-btn"
                }
                onClick={() => setSection("scraping")}
              >
                Scraping Web
              </button>
            </li>
          </ul>
        </nav>
        {/* Bouton de déconnexion */}
        <div className="admin-logout-btn-wrapper">
          <AdminLogoutButton />
        </div>
      </aside>
      {/* On affichage le contenu selon la section choisie */}
      <main className="admin-main-content">
        {section === "corpus" ? <AdminUploadPDF /> : <AdminScraping />}
      </main>
    </div>
  );
}
