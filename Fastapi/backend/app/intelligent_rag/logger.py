"""
Système de logging et statistiques pour le RAG intelligent
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import tiktoken
import hashlib

class RAGLogger:
    """Gestionnaire de logging et statistiques pour le système RAG"""
    
    def __init__(self, log_dir: str = None):
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent / "logs"
        self.responses_dir = self.log_dir / "responses"
        self.stats_file = self.log_dir / "statistics.json"
        
        # Créer les répertoires
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialiser le tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")
        except Exception:
            # Fallback si le modèle n'est pas reconnu
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Charger les statistiques existantes
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Charger les statistiques existantes"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Logger] Erreur chargement stats: {e}")
        
        return {
            "total_requests": 0,
            "total_tokens": {
                "input": 0,
                "output": 0,
                "total": 0
            },
            "intents": {
                "DIRECT_ANSWER": 0,
                "RAG_NEEDED": 0,
                "SYLLABUS_SPECIFIC_COURSE": 0,
                "SYLLABUS_SPECIALITY_OVERVIEW": 0
            },
            "specialities": {},
            "daily_stats": {},
            "response_times": [],
            "errors": 0,
            "last_updated": None
        }
    
    def _save_stats(self):
        """Sauvegarder les statistiques"""
        try:
            self.stats["last_updated"] = datetime.now().isoformat()
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Logger] Erreur sauvegarde stats: {e}")
    
    def count_tokens(self, text: str) -> int:
        """Compter les tokens dans un texte"""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            print(f"[Logger] Erreur comptage tokens: {e}")
            # Estimation approximative : ~4 caractères par token
            return len(text) // 4
    
    def generate_session_id(self, question: str, timestamp: str) -> str:
        """Générer un ID unique pour la session"""
        content = f"{question}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def log_conversation(self, 
                        question: str,
                        result: Dict[str, Any],
                        chat_history: list = None,
                        response_time: float = None,
                        intermediate_operations: list = None) -> str:
        """
        Logger une conversation complète avec statistiques détaillées
        
        Args:
            question: Question de l'utilisateur
            result: Résultat du RAG
            chat_history: Historique de conversation
            response_time: Temps de réponse
            intermediate_operations: Liste des opérations intermédiaires avec leurs coûts
        
        Returns:
            str: ID du fichier de log créé
        """
        timestamp = datetime.now()
        session_id = self.generate_session_id(question, timestamp.isoformat())
        
        # Compter les tokens de base (utilisateur)
        input_tokens = self.count_tokens(question)
        if chat_history:
            history_text = " ".join([msg.get("content", "") for msg in chat_history])
            input_tokens += self.count_tokens(history_text)
        
        output_tokens = self.count_tokens(result.get("answer", ""))
        
        # Calculer les tokens des opérations intermédiaires
        intermediate_tokens = {
            "total_input": 0,
            "total_output": 0,
            "operations": []
        }
        
        if intermediate_operations:
            for op in intermediate_operations:
                op_input_tokens = op.get("input_tokens", 0)
                op_output_tokens = op.get("output_tokens", 0)
                intermediate_tokens["total_input"] += op_input_tokens
                intermediate_tokens["total_output"] += op_output_tokens
                intermediate_tokens["operations"].append({
                    "operation": op.get("operation", "unknown"),
                    "model": op.get("model", "unknown"),
                    "input_tokens": op_input_tokens,
                    "output_tokens": op_output_tokens,
                    "total_tokens": op_input_tokens + op_output_tokens,
                    "cost_usd": op.get("cost_usd", 0)
                })
        
        # Calculer les tokens totaux (utilisateur + intermédiaires)
        total_input_tokens = input_tokens + intermediate_tokens["total_input"]
        total_output_tokens = output_tokens + intermediate_tokens["total_output"]
        total_tokens = total_input_tokens + total_output_tokens
        
        # Calculer le coût total
        total_cost = sum(op.get("cost_usd", 0) for op in intermediate_operations or [])
        
        # Préparer les données de log
        log_data = {
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "request": {
                "question": question,
                "chat_history": chat_history or [],
                "user_input_tokens": input_tokens
            },
            "response": {
                "answer": result.get("answer", ""),
                "intent_analysis": result.get("intent_analysis"),
                "context_docs_count": len(result.get("context", [])),
                "sources_count": len(result.get("sources", [])),
                "processing_steps": result.get("processing_steps", []),
                "final_output_tokens": output_tokens,
                "success": result.get("success", False),
                "error": result.get("error")
            },
            "performance": {
                "response_time_seconds": response_time,
                "tokens": {
                    "user_input": input_tokens,
                    "final_output": output_tokens,
                    "intermediate_input": intermediate_tokens["total_input"],
                    "intermediate_output": intermediate_tokens["total_output"],
                    "total_input": total_input_tokens,
                    "total_output": total_output_tokens,
                    "grand_total": total_tokens
                },
                "cost": {
                    "total_usd": total_cost,
                    "operations": intermediate_tokens["operations"]
                }
            },
            "context": {
                "documents": [
                    {
                        "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    } for doc in result.get("context", [])
                ]
            }
        }
        
        # Sauvegarder la réponse individuelle
        response_file = self.responses_dir / f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{session_id}.json"
        try:
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Logger] Erreur sauvegarde réponse: {e}")
        
        # Mettre à jour les statistiques
        self._update_stats(log_data)
        
        return session_id
    
    def _update_stats(self, log_data: Dict[str, Any]):
        """Mettre à jour les statistiques globales"""
        # Compteurs généraux
        self.stats["total_requests"] += 1
        
        # Tokens
        tokens = log_data["performance"]["tokens"]
        self.stats["total_tokens"]["input"] += tokens["total_input"]
        self.stats["total_tokens"]["output"] += tokens["total_output"]
        self.stats["total_tokens"]["total"] += tokens["grand_total"]
        
        # Intentions
        intent_analysis = log_data["response"]["intent_analysis"]
        if intent_analysis:
            intent = intent_analysis.get("intent")
            if intent:
                self.stats["intents"][intent] = self.stats["intents"].get(intent, 0) + 1
            
            # Spécialités
            speciality = intent_analysis.get("speciality")
            if speciality:
                self.stats["specialities"][speciality] = self.stats["specialities"].get(speciality, 0) + 1
        
        # Statistiques journalières
        date_key = datetime.now().strftime('%Y-%m-%d')
        if date_key not in self.stats["daily_stats"]:
            self.stats["daily_stats"][date_key] = {
                "requests": 0,
                "tokens": {"input": 0, "output": 0, "total": 0},
                "intents": {},
                "errors": 0
            }
        
        daily = self.stats["daily_stats"][date_key]
        daily["requests"] += 1
        daily["tokens"]["input"] += tokens["input"]
        daily["tokens"]["output"] += tokens["output"]
        daily["tokens"]["total"] += tokens["total"]
        
        if intent_analysis and intent_analysis.get("intent"):
            intent = intent_analysis["intent"]
            daily["intents"][intent] = daily["intents"].get(intent, 0) + 1
        
        # Temps de réponse
        response_time = log_data["performance"]["response_time_seconds"]
        if response_time:
            self.stats["response_times"].append(response_time)
            # Garder seulement les 1000 derniers temps de réponse
            if len(self.stats["response_times"]) > 1000:
                self.stats["response_times"] = self.stats["response_times"][-1000:]
        
        # Erreurs
        if log_data["response"]["error"]:
            self.stats["errors"] += 1
            daily["errors"] += 1
        
        # Sauvegarder
        self._save_stats()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques complètes"""
        stats = self.stats.copy()
        
        # Calculer des métriques dérivées
        if self.stats["response_times"]:
            response_times = self.stats["response_times"]
            stats["performance"] = {
                "avg_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "total_measurements": len(response_times)
            }
        
        # Coût estimé (basé sur les prix OpenAI pour gpt-4o-mini)
        # $0.15 / 1M tokens input, $0.60 / 1M tokens output
        input_cost = (self.stats["total_tokens"]["input"] / 1_000_000) * 0.15
        output_cost = (self.stats["total_tokens"]["output"] / 1_000_000) * 0.60
        stats["estimated_cost"] = {
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(input_cost + output_cost, 4)
        }
        
        return stats
    
    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Obtenir le rapport journalier"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return self.stats["daily_stats"].get(date, {})
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Nettoyer les anciens logs"""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        
        deleted_count = 0
        for log_file in self.responses_dir.glob("*.json"):
            if log_file.stat().st_mtime < cutoff_date:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"[Logger] Erreur suppression {log_file}: {e}")
        
        print(f"[Logger] {deleted_count} anciens logs supprimés")
        return deleted_count

# Instance globale du logger
rag_logger = RAGLogger()
