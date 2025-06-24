// ========================================================
// Composant AdminScraping
// Permet aux administrateurs de gérer le scraping de sites
// ========================================================

import { useState } from "react";
import AdminScrapingSelect from "./AdminScrapingSelect";
import AdminScrapingSettings from "./AdminScrapingSettings";

const INITIAL_SITES = [
	{ id: 1, name: "Site 1", url: "https://site1.com", lastScraped: "22/06/2025 14:12" },
	{ id: 2, name: "Site 2", url: "https://site2.com", lastScraped: "21/06/2025 09:30" },
	{ id: 3, name: "Site 3", url: "https://site3.com", lastScraped: null },
];

export default function AdminScraping() {
	const [sites, setSites] = useState(INITIAL_SITES);
	const [selectedSites, setSelectedSites] = useState<number[]>([]);
	const [loading, setLoading] = useState(false);
	const [showAdvanced, setShowAdvanced] = useState(false);

	const allSelected = selectedSites.length === sites.length && sites.length > 0;

	const handleCheckbox = (id: number) => {
		setSelectedSites((prev) =>
			prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id]
		);
	};

	const handleSelectAll = () => {
		setSelectedSites(allSelected ? [] : sites.map((site) => site.id));
	};

	const handleScrape = () => {
		setLoading(true);
		setTimeout(() => setLoading(false), 1500);
	};

	const handleAddSite = (name: string, url: string) => {
		setSites((prev) => [
			...prev,
			{
				id: prev.length ? Math.max(...prev.map((s) => s.id)) + 1 : 1,
				name,
				url,
				lastScraped: null,
			},
		]);
	};

	const handleDeleteSite = (id: number) => {
		if (window.confirm("Supprimer ce site ?")) {
			setSites((prev) => prev.filter((site) => site.id !== id));
			setSelectedSites((prev) => prev.filter((sid) => sid !== id));
		}
	};

	return (
		<div className="admin-scraping-section">
			<h2 className="admin-page-subtitle">Lancer un scraping</h2>
			<div className="admin-scraping-container">
				<p>Sélectionnez les sites à scraper :</p>
				<AdminScrapingSelect
					sites={sites}
					selectedSites={selectedSites}
					onSelectSite={handleCheckbox}
					allSelected={allSelected}
					onSelectAll={handleSelectAll}
				/>
				<button
					className="admin-scraping-btn admin-scraping-launch-btn"
					disabled={selectedSites.length === 0 || loading}
					onClick={handleScrape}
				>
					{loading ? "Scraping en cours..." : "Lancer le scraping"}
				</button>
				<div className="admin-scraping-advanced-toggle-wrapper">
					<button
						className="admin-scraping-advanced-toggle"
						type="button"
						onClick={() => setShowAdvanced((v) => !v)}
					>
						{showAdvanced ? "Fermer les options avancées" : "Options avancées (gérer les sites)"}
					</button>
				</div>
				{showAdvanced && (
					<AdminScrapingSettings
						sites={sites}
						onAddSite={handleAddSite}
						onDeleteSite={handleDeleteSite}
					/>
				)}
			</div>
		</div>
	);
}
