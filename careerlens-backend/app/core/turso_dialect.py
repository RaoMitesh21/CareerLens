"""
app/core/turso_dialect.py — Custom Turso Dialect for SQLAlchemy
===============================================================
Uses our custom pure-Python `turso_dbapi.py` wrapper around `libsql-client`.
"""

from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.engine.default import DefaultDialect

class SQLiteDialect_Turso(SQLiteDialect_pysqlite):
    name = "turso"
    driver = "libsql_client"
    
    # We must explicitly set this for SQLAlchemy 1.4/2.0
    supports_statement_cache = True
    
    @classmethod
    def import_dbapi(cls):
        import app.core.turso_dbapi as turso_dbapi
        return turso_dbapi

    def on_connect(self):
        # Disable the default SQLite on_connect which tries to run PRAGMAs
        def connect(conn):
            pass
        return connect

    def get_isolation_level(self, dbapi_conn):
        return None

    def get_default_isolation_level(self, dbapi_conn):
        return None

    def has_table(self, connection, table_name, schema=None, **kw):
        statement = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        cursor = connection.exec_driver_sql(statement, (table_name,))
        return cursor.fetchone() is not None

    def create_connect_args(self, url):
        # URL is: sqlite+libsql://...
        # Clean up the prefix
        url_full = str(url)
        if url_full.startswith("sqlite+https://"):
            actual_url = url_full.replace("sqlite+https://", "https://")
        elif url_full.startswith("sqlite+libsql://"):
            actual_url = url_full.replace("sqlite+libsql://", "https://")
        elif url_full.startswith("turso://"):
            actual_url = url_full.replace("turso://", "https://")
        elif url_full.startswith("libsql://"):
            actual_url = url_full.replace("libsql://", "https://")
        else:
            actual_url = url_full
            
        kwargs = {
            "database": actual_url
        }
        return ([], kwargs)

dialect = SQLiteDialect_Turso
