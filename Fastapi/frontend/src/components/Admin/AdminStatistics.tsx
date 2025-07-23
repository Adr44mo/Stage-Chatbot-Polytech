// ==================================
// Composant des statistiques admin
// ==================================

import { useState, useEffect } from "react";
import type { 
  DailyStatsResponse, 
  MonthlyStatsResponse, 
  YearlyStatsResponse 
} from "../../api/statsApi";

// Fonctions API utilisant les routes existantes
const fetchDailyStats = async (limit: number = 30): Promise<DailyStatsResponse[]> => {
  const response = await fetch(`/intelligent-rag/stats/daily?limit=${limit}`, {
    credentials: "include"
  });
  
  if (!response.ok) {
    let errorMessage = `Erreur ${response.status}`;
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (typeof errorData.message === 'string') {
        errorMessage = errorData.message;
      }
    } catch {
      // Si on ne peut pas parser en JSON, récupérons le texte
      try {
        const textContent = await response.text();
        console.error("Contenu de la réponse (non-JSON):", textContent);
        errorMessage = `Erreur HTTP ${response.status}: ${textContent.substring(0, 200)}...`;
      } catch {
        errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
      }
    }
    throw new Error(errorMessage);
  }
  
  // Pour une réponse OK, on lit le texte d'abord puis on parse
  const textContent = await response.text();
  try {
    return JSON.parse(textContent);
  } catch (parseError) {
    console.error("Erreur parsing JSON:", parseError);
    console.error("Contenu brut de la réponse:", textContent);
    throw new Error(`Erreur de parsing JSON. Contenu reçu: ${textContent.substring(0, 200)}...`);
  }
};

const fetchMonthlyStats = async (limit: number = 12): Promise<MonthlyStatsResponse[]> => {
  const response = await fetch(`/intelligent-rag/stats/monthly?limit=${limit}`, {
    credentials: "include"
  });
  
  if (!response.ok) {
    let errorMessage = `Erreur ${response.status}`;
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (typeof errorData.message === 'string') {
        errorMessage = errorData.message;
      }
    } catch {
      try {
        const textContent = await response.text();
        console.error("Contenu de la réponse (non-JSON):", textContent);
        errorMessage = `Erreur HTTP ${response.status}: ${textContent.substring(0, 200)}...`;
      } catch {
        errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
      }
    }
    throw new Error(errorMessage);
  }
  
  const textContent = await response.text();
  try {
    return JSON.parse(textContent);
  } catch (parseError) {
    console.error("Erreur parsing JSON:", parseError);
    console.error("Contenu brut de la réponse:", textContent);
    throw new Error(`Erreur de parsing JSON. Contenu reçu: ${textContent.substring(0, 200)}...`);
  }
};

const fetchYearlyStats = async (limit: number = 5): Promise<YearlyStatsResponse[]> => {
  const response = await fetch(`/intelligent-rag/stats/yearly?limit=${limit}`, {
    credentials: "include"
  });
  
  if (!response.ok) {
    let errorMessage = `Erreur ${response.status}`;
    try {
      const errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (typeof errorData.message === 'string') {
        errorMessage = errorData.message;
      }
    } catch {
      try {
        const textContent = await response.text();
        console.error("Contenu de la réponse (non-JSON):", textContent);
        errorMessage = `Erreur HTTP ${response.status}: ${textContent.substring(0, 200)}...`;
      } catch {
        errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
      }
    }
    throw new Error(errorMessage);
  }
  
  const textContent = await response.text();
  try {
    return JSON.parse(textContent);
  } catch (parseError) {
    console.error("Erreur parsing JSON:", parseError);
    console.error("Contenu brut de la réponse:", textContent);
    throw new Error(`Erreur de parsing JSON. Contenu reçu: ${textContent.substring(0, 200)}...`);
  }
};

export default function AdminStatistics() {
  // États pour les données
  const [dailyStats, setDailyStats] = useState<DailyStatsResponse[]>([]);
  const [monthlyStats, setMonthlyStats] = useState<MonthlyStatsResponse[]>([]);
  const [yearlyStats, setYearlyStats] = useState<YearlyStatsResponse[]>([]);
  
  // États pour l'interface
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"daily" | "monthly" | "yearly">("daily");

  // Fonction pour charger toutes les statistiques
  const loadStats = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      console.log("[AdminStatistics] Chargement des statistiques...");
      
      // Chargement parallèle de toutes les données
      const [dailyData, monthlyData, yearlyData] = await Promise.all([
        fetchDailyStats(30),
        fetchMonthlyStats(12),
        fetchYearlyStats(5)
      ]);
      
      setDailyStats(dailyData);
      setMonthlyStats(monthlyData);
      setYearlyStats(yearlyData);
      
      console.log("[AdminStatistics] Statistiques chargées avec succès");
    } catch (err: any) {
      console.error("[AdminStatistics] Erreur lors du chargement:", err);
      setError(`Erreur lors de la récupération des statistiques: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Chargement initial
  useEffect(() => {
    loadStats();
  }, []);

  // Calculer les stats globales à partir des données existantes
  const globalStats = dailyStats.length > 0 ? {
    totalConversations: dailyStats.reduce((sum, day) => sum + day.total_conversations, 0),
    successfulConversations: dailyStats.reduce((sum, day) => sum + day.successful_conversations, 0),
    totalTokens: dailyStats.reduce((sum, day) => sum + day.total_tokens, 0),
    totalCost: dailyStats.reduce((sum, day) => sum + day.total_cost_usd, 0),
    avgSuccessRate: dailyStats.reduce((sum, day) => sum + day.success_rate, 0) / dailyStats.length
  } : null;

  return (
    <div className="admin-statistics" style={{ height: "100vh", overflow: "auto" }}>
      <div className="admin-section-header" style={{ position: "sticky", top: 0, backgroundColor: "white", zIndex: 10, padding: "1rem", borderBottom: "1px solid #ddd" }}>
        <h2>📊 Statistiques du Chatbot</h2>
        <button 
          onClick={loadStats} 
          disabled={isLoading}
          className="admin-btn admin-btn-primary"
        >
          {isLoading ? "Actualisation..." : "↻ Actualiser"}
        </button>
      </div>

      <div style={{ padding: "0 1rem", paddingBottom: "2rem" }}>
        {error && (
          <div className="admin-error-message">
            <p>{error}</p>
            <button onClick={loadStats} className="admin-btn admin-btn-secondary">
              Réessayer
            </button>
          </div>
        )}

        {isLoading && (
          <div className="admin-loading" style={{ textAlign: "center", padding: "2rem" }}>
            <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>⏳</div>
            <p>Chargement des statistiques...</p>
          </div>
        )}

        {!isLoading && !error && (
          <>
            {/* Vue d'ensemble globale avec graphiques améliorés */}
            {globalStats && (
              <section className="admin-stats-section" style={{ marginBottom: "2rem" }}>
                <h3>📈 Vue d'ensemble (30 derniers jours)</h3>
                <div className="admin-stats-grid" style={{ 
                  display: "grid", 
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", 
                  gap: "1rem",
                  marginBottom: "2rem"
                }}>
                  <div className="admin-stat-card" style={{ 
                    backgroundColor: "#f8f9fa", 
                    padding: "1.5rem", 
                    borderRadius: "8px", 
                    textAlign: "center",
                    border: "1px solid #e9ecef"
                  }}>
                    <div className="admin-stat-value" style={{ fontSize: "2rem", fontWeight: "bold", color: "#007bff" }}>
                      {globalStats.totalConversations}
                    </div>
                    <div className="admin-stat-label" style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                      Conversations Total
                    </div>
                  </div>
                  <div className="admin-stat-card" style={{ 
                    backgroundColor: "#f8f9fa", 
                    padding: "1.5rem", 
                    borderRadius: "8px", 
                    textAlign: "center",
                    border: "1px solid #e9ecef"
                  }}>
                    <div className="admin-stat-value" style={{ fontSize: "2rem", fontWeight: "bold", color: "#28a745" }}>
                      {globalStats.successfulConversations}
                    </div>
                    <div className="admin-stat-label" style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                      Conversations Réussies
                    </div>
                  </div>
                  <div className="admin-stat-card" style={{ 
                    backgroundColor: "#f8f9fa", 
                    padding: "1.5rem", 
                    borderRadius: "8px", 
                    textAlign: "center",
                    border: "1px solid #e9ecef"
                  }}>
                    <div className="admin-stat-value" style={{ fontSize: "2rem", fontWeight: "bold", color: "#17a2b8" }}>
                      {globalStats.avgSuccessRate.toFixed(1)}%
                    </div>
                    <div className="admin-stat-label" style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                      Taux de Succès Moyen
                    </div>
                  </div>
                  <div className="admin-stat-card" style={{ 
                    backgroundColor: "#f8f9fa", 
                    padding: "1.5rem", 
                    borderRadius: "8px", 
                    textAlign: "center",
                    border: "1px solid #e9ecef"
                  }}>
                    <div className="admin-stat-value" style={{ fontSize: "2rem", fontWeight: "bold", color: "#ffc107" }}>
                      {globalStats.totalTokens.toLocaleString()}
                    </div>
                    <div className="admin-stat-label" style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                      Tokens Total
                    </div>
                  </div>
                  <div className="admin-stat-card" style={{ 
                    backgroundColor: "#f8f9fa", 
                    padding: "1.5rem", 
                    borderRadius: "8px", 
                    textAlign: "center",
                    border: "1px solid #e9ecef"
                  }}>
                    <div className="admin-stat-value" style={{ fontSize: "2rem", fontWeight: "bold", color: "#dc3545" }}>
                      ${globalStats.totalCost.toFixed(2)}
                    </div>
                    <div className="admin-stat-label" style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                      Coût Total
                    </div>
                  </div>
                </div>

                {/* Mini graphique de tendance */}
                {dailyStats.length > 0 && (
                  <div style={{ 
                    backgroundColor: "#f8f9fa", 
                    padding: "1rem", 
                    borderRadius: "8px", 
                    border: "1px solid #e9ecef" 
                  }}>
                    <h4>📊 Tendance des conversations (derniers jours)</h4>
                    <div style={{ 
                      display: "flex", 
                      alignItems: "end", 
                      height: "100px", 
                      gap: "2px",
                      padding: "1rem 0"
                    }}>
                      {dailyStats.slice(0, 14).reverse().map((day, index) => {
                        const maxConversations = Math.max(...dailyStats.slice(0, 14).map(d => d.total_conversations));
                        const height = maxConversations > 0 ? (day.total_conversations / maxConversations) * 80 : 0;
                        return (
                          <div
                            key={index}
                            style={{
                              backgroundColor: day.success_rate > 90 ? "#28a745" : day.success_rate > 70 ? "#ffc107" : "#dc3545",
                              height: `${height + 10}px`,
                              flex: 1,
                              borderRadius: "2px"
                            }}
                            title={`${new Date(day.date).toLocaleDateString('fr-FR')}: ${day.total_conversations} conversations (${day.success_rate.toFixed(1)}%)`}
                          />
                        );
                      })}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "#6c757d", textAlign: "center" }}>
                      Vert: &gt;90% succès | Jaune: &gt;70% succès | Rouge: &lt;70% succès
                    </div>
                  </div>
                )}
              </section>
            )}

            {/* Onglets pour les différentes vues */}
            <section className="admin-stats-section" style={{ marginBottom: "2rem" }}>
              <div className="admin-stats-tabs" style={{ 
                display: "flex", 
                gap: "1rem", 
                marginBottom: "1.5rem",
                borderBottom: "2px solid #e9ecef"
              }}>
                <button 
                  className={`admin-stats-tab ${activeTab === "daily" ? "active" : ""}`}
                  onClick={() => setActiveTab("daily")}
                  style={{
                    padding: "0.75rem 1.5rem",
                    border: "none",
                    backgroundColor: activeTab === "daily" ? "#007bff" : "transparent",
                    color: activeTab === "daily" ? "white" : "#6c757d",
                    borderRadius: "8px 8px 0 0",
                    cursor: "pointer",
                    fontWeight: activeTab === "daily" ? "bold" : "normal",
                    transition: "all 0.2s"
                  }}
                >
                  📅 Journalier
                </button>
                <button 
                  className={`admin-stats-tab ${activeTab === "monthly" ? "active" : ""}`}
                  onClick={() => setActiveTab("monthly")}
                  style={{
                    padding: "0.75rem 1.5rem",
                    border: "none",
                    backgroundColor: activeTab === "monthly" ? "#007bff" : "transparent",
                    color: activeTab === "monthly" ? "white" : "#6c757d",
                    borderRadius: "8px 8px 0 0",
                    cursor: "pointer",
                    fontWeight: activeTab === "monthly" ? "bold" : "normal",
                    transition: "all 0.2s"
                  }}
                >
                  📆 Mensuel
                </button>
                <button 
                  className={`admin-stats-tab ${activeTab === "yearly" ? "active" : ""}`}
                  onClick={() => setActiveTab("yearly")}
                  style={{
                    padding: "0.75rem 1.5rem",
                    border: "none",
                    backgroundColor: activeTab === "yearly" ? "#007bff" : "transparent",
                    color: activeTab === "yearly" ? "white" : "#6c757d",
                    borderRadius: "8px 8px 0 0",
                    cursor: "pointer",
                    fontWeight: activeTab === "yearly" ? "bold" : "normal",
                    transition: "all 0.2s"
                  }}
                >
                  🗓️ Annuel
                </button>
              </div>            {/* Contenu des onglets */}
            {activeTab === "daily" && dailyStats.length > 0 && (
              <div className="admin-stats-content">
                <h4>📊 Statistiques Journalières (30 derniers jours)</h4>
                <div className="admin-table-container">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Conversations</th>
                        <th>Succès</th>
                        <th>Taux (%)</th>
                        <th>Tokens</th>
                        <th>Coût ($)</th>
                        <th>Temps moyen (s)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dailyStats.slice(0, 15).map((day) => (
                        <tr key={day.date}>
                          <td>{new Date(day.date).toLocaleDateString('fr-FR')}</td>
                          <td>{day.total_conversations}</td>
                          <td>{day.successful_conversations}</td>
                          <td>{day.success_rate.toFixed(1)}%</td>
                          <td>{day.total_tokens.toLocaleString()}</td>
                          <td>${day.total_cost_usd.toFixed(2)}</td>
                          <td>{day.avg_response_time.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === "monthly" && monthlyStats.length > 0 && (
              <div className="admin-stats-content">
                <h4>📈 Statistiques Mensuelles</h4>
                <div className="admin-table-container">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Période</th>
                        <th>Conversations</th>
                        <th>Succès</th>
                        <th>Taux (%)</th>
                        <th>Jours actifs</th>
                        <th>Pic journalier</th>
                        <th>Coût ($)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {monthlyStats.map((month) => (
                        <tr key={`${month.year}-${month.month}`}>
                          <td>{month.month}/{month.year}</td>
                          <td>{month.total_conversations}</td>
                          <td>{month.successful_conversations}</td>
                          <td>{month.success_rate.toFixed(1)}%</td>
                          <td>{month.active_days}</td>
                          <td>
                            {month.peak_day ? (
                              <span>
                                {month.peak_day} ({month.peak_day_conversations})
                              </span>
                            ) : "-"}
                          </td>
                          <td>${month.total_cost_usd.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === "yearly" && yearlyStats.length > 0 && (
              <div className="admin-stats-content">
                <h4>📊 Statistiques Annuelles</h4>
                <div className="admin-table-container">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Année</th>
                        <th>Conversations</th>
                        <th>Succès</th>
                        <th>Taux (%)</th>
                        <th>Mois actifs</th>
                        <th>Pic mensuel</th>
                        <th>Coût total ($)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {yearlyStats.map((year) => (
                        <tr key={year.year}>
                          <td>{year.year}</td>
                          <td>{year.total_conversations}</td>
                          <td>{year.successful_conversations}</td>
                          <td>{year.success_rate.toFixed(1)}%</td>
                          <td>{year.active_months}</td>
                          <td>
                            {year.peak_month ? (
                              <span>
                                {year.peak_month}/{year.year} ({year.peak_month_conversations})
                              </span>
                            ) : "-"}
                          </td>
                          <td>${year.total_cost_usd.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>

          {/* Distribution des intents/spécialités pour le jour le plus récent */}
          {dailyStats.length > 0 && dailyStats[0].intents_distribution && (
            <section className="admin-stats-section" style={{ marginBottom: "2rem" }}>
              <h3>🎯 Distribution Récente (dernier jour avec données)</h3>
              <div className="admin-stats-distributions" style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", 
                gap: "2rem"
              }}>
                {/* Graphique des intents */}
                <div className="admin-distribution-card" style={{ 
                  backgroundColor: "#f8f9fa", 
                  padding: "1.5rem", 
                  borderRadius: "8px",
                  border: "1px solid #e9ecef"
                }}>
                  <h4 style={{ marginBottom: "1.5rem", color: "#495057" }}>📊 Intents</h4>
                  {Object.entries(dailyStats[0].intents_distribution).map(([intent, count]) => {
                    const maxCount = Math.max(...Object.values(dailyStats[0].intents_distribution));
                    const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    return (
                      <div key={intent} className="admin-distribution-item" style={{ 
                        marginBottom: "1rem" 
                      }}>
                        <div style={{ 
                          display: "flex", 
                          justifyContent: "space-between", 
                          marginBottom: "0.5rem",
                          fontSize: "0.9rem"
                        }}>
                          <span style={{ fontWeight: "500" }}>{intent}</span>
                          <span style={{ color: "#6c757d" }}>{count}</span>
                        </div>
                        <div style={{ 
                          backgroundColor: "#e9ecef", 
                          height: "8px", 
                          borderRadius: "4px",
                          overflow: "hidden"
                        }}>
                          <div style={{ 
                            backgroundColor: "#007bff", 
                            height: "100%", 
                            width: `${percentage}%`,
                            transition: "width 0.3s ease"
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Graphique des spécialités */}
                <div className="admin-distribution-card" style={{ 
                  backgroundColor: "#f8f9fa", 
                  padding: "1.5rem", 
                  borderRadius: "8px",
                  border: "1px solid #e9ecef"
                }}>
                  <h4 style={{ marginBottom: "1.5rem", color: "#495057" }}>🎓 Spécialités</h4>
                  {Object.entries(dailyStats[0].specialities_distribution).map(([spec, count]) => {
                    const maxCount = Math.max(...Object.values(dailyStats[0].specialities_distribution));
                    const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    return (
                      <div key={spec} className="admin-distribution-item" style={{ 
                        marginBottom: "1rem" 
                      }}>
                        <div style={{ 
                          display: "flex", 
                          justifyContent: "space-between", 
                          marginBottom: "0.5rem",
                          fontSize: "0.9rem"
                        }}>
                          <span style={{ fontWeight: "500" }}>{spec}</span>
                          <span style={{ color: "#6c757d" }}>{count}</span>
                        </div>
                        <div style={{ 
                          backgroundColor: "#e9ecef", 
                          height: "8px", 
                          borderRadius: "4px",
                          overflow: "hidden"
                        }}>
                          <div style={{ 
                            backgroundColor: "#28a745", 
                            height: "100%", 
                            width: `${percentage}%`,
                            transition: "width 0.3s ease"
                          }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>
          )}
          </>
        )}
      </div>
    </div>
  );
}