// =================
// Page Statistiques
// =================

import { useEffect, useState } from "react";
import { fetchGlobalStats, fetchDailyStats } from "../../api/statsApi";

export default function AdminStatistics() {
  const [globalStats, setGlobalStats] = useState<any>(null);
  const [dailyStats, setDailyStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    Promise.all([
      fetchGlobalStats(),
      fetchDailyStats()
    ])
      .then(([global, daily]) => {
        setGlobalStats(global);
        setDailyStats(daily);
      })
      .catch(() => setError("Erreur lors de la récupération des statistiques"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 className="admin-page-subtitle">Statistiques</h2>
      {loading && <p>Chargement...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && (
        <>
          <h3>Statistiques globales</h3>
          {globalStats ? (
            <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 6, overflowX: "auto" }}>
              {JSON.stringify(globalStats, null, 2)}
            </pre>
          ) : <p>Aucune donnée</p>}

          <h3>Statistiques du jour</h3>
          {dailyStats ? (
            <pre style={{ background: "#f5f5f5", padding: 12, borderRadius: 6, overflowX: "auto" }}>
              {JSON.stringify(dailyStats, null, 2)}
            </pre>
          ) : <p>Aucune donnée</p>}
        </>
      )}
    </div>
  );
}
