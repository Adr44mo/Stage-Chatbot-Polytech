// =====================================================================
// Composant AdminScrapingSettings
// Permet aux administrateurs d'ajouter et supprimer des sites à scraper
// =====================================================================

import { useState } from "react";

interface Site {
  id: number;
  name: string;
  url: string;
  lastScraped: string | null;
}

interface AdminScrapingSettingsProps {
  sites: Site[];
  onAddSite: (name: string, url: string) => void;
  onDeleteSite: (id: number) => void;
}

export default function AdminScrapingSettings({
  sites,
  onAddSite,
  onDeleteSite,
}: AdminScrapingSettingsProps) {
  const [newSiteName, setNewSiteName] = useState("");
  const [newSiteUrl, setNewSiteUrl] = useState("");
  const [addError, setAddError] = useState("");

  const handleAddSite = (e: React.FormEvent) => {
    e.preventDefault();
    setAddError("");
    if (!newSiteName.trim() || !newSiteUrl.trim()) {
      setAddError("Nom et URL obligatoires");
      return;
    }
    try {
      new URL(newSiteUrl);
    } catch {
      setAddError("URL invalide");
      return;
    }
    onAddSite(newSiteName, newSiteUrl);
    setNewSiteName("");
    setNewSiteUrl("");
  };

  return (
    <div className="admin-scraping-advanced-block">
      <h3 className="admin-scraping-advanced-title">Ajouter un site</h3>
      <form className="admin-scraping-add-form" onSubmit={handleAddSite}>
        <input
          className="admin-scraping-add-input"
          type="text"
          placeholder="Nom du site"
          value={newSiteName}
          onChange={(e) => setNewSiteName(e.target.value)}
          required
        />
        <input
          className="admin-scraping-add-input"
          type="url"
          placeholder="URL du site (https://...)"
          value={newSiteUrl}
          onChange={(e) => setNewSiteUrl(e.target.value)}
          required
        />
        <button className="admin-corpus-add-btn" type="submit">
          Ajouter
        </button>
        {addError && <div className="admin-scraping-error">{addError}</div>}
      </form>
      <h3 className="admin-scraping-advanced-title">Supprimer un site</h3>
      <ul className="admin-scraping-advanced-sites-list">
        {sites.map((site) => (
          <li key={site.id} className="admin-scraping-advanced-site-item">
            <span>
              {site.name} <span className="admin-scraping-site-url">({site.url})</span>
            </span>
            <button
              className="admin-scraping-delete-btn"
              type="button"
              onClick={() => onDeleteSite(site.id)}
            >
              Supprimer
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
