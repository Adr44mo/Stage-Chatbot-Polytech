// ========================================================
// Composant AdminScraping
// Permet aux administrateurs de gérer le scraping de sites
// ========================================================

import { useState, useEffect, useCallback, useRef } from "react";
import AdminScrapingSelect from "./AdminScrapingSites";
import AdminScrapingSettings from "./AdminScrapingSettings";
import { useScrapingContext } from "../../contexts/ScrapingContext";
import type { SiteInfo } from "../../api/scrapingApi";
import { 
	fetchSiteInfos, fetchSiteNewDocs,
	addSite, suppSite,
	runScraping, resetScrapingProgress,
	runProcessingAndVectorization, resetVectorizationProgress
} from "../../api/scrapingApi";
import { formatDateFrench } from "../../utils/scrapingUtils";

interface ExtendedSiteInfo extends SiteInfo {
	id: number;
}

export default function AdminScraping() {
	// États locaux (spécifiques à cette page)
	const [sites, setSites] = useState<ExtendedSiteInfo[]>([]);
	const [loadingSites, setLoadingSites] = useState(false);
	const [showAdvanced, setShowAdvanced] = useState(false);

	// États globaux du contexte
	const {
		isScraping,
		isVectorizing,
		isCorpusVectorizing,
		progress,
		vectorizationProgress,
		selectedSites,
		setSelectedSites,
		startScraping,
		stopScraping,
		startVectorization,
		stopVectorization
	} = useScrapingContext();

	const vectorizationCompleteRef = useRef(false);
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

	// Gestionnaires d'événements
	const handleCheckbox = useCallback((id: number) => {
		const newSelectedSites = selectedSites.includes(id) 
			? selectedSites.filter(sid => sid !== id) 
			: [...selectedSites, id];
		setSelectedSites(newSelectedSites);
	}, [selectedSites, setSelectedSites]);

	const handleSelectAll = useCallback(() => {
		setSelectedSites(allSelected ? [] : sites.map(site => site.id));
	}, [allSelected, sites, setSelectedSites]);

	const handleScrape = useCallback(async () => {
		// Filtrer les sites sélectionnés qui ont des nouveaux documents OU un statut inconnu
		const sitesToScrape = sites
			.filter(site => selectedSites.includes(site.id))
			.filter(site => {
				// Scraper si :
				// - newDocs > 0 (nouveaux documents détectés)
				// - newDocs === -1 (sitemap inaccessible, mais fallback crawler possible)
				// - newDocs === undefined (statut inconnu, tentative de scraping)
				return site.newDocs === undefined || site.newDocs === -1 || (site.newDocs && site.newDocs > 0);
			});

		const selectedSiteNames = sitesToScrape.map(site => site.name);
		const selectedSiteIds = sitesToScrape.map(site => site.id);

		// Vérifier s'il y a des sites à scraper
		if (selectedSiteNames.length === 0) {
			alert("Aucun site sélectionné n'est disponible pour le scraping.\n\nNB: Les sites avec 0 nouveaux documents sont ignorés pour éviter un scraping inutile.");
			return;
		}

		// Informer l'utilisateur des sites qui seront ignorés (seulement ceux avec 0 nouveaux documents)
		const sitesWithoutNewDocs = sites
			.filter(site => selectedSites.includes(site.id))
			.filter(site => site.newDocs === 0);

		if (sitesWithoutNewDocs.length > 0) {
			const ignoredSiteNames = sitesWithoutNewDocs.map(site => site.name).join(', ');
			console.log(`[ℹ️ Sites ignorés] (0 nouveaux documents) : ${ignoredSiteNames}`);
		}

		// Informer l'utilisateur des sites avec statut inconnu qui seront tentés
		const sitesWithUnknownStatus = sitesToScrape.filter(site => 
			site.newDocs === undefined || site.newDocs === -1
		);
		
		if (sitesWithUnknownStatus.length > 0) {
			const unknownSiteNames = sitesWithUnknownStatus.map(site => site.name).join(', ');
			console.log(`[🕷️ Sites avec crawler automatique] : ${unknownSiteNames}`);
		}

		try {
			await resetScrapingProgress(selectedSiteNames);
			
			// Utiliser le contexte pour démarrer le scraping avec les sites filtrés
			startScraping(selectedSiteNames, selectedSiteIds);

			const result = await runScraping(selectedSiteNames);
			console.log(`[✅ Scraping lancé] sur ${selectedSiteNames.length} site(s) :`, result.message);
			
		} catch (err: any) {
			console.error("Erreur scraping :", err.message);
			alert("Erreur lors du scraping : " + err.message);
			stopScraping();
		}
	}, [sites, selectedSites, startScraping, stopScraping]);

	const handleVectorization = useCallback(async () => {
		try {
			await resetVectorizationProgress();
			vectorizationCompleteRef.current = false;
			
			// Utiliser le contexte pour démarrer la vectorisation
			startVectorization();

			await runProcessingAndVectorization();
		} catch (err: any) {
			console.error("Erreur vectorisation :", err.message);
			alert("Erreur pendant la vectorisation : " + err.message);
			stopVectorization();
		}
	}, [startVectorization, stopVectorization]);

	const handleAddSite = useCallback(async (name: string, url: string) => {
		try {
			await addSite(name, url);
			await loadSites(); // Recharge les sites après ajout
		} catch (err) {
			console.error("Erreur lors de l'ajout du site :", err);
			throw err; // Propage l'erreur vers le composant enfant
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
				
				// Mettre à jour les sites sélectionnés
				const newSelectedSites = selectedSites
					.filter(sid => sid !== id)
					.map(sid => sid > id ? sid - 1 : sid);
				setSelectedSites(newSelectedSites);

			} catch (err) {
				console.error("Erreur lors de la suppression du site :", err);
				await loadSites();
			}
		}
	}, [sites, selectedSites, setSelectedSites, loadSites]);

	const toggleAdvanced = useCallback(() => {
		setShowAdvanced(prev => !prev);
	}, []);

	// Effets simplifiés - le contexte gère le polling
	useEffect(() => {
		loadSites();
	}, [loadSites]);

	useEffect(() => {
		updateSitesWithNewDocs();
	}, [updateSitesWithNewDocs]);


	return (
		<div className="admin-scraping-section">
			<h2 className="admin-page-subtitle">Lancer un scraping</h2>
			<div className="admin-scraping-container">
				<h3 className="admin-scraping-title">Sélectionnez les sites à scraper :</h3>

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
						disabled={isVectorizing || isScraping || isCorpusVectorizing}
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
