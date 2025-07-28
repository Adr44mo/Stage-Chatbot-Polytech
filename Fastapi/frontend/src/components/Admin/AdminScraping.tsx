// ========================================================
// Composant AdminScraping
// Permet aux administrateurs de gérer le scraping de sites
// ========================================================

import { useState, useEffect, useCallback } from "react";
import AdminScrapingSelect from "./AdminScrapingSites";
import AdminScrapingSettings from "./AdminScrapingSettings";
import type { SiteInfo, ProgressInfo } from "../../api/scrapingApi";
import { 
	fetchSiteInfos, fetchSiteNewDocs,
	addSite, suppSite,
	runScraping, resetScrapingProgress, fetchScrapingProgress, fetchLastScrapingSummary,
	runProcessingAndVectorization, resetVectorizationProgress, fetchVectorizationProgress 
} from "../../api/scrapingApi";
import { formatDateFrench } from "../../utils/scrapingUtils";

interface ExtendedSiteInfo extends SiteInfo {
	id: number;
}

interface ProgressState {
	[siteName: string]: ProgressInfo;
}

export default function AdminScraping() {
	// États
	const [sites, setSites] = useState<ExtendedSiteInfo[]>([]);
	const [selectedSites, setSelectedSites] = useState<number[]>([]);
	const [loadingSites, setLoadingSites] = useState(false);
	const [isScraping, setIsScraping] = useState(false);
	const [isVectorizing, setIsVectorizing] = useState(false);
	const [progress, setProgress] = useState<ProgressState>({});
	const [vectorizationProgress, setVectorizationProgress] = useState<ProgressInfo>();
	const [showAdvanced, setShowAdvanced] = useState(false);

	const allSelected = selectedSites.length === sites.length && sites.length > 0;

	// Utilitaires de transformation
	const transformSiteInfo = useCallback((site: SiteInfo, index: number): ExtendedSiteInfo => ({
		id: index + 1,
		name: site.name,
		url: site.url,
		lastScraped: formatDateFrench(site.lastScraped),
		newDocs: undefined,
	}), []);

	const updateSitesWithNewDocs = useCallback(async () => {
		if (sites.length === 0) return;

		try {
			const newDocsCounts = await fetchSiteNewDocs();
			setSites(prevSites =>
				prevSites.map(site => {
					const found = newDocsCounts.find(nd => nd.name === site.name);
					return { ...site, newDocs: found?.newDocs ?? 0};
				})
			);
		} catch (err) {
			console.error("Erreur lors de la récupération des nouveaux documents :", err);
		}
	}, [sites.length]);

	// Chargement initial des sites
	const loadSites = useCallback(async () => {
		setLoadingSites(true);
		try {
			const data = await fetchSiteInfos();
			const formattedSites = data.map(transformSiteInfo);
			setSites(formattedSites);
		} catch (err) {
			console.error("Erreur lors de la récupération des sites :", err);
		} finally {
			setLoadingSites(false);
		}
	}, [transformSiteInfo]);

	//Polling de progression du scraping
	const pollScrapingProgress = useCallback(() => {
		if (!isScraping) return;

		const interval = setInterval(async () => {
			const selectedSitesList = sites.filter(site => selectedSites.includes(site.id));

			for (const site of selectedSitesList) {
				try {
					const prog = await fetchScrapingProgress(site.name);
					setProgress(prev => ({ ...prev, [site.name]: prog}));
				} catch (err) {
					console.error(`Erreur progression ${site.name} :`, err);
				}
			}
		}, 1000);

		return () => clearInterval(interval);
	}, [isScraping, sites, selectedSites]);

	// Polling de progression de vectorisation
	const pollVectorizationProgress = useCallback(() => {
		if (!isVectorizing) return;

		const interval = setInterval(async () => {
			try {
				const prog = await fetchVectorizationProgress();
				setVectorizationProgress(prog);

				if (isVectorizing && prog.current === prog.total && prog.status.includes("terminée") && prog.current === 100) {
					setIsVectorizing(false);
					alert("Vectorisation terminée !");
				}
			} catch (err) {
				console.error("Erreur récupération progression vectorisation :", err);
				setIsVectorizing(false); // On arrête le polling en cas d'erreur
			}
		}, 1000);

		return () => clearInterval(interval);
	}, [isVectorizing]);

	// Fonction utilitaire pour afficher le résumé de scraping
	const showScrapingSummary = useCallback(async () => {
		try {
			const summary = await fetchLastScrapingSummary();
			const message = `Scraping terminé avec succès !\n\n` +
				`Résumé :\n` +
				`- Site(s) scrappé(s) : ${summary.sitesScraped.join(", ")}\n` +
				`- Total nouveaux documents : ${summary.totalNewDocuments}\n\n` +
				`Détails par site :\n` +
				Object.entries(summary.detailsBySite)
					.map(([site, count]) => `- ${site} : ${count} nouveau${count > 1 ? "x" : ""} document${count > 1 ? "s" : ""}`)
					.join("\n");

			alert(message);
		} catch (err) {
			console.warn("Impossible de récupérer le résumé de scraping :", err);
			alert("Scraping terminé avec succès !");
		}
	}, []);

	// Gestionnaires d'événements
	const handleCheckbox = useCallback((id: number) => {
		setSelectedSites(prev => 
			prev.includes(id) ? prev.filter(sid => sid !== id) : [...prev, id]
		);
	}, []);

	const handleSelectAll = useCallback(() => {
		setSelectedSites(allSelected ? [] : sites.map(site => site.id));
	}, [allSelected, sites]);

	const handleScrape = useCallback(async () => {
		const selectedSiteNames = sites
			.filter(site => selectedSites.includes(site.id))
			.map(site => site.name);

		try {
			await resetScrapingProgress(selectedSiteNames);
			setIsScraping(true);

			const result = await runScraping(selectedSiteNames);
			console.log("[✅ Scraping lancé] :", result.message);

			await loadSites(); // Recharge les sites après scraping
			await updateSitesWithNewDocs();
			await resetScrapingProgress(selectedSiteNames);
			await showScrapingSummary();
			
		} catch (err: any) {
			console.error("Erreur scraping :", err.message);
			alert("Erreur lors du scraping : " + err.message);
		} finally {
			setIsScraping(false);
			setProgress({}); // Réinitialise la progression
			setSelectedSites([]); // Réinitialise la sélection
		}
	}, [sites, selectedSites, updateSitesWithNewDocs, showScrapingSummary]);

	const handleVectorization = useCallback(async () => {
		try {
			await resetVectorizationProgress();
			setIsVectorizing(true);
			await runProcessingAndVectorization();
		} catch (err: any) {
			console.error("Erreur vectorisation :", err.message);
			alert("Erreur pendant la vectorisation : " + err.message);
		}
	}, []);

	const handleAddSite = useCallback(async (name: string, url: string) => {
		try {
			await addSite(name, url);
			await loadSites(); // Recharge les sites après ajout
		} catch (err) {
			console.error("Erreur lors de l'ajout du site :", err);
		}
	}, [loadSites]);

	const handleDeleteSite = useCallback(async (id: number) => {
		const siteToDelete = sites.find(s => s.id === id);
		if (!siteToDelete) return;

		if (window.confirm(`Supprimer le site "${siteToDelete.name}" ?`)) {
			try {
				await suppSite(siteToDelete.name);

				// Recharge les sites après déletion
				setSites(prevSites => {
					const filteredSites = prevSites.filter(site => site.name !== siteToDelete.name);
					return filteredSites.map((site, index) => ({
						...site,
						id: index + 1
					}));
				});
				setSelectedSites(prev => {
					return prev
						.filter(sid => sid !== id)
						.map(sid => sid > id ? sid - 1 : sid);
				});

			} catch (err) {
				console.error("Erreur lors de la suppression du site :", err);
				await loadSites();
			}
		}
	}, [sites]);

	const toggleAdvanced = useCallback(() => {
		setShowAdvanced(prev => !prev);
	}, []);

	// Effets
	useEffect(() => {
		loadSites();
	}, [loadSites]);

	useEffect(() => {
		updateSitesWithNewDocs();
	}, [updateSitesWithNewDocs]);

	useEffect(() => {
		return pollScrapingProgress();
	}, [pollScrapingProgress]);

	useEffect(() => {
		return pollVectorizationProgress();
	}, [pollVectorizationProgress]);


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
						siteProgress={progress}
						isScraping={isScraping}
					/>
				)}

				<div className="admin-scraping-actions">
					<button
						className="admin-scraping-btn admin-scraping-launch-btn"
						disabled={selectedSites.length === 0 || isScraping}
						onClick={handleScrape}
					>
						{isScraping ? "Scraping en cours..." : "Lancer le scraping"}
					</button>

					<button
						className="admin-scraping-btn admin-scraping-launch-btn"
						onClick={handleVectorization}
						disabled={isVectorizing}
					>
						{isVectorizing ? "Vectorisation en cours..." : "Lancer la vectorisation"}
					</button>

					{isVectorizing && vectorizationProgress && (
						<div>
							<progress
								value={vectorizationProgress.current}
								max={vectorizationProgress.total}
								className="admin-vectorization-progress"
							/>
							<span>{vectorizationProgress.status}</span>
						</div>
					)}
				</div>

				<div className="admin-scraping-advanced-toggle-wrapper">
					<button
						className="admin-scraping-advanced-toggle"
						type="button"
						onClick={toggleAdvanced}
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
