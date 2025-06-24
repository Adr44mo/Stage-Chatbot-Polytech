import { useState } from "react";
import AdminScraping from "../components/Admin/AdminScraping";
import AdminUploadPDF from "../components/Admin/AdminUploadPDF";

export default function AdminPage() {
  const [section, setSection] = useState<"corpus" | "scraping">("corpus");

  return (
    <div className="admin-page-layout">
      <aside className="admin-sidebar">
        <nav>
          <ul>
            <li>
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
      </aside>
      <main className="admin-main-content">
        {section === "corpus" ? <AdminUploadPDF /> : <AdminScraping />}
      </main>
    </div>
  );
}