// ==================================
// Composant de maintenance admin
// ==================================

import { useState, useEffect } from "react";
import { DateTime } from "luxon";

/* URL de l'API backend */
const API_URL = import.meta.env.VITE_BACKEND_URL || "/api";

// Types pour les APIs de maintenance
interface MaintenanceStatus {
  service_running: boolean;
  next_scheduled_tasks: any[];
  timestamp: string;
}

interface MaintenanceSchedule {
  daily_maintenance: {
    description: string;
    schedule: string;
  };
  weekly_cleanup: {
    description: string;
    schedule: string;
  };
  monthly_cleanup: {
    description: string;
    schedule: string;
  };
  next_tasks: any[];
  timestamp: string;
}

interface CleanupResult {
  message: string;
  result: any;
  timestamp: string;
}

// Fonctions API pour la maintenance
const fetchMaintenanceStatus = async (): Promise<MaintenanceStatus> => {
  const response = await fetch(`${API_URL}/intelligent-rag/maintenance/status`, {
    credentials: "include"
  });
  
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
};

const fetchMaintenanceSchedule = async (): Promise<MaintenanceSchedule> => {
  const response = await fetch(`${API_URL}/intelligent-rag/maintenance/schedule`, {
    credentials: "include"
  });
  
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
};

const startMaintenanceService = async (): Promise<any> => {
  const response = await fetch(`${API_URL}/intelligent-rag/maintenance/service/start`, {
    method: 'POST',
    credentials: "include"
  });
  
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
};

const stopMaintenanceService = async (): Promise<any> => {
  const response = await fetch(`${API_URL}/intelligent-rag/maintenance/service/stop`, {
    method: 'POST',
    credentials: "include"
  });
  
  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${response.statusText}`);
  }
  
  return response.json();
};

const runManualCleanup = async (daysToKeep: number): Promise<CleanupResult> => {
  const response = await fetch(`${API_URL}/intelligent-rag/maintenance/cleanup/manual?days_to_keep=${daysToKeep}`, {
    method: 'POST',
    credentials: "include"
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `Erreur ${response.status}`);
  }
  
  return response.json();
};

export default function AdminMaintenance() {
  // États
  const [status, setStatus] = useState<MaintenanceStatus | null>(null);
  const [schedule, setSchedule] = useState<MaintenanceSchedule | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");
  const [daysToKeep, setDaysToKeep] = useState<number>(90);
  const [isProcessing, setIsProcessing] = useState(false);

  // Fonction pour charger les données
  const loadMaintenanceData = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      const [statusData, scheduleData] = await Promise.all([
        fetchMaintenanceStatus(),
        fetchMaintenanceSchedule()
      ]);
      
      setStatus(statusData);
      setSchedule(scheduleData);
      console.log("[AdminMaintenance] Données de maintenance chargées");
    } catch (err: any) {
      console.error("[AdminMaintenance] Erreur de chargement:", err);
      setError(`Erreur: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Fonction pour démarrer le service
  const handleStartService = async () => {
    setIsProcessing(true);
    setError("");
    setSuccessMessage("");
    
    try {
      await startMaintenanceService();
      setSuccessMessage("Service de maintenance démarré avec succès !");
      await loadMaintenanceData(); // Recharger les données
    } catch (err: any) {
      setError(`Erreur lors du démarrage: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Fonction pour arrêter le service
  const handleStopService = async () => {
    setIsProcessing(true);
    setError("");
    setSuccessMessage("");
    
    try {
      await stopMaintenanceService();
      setSuccessMessage("Service de maintenance arrêté avec succès !");
      await loadMaintenanceData(); // Recharger les données
    } catch (err: any) {
      setError(`Erreur lors de l'arrêt: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Fonction pour le nettoyage manuel
  const handleManualCleanup = async () => {
    if (daysToKeep < 30) {
      setError("Par sécurité, minimum 30 jours de données doivent être conservées");
      return;
    }

    setIsProcessing(true);
    setError("");
    setSuccessMessage("");
    
    try {
      const result = await runManualCleanup(daysToKeep);
      setSuccessMessage(result.message);
    } catch (err: any) {
      setError(`Erreur lors du nettoyage: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Chargement initial
  useEffect(() => {
    loadMaintenanceData();
  }, []);

  // Auto-refresh toutes les 30 secondes
  useEffect(() => {
    const interval = setInterval(loadMaintenanceData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="admin-maintenance" style={{ height: "100vh", overflow: "auto" }}>
      <div className="admin-section-header" style={{ 
        position: "sticky", 
        top: 0, 
        backgroundColor: "white", 
        zIndex: 10, 
        padding: "1rem", 
        borderBottom: "1px solid #ddd" 
      }}>
        <h2>🔧 Maintenance du Système</h2>
        <button 
          onClick={loadMaintenanceData} 
          disabled={isLoading}
          className="admin-btn admin-btn-primary"
        >
          {isLoading ? "Actualisation..." : "↻ Actualiser"}
        </button>
      </div>

      <div style={{ padding: "0 1rem", paddingBottom: "2rem" }}>
        {/* Messages d'erreur et de succès */}
        {error && (
          <div className="admin-error-message" style={{ 
            backgroundColor: "#f8d7da", 
            color: "#721c24", 
            padding: "1rem", 
            borderRadius: "8px", 
            marginBottom: "1rem",
            border: "1px solid #f5c6cb"
          }}>
            <p>❌ {error}</p>
          </div>
        )}

        {successMessage && (
          <div style={{ 
            backgroundColor: "#d4edda", 
            color: "#155724", 
            padding: "1rem", 
            borderRadius: "8px", 
            marginBottom: "1rem",
            border: "1px solid #c3e6cb"
          }}>
            <p>✅ {successMessage}</p>
          </div>
        )}

        {isLoading && (
          <div className="admin-loading" style={{ textAlign: "center", padding: "2rem" }}>
            <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>⏳</div>
            <p>Chargement des informations de maintenance...</p>
          </div>
        )}

        {!isLoading && status && schedule && (
          <>
            {/* Status du service */}
            <section className="admin-stats-section" style={{ marginBottom: "2rem" }}>
              <h3>📊 Statut du Service</h3>
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", 
                gap: "1rem",
                marginBottom: "1.5rem"
              }}>
                <div style={{ 
                  backgroundColor: status.service_running ? "#d4edda" : "#f8d7da", 
                  padding: "1.5rem", 
                  borderRadius: "8px", 
                  textAlign: "center",
                  border: `1px solid ${status.service_running ? "#c3e6cb" : "#f5c6cb"}`
                }}>
                  <div style={{ 
                    fontSize: "3rem", 
                    marginBottom: "0.5rem"
                  }}>
                    {status.service_running ? "🟢" : "🔴"}
                  </div>
                  <div style={{ 
                    fontSize: "1.2rem", 
                    fontWeight: "bold",
                    color: status.service_running ? "#155724" : "#721c24"
                  }}>
                    {status.service_running ? "Service Actif" : "Service Arrêté"}
                  </div>
                  <div style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                    Dernière vérification: {DateTime.fromISO(status.timestamp, { zone: 'utc' }).setZone('Europe/Paris').toFormat('dd/MM/yyyy HH:mm:ss')}
                  </div>
                </div>

                <div style={{ 
                  backgroundColor: "#f8f9fa", 
                  padding: "1.5rem", 
                  borderRadius: "8px", 
                  textAlign: "center",
                  border: "1px solid #e9ecef"
                }}>
                  <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📅</div>
                  <div style={{ fontSize: "1.1rem", fontWeight: "bold" }}>
                    Prochaines Tâches
                  </div>
                  <div style={{ fontSize: "0.9rem", color: "#6c757d" }}>
                    {status.next_scheduled_tasks?.length > 0 
                      ? `${status.next_scheduled_tasks.length} tâche(s) planifiée(s)`
                      : "Aucune tâche planifiée"
                    }
                  </div>
                </div>
              </div>

              {/* Contrôles du service */}
              <div style={{ 
                display: "flex", 
                gap: "1rem", 
                justifyContent: "center",
                flexWrap: "wrap"
              }}>
                <button
                  onClick={handleStartService}
                  disabled={isProcessing || status.service_running}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: status.service_running ? "#6c757d" : "#28a745",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: status.service_running ? "not-allowed" : "pointer",
                    fontWeight: "bold"
                  }}
                >
                  {isProcessing ? "⏳ Démarrage..." : "▶️ Démarrer le Service"}
                </button>
                
                <button
                  onClick={handleStopService}
                  disabled={isProcessing || !status.service_running}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: !status.service_running ? "#6c757d" : "#dc3545",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: !status.service_running ? "not-allowed" : "pointer",
                    fontWeight: "bold"
                  }}
                >
                  {isProcessing ? "⏳ Arrêt..." : "⏹️ Arrêter le Service"}
                </button>
              </div>
            </section>

            {/* Planning des tâches */}
            <section className="admin-stats-section" style={{ marginBottom: "2rem" }}>
              <h3>📋 Planning des Tâches Automatiques</h3>
              <div style={{ 
                display: "grid", 
                gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", 
                gap: "1rem"
              }}>
                <div style={{ 
                  backgroundColor: "#e7f3ff", 
                  padding: "1.5rem", 
                  borderRadius: "8px",
                  border: "1px solid #b8daff"
                }}>
                  <h4 style={{ margin: "0 0 1rem 0", color: "#0056b3" }}>
                    🌅 Maintenance Quotidienne
                  </h4>
                  <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                    <strong>Description:</strong> {schedule.daily_maintenance.description}
                  </p>
                  <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                    <strong>Planning:</strong> {schedule.daily_maintenance.schedule}
                  </p>
                </div>

                <div style={{ 
                  backgroundColor: "#fff3cd", 
                  padding: "1.5rem", 
                  borderRadius: "8px",
                  border: "1px solid #ffeaa7"
                }}>
                  <h4 style={{ margin: "0 0 1rem 0", color: "#856404" }}>
                    🗓️ Nettoyage Hebdomadaire
                  </h4>
                  <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                    <strong>Description:</strong> {schedule.weekly_cleanup.description}
                  </p>
                  <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                    <strong>Planning:</strong> {schedule.weekly_cleanup.schedule}
                  </p>
                </div>

                <div style={{ 
                  backgroundColor: "#f8d7da", 
                  padding: "1.5rem", 
                  borderRadius: "8px",
                  border: "1px solid #f5c6cb"
                }}>
                  <h4 style={{ margin: "0 0 1rem 0", color: "#721c24" }}>
                    📆 Nettoyage Mensuel
                  </h4>
                  <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                    <strong>Description:</strong> {schedule.monthly_cleanup.description}
                  </p>
                  <p style={{ margin: "0.5rem 0", fontSize: "0.9rem" }}>
                    <strong>Planning:</strong> {schedule.monthly_cleanup.schedule}
                  </p>
                </div>
              </div>
            </section>

            {/* Nettoyage manuel */}
            <section className="admin-stats-section" style={{ marginBottom: "2rem" }}>
              <h3>🧹 Nettoyage Manuel</h3>
              <div style={{ 
                backgroundColor: "#f8f9fa", 
                padding: "1.5rem", 
                borderRadius: "8px",
                border: "1px solid #e9ecef"
              }}>
                <p style={{ marginBottom: "1rem", color: "#6c757d" }}>
                  Déclencher un nettoyage manuel des données anciennes. 
                  <strong> Attention:</strong> cette action supprimera définitivement les données plus anciennes que le nombre de jours spécifié.
                </p>
                
                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "1rem", 
                  flexWrap: "wrap",
                  marginBottom: "1rem"
                }}>
                  <label style={{ fontWeight: "bold" }}>
                    Conserver les données des derniers:
                  </label>
                  <input
                    type="number"
                    min="30"
                    max="365"
                    value={daysToKeep}
                    onChange={(e) => setDaysToKeep(parseInt(e.target.value) || 90)}
                    style={{
                      padding: "0.5rem",
                      border: "1px solid #ced4da",
                      borderRadius: "4px",
                      width: "100px"
                    }}
                  />
                  <span>jours</span>
                </div>

                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "1rem",
                  marginBottom: "1rem"
                }}>
                  <div style={{ 
                    fontSize: "0.85rem", 
                    color: daysToKeep < 30 ? "#dc3545" : daysToKeep < 60 ? "#ffc107" : "#28a745",
                    fontWeight: "bold"
                  }}>
                    {daysToKeep < 30 && "⚠️ Minimum 30 jours requis"}
                    {daysToKeep >= 30 && daysToKeep < 60 && "⚠️ Attention: période de conservation courte"}
                    {daysToKeep >= 60 && "✅ Période de conservation recommandée"}
                  </div>
                </div>

                <button
                  onClick={handleManualCleanup}
                  disabled={isProcessing || daysToKeep < 30}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: daysToKeep < 30 ? "#6c757d" : "#dc3545",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    cursor: daysToKeep < 30 ? "not-allowed" : "pointer",
                    fontWeight: "bold"
                  }}
                >
                  {isProcessing ? "⏳ Nettoyage en cours..." : `🗑️ Nettoyer (garder ${daysToKeep} jours)`}
                </button>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
