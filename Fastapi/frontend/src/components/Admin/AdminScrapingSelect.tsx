// ==============================================================
// Composant AdminScrapingSelect
// Permet aux administrateurs de sélectionner les sites à scraper
// ==============================================================

interface Site {
  id: number;
  name: string;
  url: string;
  lastScraped: string | null;
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
            >
              {site.name}
              <span className="admin-scraping-site-date">
                {site.lastScraped
                  ? `(Dernier scraping : ${site.lastScraped})`
                  : "(Jamais scrappé)"}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </>
  );
}
