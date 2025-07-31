// ========================================================
// Contexte React pour gérer l'état du scraping de manière globale
// Permet de persister les barres de progression entre les pages
// ========================================================

import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { 
    fetchScrapingProgress, 
    fetchVectorizationProgress, 
    resetScrapingProgress,
    fetchLastScrapingSummary 
} from '../api/scrapingApi';
import { fetchCorpusVectorizationProgress } from '../api/corpusApi';
import type { ProgressInfo } from '../api/scrapingApi';

interface ProgressState {
    [siteName: string]: ProgressInfo;
}

interface ScrapingContextType {
    // États du scraping
    isScraping: boolean;
    isVectorizing: boolean;
    isCorpusVectorizing: boolean;
    progress: ProgressState;
    vectorizationProgress?: ProgressInfo;
    corpusVectorizationProgress?: ProgressInfo;
    selectedSites: number[];
    
    // Actions
    setIsScraping: (value: boolean) => void;
    setIsVectorizing: (value: boolean) => void;
    setIsCorpusVectorizing: (value: boolean) => void;
    setProgress: (value: ProgressState | ((prev: ProgressState) => ProgressState)) => void;
    setVectorizationProgress: (value?: ProgressInfo) => void;
    setCorpusVectorizationProgress: (value?: ProgressInfo) => void;
    setSelectedSites: (value: number[]) => void;
    
    // Fonctions utilitaires
    startScraping: (siteNames: string[], siteIds: number[]) => void;
    stopScraping: () => void;
    startVectorization: () => void;
    stopVectorization: () => void;
    startCorpusVectorization: () => void;
    stopCorpusVectorization: () => void;
}

const ScrapingContext = createContext<ScrapingContextType | undefined>(undefined);

export const useScrapingContext = () => {
    const context = useContext(ScrapingContext);
    if (!context) {
        throw new Error('useScrapingContext must be used within a ScrapingProvider');
    }
    return context;
};

export const ScrapingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    // États globaux
    const [isScraping, setIsScraping] = useState(false);
    const [isVectorizing, setIsVectorizing] = useState(false);
    const [isCorpusVectorizing, setIsCorpusVectorizing] = useState(false);
    const [progress, setProgress] = useState<ProgressState>({});
    const [vectorizationProgress, setVectorizationProgress] = useState<ProgressInfo>();
    const [corpusVectorizationProgress, setCorpusVectorizationProgress] = useState<ProgressInfo>();
    const [selectedSites, setSelectedSites] = useState<number[]>([]);
    
    // Refs pour éviter les alertes en double
    const vectorizationCompleteRef = useRef(false);
    const corpusVectorizationCompleteRef = useRef(false);
    const scrapingCompleteRef = useRef(false);

    // Fonction pour démarrer le scraping
    const startScraping = useCallback((siteNames: string[], siteIds: number[]) => {
        setIsScraping(true);
        setSelectedSites(siteIds);
        setProgress({});
        scrapingCompleteRef.current = false;
        
        // Sauvegarder dans localStorage pour la persistance
        localStorage.setItem('scrapingActive', 'true');
        localStorage.setItem('scrapingSites', JSON.stringify(siteNames));
        localStorage.setItem('selectedSiteIds', JSON.stringify(siteIds));
    }, []);

    // Fonction pour arrêter le scraping
    const stopScraping = useCallback(async () => {
        setIsScraping(false);
        setProgress({});
        setSelectedSites([]);
        
        // Nettoyer localStorage
        localStorage.removeItem('scrapingActive');
        localStorage.removeItem('scrapingSites');
        localStorage.removeItem('selectedSiteIds');
        
        // Afficher le résumé si pas encore fait
        if (!scrapingCompleteRef.current) {
            scrapingCompleteRef.current = true;
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
                alert("Scraping terminé avec succès !");
            }
        }
    }, []);

    // Fonction pour démarrer la vectorisation
    const startVectorization = useCallback(() => {
        setIsVectorizing(true);
        setVectorizationProgress(undefined);
        vectorizationCompleteRef.current = false;
        
        localStorage.setItem('vectorizationActive', 'true');
    }, []);

    // Fonction pour arrêter la vectorisation
    const stopVectorization = useCallback(() => {
        setIsVectorizing(false);
        setVectorizationProgress(undefined);
        
        localStorage.removeItem('vectorizationActive');
        
        if (!vectorizationCompleteRef.current) {
            vectorizationCompleteRef.current = true;
            alert("Vectorisation terminée !");
        }
    }, []);

    // Fonction pour démarrer la vectorisation corpus
    const startCorpusVectorization = useCallback(() => {
        setIsCorpusVectorizing(true);
        setCorpusVectorizationProgress(undefined);
        corpusVectorizationCompleteRef.current = false;

        localStorage.setItem('corpusVectorizationActive', 'true');
    }, []);

    // Fonction pour arrêter la vectorisation corpus
    const stopCorpusVectorization = useCallback(() => {
        setIsCorpusVectorizing(false);
        setCorpusVectorizationProgress(undefined);

        localStorage.removeItem('corpusVectorizationActive');

        if (!corpusVectorizationCompleteRef.current) {
            corpusVectorizationCompleteRef.current = true;
            alert("Vectorisation du corpus terminée !");
        }
    }, []);

    // Polling pour le scraping
    useEffect(() => {
        if (!isScraping) return;

        const interval = setInterval(async () => {
            const scrapingSitesJson = localStorage.getItem('scrapingSites');
            const scrapingSites = scrapingSitesJson ? JSON.parse(scrapingSitesJson) : [];

            if (scrapingSites.length === 0) {
                stopScraping();
                return;
            }

            const currentProgress: ProgressState = {};
            let hasActiveProgress = false;
            let foundFiles = 0;

            for (const siteName of scrapingSites) {
                try {
                    const prog = await fetchScrapingProgress(siteName);
                    foundFiles++;
                    currentProgress[siteName] = prog;
                    
                    if (prog.current < prog.total || !prog.status.toLowerCase().includes("terminé")) {
                        hasActiveProgress = true;
                    }
                } catch (err: any) {
                    if (err.message?.includes('404')) {
                        hasActiveProgress = true; // Fichier pas encore créé
                    }
                }
            }

            setProgress(currentProgress);

            // Si tous terminés
            if (!hasActiveProgress && foundFiles > 0) {
                try {
                    await resetScrapingProgress(scrapingSites);
                } catch (err) {
                    console.error("Erreur nettoyage progression:", err);
                }
                stopScraping();
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isScraping, stopScraping]);

    // Polling pour la vectorisation
    useEffect(() => {
        if (!isVectorizing) return;

        const interval = setInterval(async () => {
            try {
                const prog = await fetchVectorizationProgress();
                setVectorizationProgress(prog);

                if (prog.current >= prog.total && prog.status.toLowerCase().includes("terminée")) {
                    stopVectorization();
                }
            } catch (err: any) {
                if (!err.message?.includes('404')) {
                    stopVectorization();
                }
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isVectorizing, stopVectorization]);

    // Polling pour la vectorisation corpus
    useEffect(() => {
        if (!isCorpusVectorizing) return;

        const interval = setInterval(async () => {
            try {
                const prog = await fetchCorpusVectorizationProgress();
                setCorpusVectorizationProgress(prog);

                if (prog.current >= prog.total && prog.status.toLowerCase().includes("terminée")) {
                    stopCorpusVectorization();
                }
            } catch (err: any) {
                if (!err.message?.includes('404')) {
                    stopCorpusVectorization();
                }
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isCorpusVectorizing, stopCorpusVectorization]);

    // Restaurer l'état au chargement de l'app
    useEffect(() => {
        // Restaurer le scraping
        if (localStorage.getItem('scrapingActive') === 'true') {
            const scrapingSitesJson = localStorage.getItem('scrapingSites');
            const selectedSiteIdsJson = localStorage.getItem('selectedSiteIds');
            
            if (scrapingSitesJson && selectedSiteIdsJson) {
                const siteIds = JSON.parse(selectedSiteIdsJson);
                setIsScraping(true);
                setSelectedSites(siteIds);
                scrapingCompleteRef.current = false;
            }
        }

        // Restaurer la vectorisation
        if (localStorage.getItem('vectorizationActive') === 'true') {
            setIsVectorizing(true);
            vectorizationCompleteRef.current = false;
        }

        // Restaurer la vectorisation corpus
        if (localStorage.getItem('corpusVectorizationActive') === 'true') {
            setIsCorpusVectorizing(true);
            corpusVectorizationCompleteRef.current = false;
        }
    }, []);

    const value: ScrapingContextType = {
        // États
        isScraping,
        isVectorizing,
        isCorpusVectorizing,
        progress,
        vectorizationProgress,
        corpusVectorizationProgress,
        selectedSites,
        
        // Actions
        setIsScraping,
        setIsVectorizing,
        setIsCorpusVectorizing,
        setProgress,
        setVectorizationProgress,
        setCorpusVectorizationProgress,
        setSelectedSites,
        
        // Fonctions utilitaires
        startScraping,
        stopScraping,
        startVectorization,
        stopVectorization,
        startCorpusVectorization,
        stopCorpusVectorization
    };

    return (
        <ScrapingContext.Provider value={value}>
            {children}
        </ScrapingContext.Provider>
    );
};
