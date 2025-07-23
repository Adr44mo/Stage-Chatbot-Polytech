// ==============================================================
// Composant AdminScrapingSelect
// Permet aux administrateurs de sélectionner les sites à scraper
// ==============================================================

import { memo } from "react"
import type { ProgressInfo } from "../../api/scrapingApi";

// Types locaux
interface ExtendedSiteInfo {
  id: number;
  name: string;
  url: string;
  lastScraped: string | null;
  newDocs?: number;
}

interface ProgressState {
    [siteName: string]: ProgressInfo;
}

interface AdminScrapingSelectProps {
  sites: ExtendedSiteInfo[];
  selectedSites: number[];
  onSelectSite: (id: number) => void;
  allSelected: boolean;
  onSelectAll: () => void;
  siteProgress: ProgressState;
  isScraping: boolean;
}

//Composant pour afficher le status des nouveaux documents
const NewDocsStatus = memo(({ newDocs }: { newDocs?: number }) => {
  if (newDocs === undefined) {
    return (
      <span className="admin-scraping-newdocs loading" style={{ fontWeight: 500, fontSize: "0.9rem" }}>
        Chargement...
      </span>
    );
  }

  return (
    <span 
      className={`admin-scraping-newdocs ${newDocs > 0 ? "has-new" : "no-new"}`} 
      style={{ fontWeight: 500, fontSize: "0.9rem" }}
    >
      {newDocs > 0 
        ? `${newDocs} nouveau${newDocs > 1 ? "x" : ""}` 
        : "Aucun nouveau"
      }
    </span>
  );
});

// Composant pour afficher la progression du scraping
const ScrapingProgress = memo(({ 
  siteName, 
  siteProgress 
}: { 
  siteName: string; 
  siteProgress: ProgressState;
}) => {
  const progress = siteProgress[siteName];

  if (!progress) return null;

  return(
    <div style={{ flex: 1, marginLeft: "1rem" }}>
      <progress
          value={progress.current}
          max={progress.total}
          className="admin-scraping-progress"
      />
      <span className="admin-scraping-progress-status">
          {progress.status}
      </span>
  </div>
  );
});

// Composant pour un élément de site individuel
const SiteItem = memo(({
  site,
  isSelected,
  isScraping,
  siteProgress,
  onSelectSite
}: {
  site: ExtendedSiteInfo;
  isSelected: boolean;
  isScraping: boolean;
  siteProgress: ProgressState;
  onSelectSite: (id: number) => void;
}) => {
  const handleSiteSelection = () => onSelectSite(site.id);

  return (
    <li key={site.id} className="admin-scraping-site-item">
      <input
        type="checkbox"
        checked={isSelected}
        onChange={handleSiteSelection}
        id={`site-${site.id}`}
        className="admin-scraping-checkbox"
        disabled={isScraping}
      />
      <label
        htmlFor={`site-${site.id}`}
        className="admin-scraping-checkbox-label admin-scraping-site-label"
        style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center",
          width: "100%"
        }}
      >
      <div style={{ 
        display: "flex", 
        alignItems: "center", 
        flex: 1,
        minWidth: 0 // Pour permettre la troncature du texte
      }}>
        <span style={{ fontWeight: 500 }}>
          {site.name}
        </span>
          
        <span 
          className="admin-scraping-site-date" 
        >
          {site.lastScraped 
            ? `(Dernier scraping : ${site.lastScraped})` 
            : "(Jamais scrappé)"
          }
        </span>

        {isScraping && isSelected && (
          <ScrapingProgress 
            siteName={site.name}
            siteProgress={siteProgress}
          />
        )}
        </div>
        <NewDocsStatus newDocs={site.newDocs} />
      </label>
    </li>
  );
});


// Composant principal
const AdminScrapingSelect = memo(({
  sites,
  selectedSites,
  onSelectSite,
  allSelected,
  onSelectAll,
  siteProgress,
  isScraping,
}: AdminScrapingSelectProps) => {
  return (
    <div className="admin-scraping-selection">
      {/* Case "Sélectionner tout" */}
      <div className="admin-scraping-selectall">
        <label className="admin-scraping-checkbox-label">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={onSelectAll}
            className="admin-scraping-checkbox"
            disabled={isScraping}
          />
          Sélectionner tout
        </label>
      </div>

      {/* Liste des sites */}
      <ul className="admin-scraping-sites-list">
        {sites.map((site) => (
          <SiteItem
            key={site.id}
            site={site}
            isSelected={selectedSites.includes(site.id)}
            isScraping={isScraping}
            siteProgress={siteProgress}
            onSelectSite={onSelectSite}
          />
        ))}
      </ul>
    </div>
  );
});


// Noms d'affichage pour le débogage 
NewDocsStatus.displayName = "NewDocsStatus";
ScrapingProgress.displayName = "ScrapingProgress";
SiteItem.displayName = "SiteItem";
AdminScrapingSelect.displayName = "AdminScrapingSelect";

export default AdminScrapingSelect;