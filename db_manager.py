#!/usr/bin/env python3
"""
Gestor de base de datos SQLite para API keys de LLMs.
"""

import sqlite3
import os
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class APIKeyManager:
    """Gestor de API keys con rotación automática."""
    
    def __init__(self, db_path: str = "git_splitter.db"):
        """Inicializa el gestor de base de datos."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Inicializa la base de datos con las tablas necesarias."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                api_key TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                use_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(provider, api_key)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_key_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_id INTEGER,
                error_type TEXT,
                error_message TEXT,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_key(self, provider: str, api_key: str, 
                name: Optional[str] = None) -> bool:
        """Añade una nueva API key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO api_keys (provider, api_key, name)
                VALUES (?, ?, ?)
            """, (provider, api_key, name))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def list_keys(self, provider: Optional[str] = None) -> List[Dict]:
        """Lista todas las API keys, opcionalmente filtradas por provider."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if provider:
            cursor.execute("""
                SELECT id, provider, name, created_at, last_used, 
                       use_count, is_active
                FROM api_keys
                WHERE provider = ? AND is_active = 1
                ORDER BY last_used DESC, created_at DESC
            """, (provider,))
        else:
            cursor.execute("""
                SELECT id, provider, name, created_at, last_used, 
                       use_count, is_active
                FROM api_keys
                WHERE is_active = 1
                ORDER BY provider, last_used DESC
            """)
        
        keys = []
        for row in cursor.fetchall():
            keys.append({
                'id': row['id'],
                'provider': row['provider'],
                'name': row['name'],
                'created_at': row['created_at'],
                'last_used': row['last_used'],
                'use_count': row['use_count'],
                'is_active': bool(row['is_active'])
            })
        
        conn.close()
        return keys
    
    def delete_key(self, key_id: int) -> bool:
        """Elimina (desactiva) una API key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE api_keys
            SET is_active = 0
            WHERE id = ?
        """, (key_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def get_next_key(self, provider: str) -> Optional[Dict]:
        """Obtiene la siguiente API key disponible para un provider."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener keys activas que no han tenido errores recientes
        # (últimos 5 minutos)
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        cursor.execute("""
            SELECT ak.id, ak.provider, ak.api_key, ak.name
            FROM api_keys ak
            LEFT JOIN api_key_errors ake ON ak.id = ake.api_key_id
                AND ake.occurred_at > ?
                AND ake.error_type = 'RATE_LIMIT'
            WHERE ak.provider = ? 
                AND ak.is_active = 1
                AND ake.id IS NULL
            ORDER BY 
                ak.last_used ASC,
                ak.use_count ASC,
                ak.created_at ASC
            LIMIT 1
        """, (cutoff_time.isoformat(), provider))
        
        row = cursor.fetchone()
        if row:
            key_data = {
                'id': row['id'],
                'provider': row['provider'],
                'api_key': row['api_key'],
                'name': row['name']
            }
            # Actualizar last_used y use_count
            cursor.execute("""
                UPDATE api_keys
                SET last_used = CURRENT_TIMESTAMP,
                    use_count = use_count + 1
                WHERE id = ?
            """, (row['id'],))
            conn.commit()
            conn.close()
            return key_data
        
        conn.close()
        return None
    
    def record_error(self, key_id: int, error_type: str, 
                    error_message: str) -> None:
        """Registra un error para una API key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO api_key_errors 
            (api_key_id, error_type, error_message)
            VALUES (?, ?, ?)
        """, (key_id, error_type, error_message))
        
        conn.commit()
        conn.close()
    
    def get_key_by_id(self, key_id: int) -> Optional[Dict]:
        """Obtiene una API key por su ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, provider, api_key, name, is_active
            FROM api_keys
            WHERE id = ?
        """, (key_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'provider': row['provider'],
                'api_key': row['api_key'],
                'name': row['name'],
                'is_active': bool(row['is_active'])
            }
        return None



