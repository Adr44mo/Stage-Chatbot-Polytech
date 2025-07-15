export interface SiteInfo {
    name: string;
    url:string;
    lastScraped: string | null;
    newDocs?: number;
}

export async function fetchSiteInfos(): Promise<SiteInfo[]> {
    const response = await fetch("/scraping/site_infos");
    if (!response.ok) {
        throw new Error("Erreur lors du chargement des sites");
    }
    return response.json();
}

export async function fetchSiteNewDocs(): Promise<{ name: string; url: string, newDocs: number }[]> {
    const response = await fetch("/scraping/site_new_docs");
    if (!response.ok) {
        throw new Error("Erreur lors du chargement des sites");
    }
    return response.json();
}

export async function addSite(name: string, url: string) {
    const response = await fetch("/scraping/add_site", {
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({ siteName: name, url}),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Erreur lors de l'ajout du site");
    }
    return response.json();
}

export async function suppSite(name: string) {
    const response = await fetch("/scraping/supp_site", {
        method: "POST",
        headers: { "Content-Type": "application/json"},
        body: JSON.stringify({ siteName: name }),
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Erreur lors de la suppression du site");
    }
    return response.json();
}

export async function runScraping(siteNames: string[]) {
	const response = await fetch("/scraping/scraping", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify(siteNames),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail || "Erreur inconnue");
	}

	return await response.json();
}
