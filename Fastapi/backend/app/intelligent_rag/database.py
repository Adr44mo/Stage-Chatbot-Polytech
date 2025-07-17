"""
Base de données SQLite pour le système RAG intelligent
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import asdict
import threading
from contextlib import contextmanager

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

class RAGDatabase:
    """Gestionnaire de base de données pour le système RAG intelligent"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Path(__file__).parent / "logs" / "rag_system.db"
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        cp.print_info(f"[Database] Initialisation de la base de données à {self.db_path}")
        # donner les droit en écriture à tous les utilisateurs
        self._set_db_permissions()

        # Thread lock pour la sécurité
        self._lock = threading.Lock()
        
        # Initialiser la base de données
        self._init_database()
    
    def _set_db_permissions(self):
        """Définir les permissions de la base de données pour tous les utilisateurs"""
        try:
            # on commence par le dossier parent
            os.chmod(self.db_path.parent, 0o777)  # Permissions en écriture
            os.chmod(self.db_path, 0o666)  # Permissions en écriture
            cp.print_info(f"[Database] Permissions définies pour {self.db_path}")
        except Exception as e:
            cp.print_error(f"[Database] Erreur lors de la définition des permissions: {e}")

    def _init_database(self):
        """Initialiser les tables de la base de données"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des conversations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    timestamp DATETIME NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    chat_history TEXT, -- JSON
                    intent_analysis TEXT, -- JSON
                    context_docs_count INTEGER DEFAULT 0,
                    sources_count INTEGER DEFAULT 0,
                    processing_steps TEXT, -- JSON
                    success BOOLEAN DEFAULT 1,
                    error TEXT,
                    response_time REAL,
                    user_input_tokens INTEGER DEFAULT 0,
                    final_output_tokens INTEGER DEFAULT 0,
                    intermediate_input_tokens INTEGER DEFAULT 0,
                    intermediate_output_tokens INTEGER DEFAULT 0,
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    grand_total_tokens INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des opérations de tokens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
                )
            ''')
            
            # Table des documents contextuels
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS context_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    content_preview TEXT NOT NULL,
                    metadata TEXT NOT NULL, -- JSON
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
                )
            ''')
            
            # Table des statistiques globales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS global_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_name TEXT UNIQUE NOT NULL,
                    stat_value TEXT NOT NULL, -- JSON pour flexibilité
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index pour optimiser les requêtes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_session ON token_operations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_context_session ON context_documents(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stat_name ON global_statistics(stat_name)')
            
            conn.commit()
            cp.print_success("[Database] Base de données initialisée avec succès")
    
    @contextmanager
    def _get_connection(self):
        """Context manager pour les connexions à la base de données"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            cp.print_error(f"[Database] Erreur de connexion: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_conversation(self, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """Sauvegarder une conversation complète"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Extraire les données
                    request = conversation_data.get("request", {})
                    response = conversation_data.get("response", {})
                    performance = conversation_data.get("performance", {})
                    context = conversation_data.get("context", {})
                    
                    tokens = performance.get("tokens", {})
                    cost = performance.get("cost", {})
                    
                    # Insérer la conversation principale
                    cursor.execute('''
                        INSERT OR REPLACE INTO conversations (
                            session_id, timestamp, question, answer, chat_history,
                            intent_analysis, context_docs_count, sources_count,
                            processing_steps, success, error, response_time,
                            user_input_tokens, final_output_tokens, 
                            intermediate_input_tokens, intermediate_output_tokens,
                            total_input_tokens, total_output_tokens, 
                            grand_total_tokens, total_cost_usd
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session_id,
                        conversation_data.get("timestamp"),
                        request.get("question", ""),
                        response.get("answer", ""),
                        json.dumps(request.get("chat_history", [])),
                        json.dumps(response.get("intent_analysis")),
                        response.get("context_docs_count", 0),
                        response.get("sources_count", 0),
                        json.dumps(response.get("processing_steps", [])),
                        response.get("success", True),
                        response.get("error"),
                        performance.get("response_time_seconds"),
                        tokens.get("user_input", 0),
                        tokens.get("final_output", 0),
                        tokens.get("intermediate_input", 0),
                        tokens.get("intermediate_output", 0),
                        tokens.get("total_input", 0),
                        tokens.get("total_output", 0),
                        tokens.get("grand_total", 0),
                        cost.get("total_usd", 0.0)
                    ))
                    
                    # Supprimer les anciennes opérations de tokens pour cette session
                    cursor.execute('DELETE FROM token_operations WHERE session_id = ?', (session_id,))
                    
                    # Insérer les opérations de tokens
                    for operation in cost.get("operations", []):
                        cursor.execute('''
                            INSERT INTO token_operations (
                                session_id, operation, model, input_tokens, 
                                output_tokens, total_tokens, cost_usd, timestamp
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            session_id,
                            operation.get("operation", ""),
                            operation.get("model", ""),
                            operation.get("input_tokens", 0),
                            operation.get("output_tokens", 0),
                            operation.get("total_tokens", 0),
                            operation.get("cost_usd", 0.0),
                            operation.get("timestamp", datetime.now().isoformat())
                        ))
                    
                    # Supprimer les anciens documents contextuels
                    cursor.execute('DELETE FROM context_documents WHERE session_id = ?', (session_id,))
                    
                    # Insérer les documents contextuels
                    for doc in context.get("documents", []):
                        cursor.execute('''
                            INSERT INTO context_documents (session_id, content_preview, metadata)
                            VALUES (?, ?, ?)
                        ''', (
                            session_id,
                            doc.get("content_preview", ""),
                            json.dumps(doc.get("metadata", {}))
                        ))
                    
                    conn.commit()
                    cp.print_success(f"[Database] Conversation {session_id} sauvegardée")
                    return True
                    
        except Exception as e:
            cp.print_error(f"[Database] Erreur sauvegarde conversation: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une conversation par session ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Récupérer la conversation principale
                cursor.execute('''
                    SELECT * FROM conversations WHERE session_id = ?
                ''', (session_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Récupérer les opérations de tokens
                cursor.execute('''
                    SELECT * FROM token_operations WHERE session_id = ?
                    ORDER BY timestamp
                ''', (session_id,))
                
                operations = []
                for op_row in cursor.fetchall():
                    operations.append({
                        "operation": op_row["operation"],
                        "model": op_row["model"],
                        "input_tokens": op_row["input_tokens"],
                        "output_tokens": op_row["output_tokens"],
                        "total_tokens": op_row["total_tokens"],
                        "cost_usd": op_row["cost_usd"],
                        "timestamp": op_row["timestamp"]
                    })
                
                # Récupérer les documents contextuels
                cursor.execute('''
                    SELECT * FROM context_documents WHERE session_id = ?
                ''', (session_id,))
                
                documents = []
                for doc_row in cursor.fetchall():
                    documents.append({
                        "content_preview": doc_row["content_preview"],
                        "metadata": json.loads(doc_row["metadata"])
                    })
                
                # Reconstituer la structure
                return {
                    "session_id": row["session_id"],
                    "timestamp": row["timestamp"],
                    "request": {
                        "question": row["question"],
                        "chat_history": json.loads(row["chat_history"] or "[]"),
                        "user_input_tokens": row["user_input_tokens"]
                    },
                    "response": {
                        "answer": row["answer"],
                        "intent_analysis": json.loads(row["intent_analysis"] or "null"),
                        "context_docs_count": row["context_docs_count"],
                        "sources_count": row["sources_count"],
                        "processing_steps": json.loads(row["processing_steps"] or "[]"),
                        "success": bool(row["success"]),
                        "error": row["error"]
                    },
                    "performance": {
                        "response_time_seconds": row["response_time"],
                        "tokens": {
                            "user_input": row["user_input_tokens"],
                            "final_output": row["final_output_tokens"],
                            "intermediate_input": row["intermediate_input_tokens"],
                            "intermediate_output": row["intermediate_output_tokens"],
                            "total_input": row["total_input_tokens"],
                            "total_output": row["total_output_tokens"],
                            "grand_total": row["grand_total_tokens"]
                        },
                        "cost": {
                            "total_usd": row["total_cost_usd"],
                            "operations": operations
                        }
                    },
                    "context": {
                        "documents": documents
                    }
                }
                
        except Exception as e:
            cp.print_error(f"[Database] Erreur récupération conversation: {e}")
            return None
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupérer les conversations récentes"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT session_id, timestamp, question, answer, success, 
                           response_time, grand_total_tokens, total_cost_usd,
                           intent_analysis
                    FROM conversations
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                conversations = []
                for row in cursor.fetchall():
                    intent_analysis = json.loads(row["intent_analysis"] or "null")
                    conversations.append({
                        "session_id": row["session_id"],
                        "timestamp": row["timestamp"],
                        "question": row["question"][:100] + "..." if len(row["question"]) > 100 else row["question"],
                        "answer_preview": row["answer"][:100] + "..." if len(row["answer"]) > 100 else row["answer"],
                        "intent": intent_analysis.get("intent") if intent_analysis else None,
                        "success": bool(row["success"]),
                        "response_time": row["response_time"],
                        "total_tokens": row["grand_total_tokens"],
                        "cost_usd": row["total_cost_usd"]
                    })
                
                return conversations
                
        except Exception as e:
            cp.print_error(f"[Database] Erreur récupération conversations récentes: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculer les statistiques globales"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Statistiques de base
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(total_input_tokens) as total_input_tokens,
                        SUM(total_output_tokens) as total_output_tokens,
                        SUM(grand_total_tokens) as grand_total_tokens,
                        SUM(total_cost_usd) as total_cost_usd,
                        AVG(response_time) as avg_response_time,
                        MIN(response_time) as min_response_time,
                        MAX(response_time) as max_response_time,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
                    FROM conversations
                ''')
                
                stats_row = cursor.fetchone()
                
                # Statistiques par intention
                cursor.execute('''
                    SELECT 
                        JSON_EXTRACT(intent_analysis, '$.intent') as intent,
                        COUNT(*) as count
                    FROM conversations
                    WHERE intent_analysis IS NOT NULL
                    GROUP BY JSON_EXTRACT(intent_analysis, '$.intent')
                ''')
                
                intents = {}
                for row in cursor.fetchall():
                    if row["intent"]:
                        intents[row["intent"]] = row["count"]
                
                # Statistiques par spécialité
                cursor.execute('''
                    SELECT 
                        JSON_EXTRACT(intent_analysis, '$.speciality') as speciality,
                        COUNT(*) as count
                    FROM conversations
                    WHERE intent_analysis IS NOT NULL
                    AND JSON_EXTRACT(intent_analysis, '$.speciality') IS NOT NULL
                    GROUP BY JSON_EXTRACT(intent_analysis, '$.speciality')
                ''')
                
                specialities = {}
                for row in cursor.fetchall():
                    if row["speciality"]:
                        specialities[row["speciality"]] = row["count"]
                
                # Statistiques journalières (30 derniers jours)
                cursor.execute('''
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as requests,
                        SUM(total_input_tokens) as input_tokens,
                        SUM(total_output_tokens) as output_tokens,
                        SUM(grand_total_tokens) as total_tokens,
                        SUM(total_cost_usd) as cost_usd,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
                    FROM conversations
                    WHERE timestamp >= DATE('now', '-30 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                ''')
                
                daily_stats = {}
                for row in cursor.fetchall():
                    daily_stats[row["date"]] = {
                        "requests": row["requests"],
                        "tokens": {
                            "input": row["input_tokens"] or 0,
                            "output": row["output_tokens"] or 0,
                            "total": row["total_tokens"] or 0
                        },
                        "cost_usd": row["cost_usd"] or 0.0,
                        "errors": row["errors"] or 0
                    }
                
                return {
                    "total_requests": stats_row["total_requests"] or 0,
                    "total_tokens": {
                        "input": stats_row["total_input_tokens"] or 0,
                        "output": stats_row["total_output_tokens"] or 0,
                        "total": stats_row["grand_total_tokens"] or 0
                    },
                    "intents": intents,
                    "specialities": specialities,
                    "estimated_cost": {
                        "total_cost_usd": stats_row["total_cost_usd"] or 0.0
                    },
                    "performance": {
                        "avg_response_time": stats_row["avg_response_time"] or 0.0,
                        "min_response_time": stats_row["min_response_time"] or 0.0,
                        "max_response_time": stats_row["max_response_time"] or 0.0,
                        "total_measurements": stats_row["total_requests"] or 0
                    },
                    "errors": stats_row["errors"] or 0,
                    "daily_stats": daily_stats,
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            cp.print_error(f"[Database] Erreur calcul statistiques: {e}")
            return {}
    
    def get_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Obtenir le rapport journalier"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as requests,
                        SUM(total_input_tokens) as input_tokens,
                        SUM(total_output_tokens) as output_tokens,
                        SUM(grand_total_tokens) as total_tokens,
                        SUM(total_cost_usd) as cost_usd,
                        AVG(response_time) as avg_response_time,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors
                    FROM conversations
                    WHERE DATE(timestamp) = ?
                ''', (date,))
                
                row = cursor.fetchone()
                
                # Statistiques par intention pour ce jour
                cursor.execute('''
                    SELECT 
                        JSON_EXTRACT(intent_analysis, '$.intent') as intent,
                        COUNT(*) as count
                    FROM conversations
                    WHERE DATE(timestamp) = ?
                    AND intent_analysis IS NOT NULL
                    GROUP BY JSON_EXTRACT(intent_analysis, '$.intent')
                ''', (date,))
                
                intents = {}
                for intent_row in cursor.fetchall():
                    if intent_row["intent"]:
                        intents[intent_row["intent"]] = intent_row["count"]
                
                return {
                    "requests": row["requests"] or 0,
                    "tokens": {
                        "input": row["input_tokens"] or 0,
                        "output": row["output_tokens"] or 0,
                        "total": row["total_tokens"] or 0
                    },
                    "cost_usd": row["cost_usd"] or 0.0,
                    "avg_response_time": row["avg_response_time"] or 0.0,
                    "errors": row["errors"] or 0,
                    "intents": intents
                }
                
        except Exception as e:
            cp.print_error(f"[Database] Erreur rapport journalier: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Nettoyer les anciennes données"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Supprimer les anciennes conversations
                    cursor.execute('''
                        DELETE FROM conversations 
                        WHERE timestamp < DATE('now', '-{} days')
                    '''.format(days_to_keep))
                    
                    deleted_count = cursor.rowcount
                    
                    # Supprimer les opérations de tokens orphelines
                    cursor.execute('''
                        DELETE FROM token_operations 
                        WHERE session_id NOT IN (SELECT session_id FROM conversations)
                    ''')
                    
                    # Supprimer les documents contextuels orphelins
                    cursor.execute('''
                        DELETE FROM context_documents 
                        WHERE session_id NOT IN (SELECT session_id FROM conversations)
                    ''')
                    
                    conn.commit()
                    cp.print_success(f"[Database] {deleted_count} anciennes conversations supprimées")
                    return deleted_count
                    
        except Exception as e:
            cp.print_error(f"[Database] Erreur nettoyage: {e}")
            return 0
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtenir des informations sur la base de données"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Taille de la base de données
                db_size = self.db_path.stat().st_size / 1024 / 1024  # MB
                
                # Nombre d'enregistrements par table
                cursor.execute('SELECT COUNT(*) FROM conversations')
                conversations_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM token_operations')
                operations_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM context_documents')
                documents_count = cursor.fetchone()[0]
                
                # Première et dernière conversation
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM conversations')
                date_range = cursor.fetchone()
                
                return {
                    "database_path": str(self.db_path),
                    "database_size_mb": round(db_size, 2),
                    "tables": {
                        "conversations": conversations_count,
                        "token_operations": operations_count,
                        "context_documents": documents_count
                    },
                    "date_range": {
                        "first_conversation": date_range[0],
                        "last_conversation": date_range[1]
                    }
                }
                
        except Exception as e:
            cp.print_error(f"[Database] Erreur info base de données: {e}")
            return {}

    def clean_all_data(self) -> None:
        """Nettoyer toutes les données de la base"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('DELETE FROM conversations')
                    cursor.execute('DELETE FROM token_operations')
                    cursor.execute('DELETE FROM context_documents')
                    
                    conn.commit()
                    cp.print_success("[Database] Toutes les données ont été nettoyées")
                    
        except Exception as e:
            cp.print_error(f"[Database] Erreur nettoyage complet: {e}")

# Instance globale de la base de données
rag_database = RAGDatabase()
