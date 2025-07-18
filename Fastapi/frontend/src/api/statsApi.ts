// =================================================
// Gestionnaire des appels API pour les statistiques
// =================================================

// Récupère les statistiques globales
export async function fetchGlobalStats() {
  const res = await fetch("/intelligent-rag/database/statistics", {
    credentials: "include",
  });
  if (!res.ok)
    throw new Error("Erreur lors de la récupération des statistiques globales");
  return await res.json();
}

// Récupère le rapport journalier (aujourd'hui par défaut)
export async function fetchDailyStats(date?: string) {
  let url = "/intelligent-rag/database/statistics/daily";
  if (date) url += `?date=${encodeURIComponent(date)}`;
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok)
    throw new Error("Erreur lors de la récupération du rapport journalier");
  return await res.json();
}
