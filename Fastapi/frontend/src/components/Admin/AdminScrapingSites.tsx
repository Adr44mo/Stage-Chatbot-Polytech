// ==============================================================
// Composant AdminScrapingSelect
// Permet aux administrateurs de sélectionner les sites à scraper
// ==============================================================

interface Site {
  id: number;
  name: string;
  url: string;
  lastScraped: string | null;
  newDocs?: number;
}

interface AdminScrapingSelectProps {
  sites: Site[];
  selectedSites: number[];
  onSelectSite: (id: number) => void;
  allSelected: boolean;
  onSelectAll: () => void;
}

export default function AdminScrapingSelect({
  sites,
  selectedSites,
  onSelectSite,
  allSelected,
  onSelectAll,
}: AdminScrapingSelectProps) {
  return (
    <>
      <div className="admin-scraping-selectall">
        <label className="admin-scraping-checkbox-label">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={onSelectAll}
            className="admin-scraping-checkbox"
          />
          Sélectionner tout
        </label>
      </div>
      <ul className="admin-scraping-sites-list">
        {sites.map((site) => (
          <li key={site.id} className="admin-scraping-site-item">
            <input
              type="checkbox"
              checked={selectedSites.includes(site.id)}
              onChange={() => onSelectSite(site.id)}
              id={`site-${site.id}`}
              className="admin-scraping-checkbox"
            />
            <label
              htmlFor={`site-${site.id}`}
              className="admin-scraping-checkbox-label admin-scraping-site-label"
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              <div>
                {site.name}
                <span className="admin-scraping-site-date" style={{ marginLeft: 8, fontSize: "0.85rem", color: "#666" }}>
                  {site.lastScraped ? `(Dernier scraping : ${site.lastScraped})` : "(Jamais scrappé)"}
                </span>
              </div>

              {site.newDocs === undefined ? (
                <span className="admin-scraping-newdocs loading" style={{ fontWeight: 500, fontSize: "0.9rem" }}>
                  Chargement...
                </span>
              ) : (
                <span
                  className={`admin-scraping-newdocs ${site.newDocs > 0 ? "has-new" : "no-new"}`}
                  style={{ fontWeight: 500, fontSize: "0.9rem" }}
                >
                  {site.newDocs > 0
                    ? `${site.newDocs} nouveau${site.newDocs > 1 ? "x" : ""}`
                    : "Aucun nouveau"}
                </span>
              )}
            </label>
          </li>
        ))}
      </ul>
    </>
  );
}
