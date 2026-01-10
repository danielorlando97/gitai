"""Repository for API key management."""

from typing import List, Dict, Optional
from .repository import AbstractRepository


class APIKeyRepository(AbstractRepository):
    """Repository for managing API keys."""

    def __init__(self, db_path: str = "git_splitter.db"):
        """Initialize repository with database path."""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables."""
        import sqlite3
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

    def create(self, entity: Dict) -> bool:
        """Add a new API key."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO api_keys (provider, api_key, name)
                VALUES (?, ?, ?)
            """, (entity['provider'], entity['api_key'],
                  entity.get('name')))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def read(self, entity_id: int) -> Optional[Dict]:
        """Get API key by ID."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, provider, api_key, name, is_active
            FROM api_keys
            WHERE id = ?
        """, (entity_id,))

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

    def update(self, entity_id: int, entity: Dict) -> bool:
        """Update API key (soft delete by setting is_active=0)."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE api_keys
            SET is_active = 0
            WHERE id = ?
        """, (entity_id,))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

    def delete(self, entity_id: int) -> bool:
        """Delete (deactivate) API key."""
        return self.update(entity_id, {})

    def list_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        """List all API keys with optional filters."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        provider = filters.get('provider') if filters else None

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

    def get_next_key(self, provider: str) -> Optional[Dict]:
        """Get next available API key for provider."""
        import sqlite3
        from datetime import datetime, timedelta

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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
        """Record an error for an API key."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO api_key_errors
            (api_key_id, error_type, error_message)
            VALUES (?, ?, ?)
        """, (key_id, error_type, error_message))

        conn.commit()
        conn.close()
