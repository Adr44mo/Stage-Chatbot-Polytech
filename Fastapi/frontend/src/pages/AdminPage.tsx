// ================================
// Page d'administration principale
// ================================

import { useState } from "react";
import AdminCorpus from "../components/Admin/AdminCorpus";
import AdminScraping from "../components/Admin/AdminScraping";
import AdminStatistics from "../components/Admin/AdminStatistics";
import AdminMaintenance from "../components/Admin/AdminMaintenance";
import AdminLogoutButton from "../components/Admin/AdminLogoutButton";

export default function AdminPage() {
  // État local pour savoir quelle section afficher
  const [section, setSection] = useState<"corpus" | "scraping" | "statistics" | "maintenance">(
    "corpus"
  );

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

            <li>
              {/* Section statistiques */}
              <button
                className={
                  section === "statistics"
                    ? "admin-sidebar-btn active"
                    : "admin-sidebar-btn"
                }
                onClick={() => setSection("statistics")}
              >
                Statistiques
              </button>
            </li>

            <li>
              {/* Section maintenance */}
              <button
                className={
                  section === "maintenance"
                    ? "admin-sidebar-btn active"
                    : "admin-sidebar-btn"
                }
                onClick={() => setSection("maintenance")}
              >
                Maintenance
              </button>
            </li>
          </ul>
        </nav>

        {/* Bouton de déconnexion */}
        <div style={{ marginTop: "32px" }}>
          <AdminLogoutButton />
        </div>
      </aside>
      
      {/* On affichage le contenu selon la section choisie */}
      <main className="admin-main-content">
        {section === "corpus" && <AdminCorpus />}
        {section === "scraping" && <AdminScraping />}
        {section === "statistics" && <AdminStatistics />}
        {section === "maintenance" && <AdminMaintenance />}
      </main>
    </div>
  );
}
