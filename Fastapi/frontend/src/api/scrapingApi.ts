// ============================================
// Gestionnaire des appels API pour le scraping
// ============================================

import { siteNameToFileName } from "../utils/scrapingUtils";

// Types et interfaces
export interface SiteInfo {
    name: string;
    url:string;
    lastScraped: string | null;
    newDocs?: number;
}

export interface SiteNewDocs {
    name: string;
    url: string;
    newDocs: number;
}

export interface ProgressInfo {
	current: number;
	total: number;
	status: string;
}

export interface ApiResponse {
    status: string;
    message: string;
}

// Utilitaires pour les requêtes
class ApiError extends Error {
    constructor(message: string | any) {
        const errorMessage = typeof message === 'string' ? message : JSON.stringify(message);
        super(errorMessage);
        this.name = 'ApiError';
    }
}

const handleApiResponse = async (response: Response) => {
    if (!response.ok) {
        let errorMessage = `Erreur ${response.status}`;
        try {
            const errorData = await response.json();
            console.log("Données d'erreur reçues:", errorData);
            
            if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
            } else if (typeof errorData.message === 'string') {
                errorMessage = errorData.message;
            } else if (errorData.detail) {
                errorMessage = JSON.stringify(errorData.detail);
            } else {
                errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
            }
        } catch {
            errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
        }
        throw new ApiError(errorMessage);
    }
    return response;
};


// ========================================================
// GESTION DES SITES
// ========================================================

export const fetchSiteInfos = async (): Promise<SiteInfo[]> => {
    const response = await fetch("/scraping/site_infos");
    await handleApiResponse(response);
    return response.json();
};

export const fetchSiteNewDocs = async (): Promise<SiteNewDocs[]> => {
    const response = await fetch("/scraping/site_new_docs");
    await handleApiResponse(response);
    return response.json();
};

export const addSite = async (name: string, url: string): Promise<ApiResponse> => {
    const response = await fetch("/scraping/add_site", {
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({ siteName: name, url}),
    });
    await handleApiResponse(response);
    return response.json();
};

export const suppSite = async (name: string): Promise<ApiResponse> => {
    const response = await fetch("/scraping/supp_site", {
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({ siteName: name }),
    });
    await handleApiResponse(response);
    return response.json();
};


// ========================================================
// SCRAPING
// ========================================================

export const runScraping = async (siteNames: string[]): Promise<ApiResponse> => {
    const response = await fetch("/scraping/scraping", {
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify(siteNames),
    });
    await handleApiResponse(response);
    return response.json();
};

export const fetchScrapingProgress = async (siteName: string): Promise<ProgressInfo> => {
    const fileName = siteNameToFileName(siteName);
    const response = await fetch(`/scraping/progress/${encodeURIComponent(fileName)}`);

    if (response.status === 404) {
        // Fichier de progression absent : scraping pas commencé ou déjà fini
        return { current: 0, total: 1, status: "" };
    }
    
    await handleApiResponse(response);
    return response.json();
};

export const resetScrapingProgress = async (siteNames: string[]): Promise<void> => {
    const fileNames = siteNames.map(siteNameToFileName);

    const resetPromises = fileNames.map(async (fileName) => {
        const response = await fetch(`/scraping/reset_progress/${encodeURIComponent(fileName)}`, {
            method: "POST",
        });
        await handleApiResponse(response);
    });

    await Promise.all(resetPromises);
};


// ========================================================
// TRAITEMENT ET VECTORISATION
// ========================================================

export const runProcessing = async (): Promise<ApiResponse> => {
    const response = await fetch("/scraping/files_normalization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
    await handleApiResponse(response);
    return response.json();
};

export const runVectorization = async (): Promise<ApiResponse> => {
    const response = await fetch("/scraping/vectorization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
    await handleApiResponse(response);
    return response.json();
};

export const runProcessingAndVectorization = async (): Promise<ApiResponse> => {
    const response = await fetch("/scraping/process_and_vectorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    });
    await handleApiResponse(response);
    return response.json();
};

export const fetchVectorizationProgress = async (): Promise<ProgressInfo> => {
    const response = await fetch(`/scraping/vectorization_progress`);
    await handleApiResponse(response);
    return response.json();
};

export const resetVectorizationProgress = async (): Promise<void> => {
    const response = await fetch('/scraping/vectorization_reset_progress', {
        method: "POST",
    });
    await handleApiResponse(response);
};