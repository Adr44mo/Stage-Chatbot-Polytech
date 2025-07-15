// ========================================================
// Composant AdminScraping
// Permet aux administrateurs de gérer le scraping de sites
// ========================================================

import { useState, useEffect } from "react";
import AdminScrapingSelect from "./AdminScrapingSites";
import AdminScrapingSettings from "./AdminScrapingSettings";
import type { SiteInfo } from "../../api/scrapingApi";
import { fetchSiteInfos, fetchSiteNewDocs } from "../../api/scrapingApi";
import { addSite as apiAddSite, suppSite as apiSuppSite } from "../../api/scrapingApi";
import { runScraping } from "../../api/scrapingApi";

/* const INITIAL_SITES = [
	{ id: 1, name: "Site 1", url: "https://site1.com", lastScraped: "22/06/2025 14:12" },
	{ id: 2, name: "Site 2", url: "https://site2.com", lastScraped: "21/06/2025 09:30" },
	{ id: 3, name: "Site 3", url: "https://site3.com", lastScraped: null },
]; */

export default function AdminScraping() {
	//const [sites, setSites] = useState(INITIAL_SITES);
	const [sites, setSites] = useState<({ id: number } & SiteInfo)[]>([]);
	const [selectedSites, setSelectedSites] = useState<number[]>([]);
	const [loading, setLoading] = useState(false);
	const [loadingSites, setLoadingSites] = useState(false);
	const [showAdvanced, setShowAdvanced] = useState(false);

	const allSelected = selectedSites.length === sites.length && sites.length > 0;

	useEffect(() => {
		setLoadingSites(true);

		fetchSiteInfos()
			.then((data) => {
				const formattedSites = data.map((site, index) => ({
					id: index + 1,
					name: site.name,
					url: site.url,
					lastScraped: site.lastScraped,
					newDocs: undefined, // mis à jour ensuite
				}));
				setSites(formattedSites);
			})
			.catch((err) => {
				console.error("Erreur lors de la récupération des sites :", err);
			})
			.finally(() => {
				setLoadingSites(false);
			});
	}, []);

	useEffect(() => {
		if (sites.length === 0) return; // Évite de lancer si pas de sites

		fetchSiteNewDocs()
			.then((newDocsCounts) => {
				setSites((prevSites) => 
					prevSites.map((site) => {
						const found = newDocsCounts.find((nd) => nd.name === site.name);
						return { ...site, newDocs: found ? found.newDocs : 0 };
					})
				);
			})
			.catch((err) => {
				console.error("Erreur lors de la récupération des sites :", err);
			});
	}, [sites.length]);

	const handleCheckbox = (id: number) => {
		setSelectedSites((prev) =>
			prev.includes(id) ? prev.filter((sid) => sid !== id) : [...prev, id]
		);
	};

	const handleSelectAll = () => {
		setSelectedSites(allSelected ? [] : sites.map((site) => site.id));
	};

	const handleScrape = async () => {
		setLoading(true);
		try {
			const selectedSiteNames = sites
				.filter((site) => selectedSites.includes(site.id))
				.map((site) => site.name);

			const result = await runScraping(selectedSiteNames);
			console.log("[✅ Scraping lancé] :", result.message);

			const updatedNewDocs = await fetchSiteNewDocs();
			setSites((prevSites) =>
				prevSites.map((site) => {
					const found = updatedNewDocs.find((nd) => nd.name === site.name);
					return { ...site, newDocs: found ? found.newDocs : 0 };
				})
			);

			alert("Scraping terminé avec succès !");
			
		} catch (err: any) {
			console.error("Erreur scraping :", err.message);
			alert("Erreur lors du scraping : " + err.message);
		} finally {
			setLoading(false);
		}
	};

	const handleAddSite = async (name: string, url: string) => {
		try {
			await apiAddSite(name, url);
			const newSites = await fetchSiteInfos();
			setSites(
				newSites.map((site, index) => ({
					id: index + 1,
					name: site.name,
					url: site.url,
					lastScraped: site.lastScraped,
					newDocs: undefined,
				}))
			);
		} catch(err) {
			console.error("Erreur lors de l'ajout du site :", err);
		}
	};

	const handleDeleteSite = async (id: number) => {
		const siteToDelete = sites.find((s) => s.id ===id);
		if (!siteToDelete) return;

		if (window.confirm(`Supprimer le site "${siteToDelete.name}" ?`)) {
			try {
				await apiSuppSite(siteToDelete.name);
				const updatedSites = await fetchSiteInfos();
				setSites(
					updatedSites.map((site, index) => ({
						id: index + 1,
						name: site.name,
						url: site.url,
						lastScraped: site.lastScraped,
						newDocs: undefined,
					}))
				);
				setSelectedSites((prev) => prev.filter((sid) => sid !== id));
			} catch (err) {
				console.error("Erreur lors de la suppression du site :", err);
			}		
		}
	};

	return (
		<div className="admin-scraping-section">
			<h2 className="admin-page-subtitle">Lancer un scraping</h2>
			<div className="admin-scraping-container">
				<p>Sélectionnez les sites à scraper :</p>
				{loadingSites ? (
					<div style={{ textAlign: "center", padding: "2rem" }}>
						<div className="spinner" />
						<p>Chargement des sites...</p>
					</div>
				) : (
					<AdminScrapingSelect
						sites={sites}
						selectedSites={selectedSites}
						onSelectSite={handleCheckbox}
						allSelected={allSelected}
						onSelectAll={handleSelectAll}
					/>
				)}
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
