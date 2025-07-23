// ============================================
// Gestionnaire des appels API pour statistiques
// ============================================

// Types basés sur les modèles backend existants
export interface DailyStatsResponse {
  date: string;
  total_conversations: number;
  successful_conversations: number;
  failed_conversations: number;
  success_rate: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_response_time: number;
  intents_distribution: Record<string, number>;
  specialities_distribution: Record<string, number>;
}

export interface MonthlyStatsResponse {
  year: number;
  month: number;
  total_conversations: number;
  successful_conversations: number;
  failed_conversations: number;
  success_rate: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_response_time: number;
  active_days: number;
  peak_day: string | null;
  peak_day_conversations: number;
}

export interface YearlyStatsResponse {
  year: number;
  total_conversations: number;
  successful_conversations: number;
  failed_conversations: number;
  success_rate: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_response_time: number;
  active_months: number;
  peak_month: number | null;
  peak_month_conversations: number;
  monthly_evolution: Array<Record<string, any>>;
}

// Utilitaires pour gérer les erreurs d'API
class StatsApiError extends Error {
  constructor(message: string | any) {
    const errorMessage = typeof message === 'string' ? message : JSON.stringify(message);
    super(errorMessage);
    this.name = 'StatsApiError';
  }
}

export const handleStatsResponse = async (response: Response) => {
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
    throw new StatsApiError(errorMessage);
  }
  return response;
};
