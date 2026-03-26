"""
app/core/turso_dialect.py — Custom Turso/Hrana Dialect for SQLAlchemy
=====================================================================
Custom SQLAlchemy dialect that disables PRAGMA detection for Turso compatibility.
"""

from sqlalchemy.dialects.sqlite.base import SQLiteDialect
from sqlalchemy_libsql import SQLiteDialect_libsql


class SQLiteDialect_Turso(SQLiteDialect_libsql):
    """
    Custom libsql dialect optimized for Turso.
    Disables PRAGMA execution that Turso/Hrana rejects.
    """
    
    def initialize(self, connection):
        """Override to skip isolation level detection that uses PRAGMA."""
        # Call parent initialize but catch PRAGMA errors
        try:
            super().initialize(connection)
        except Exception as e:
            if "PRAGMA" in str(e) or "405" in str(e):
                # Skip PRAGMA initialization - Turso doesn't support these
                self.server_version_info = None
                self.default_isolation_level = None
            else:
                raise
    
    def get_isolation_level(self, dbapi_conn):
        """Override to disable PRAGMA read_uncommitted check."""
        # Return None to disable isolation level checking
        return None
    
    def get_default_isolation_level(self, dbapi_conn):
        """Override to disable PRAGMA read_uncommitted check."""
        # Return None - Turso doesn't support isolation level detection
        return None
    
    def has_table(self, connection, table_name, schema=None):
        """Override to avoid PRAGMA table_info."""
        # Query sqlite_master table instead of using PRAGMA
        statement = (
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        )
        cursor = connection.exec_driver_sql(statement, (table_name,))
        return cursor.fetchone() is not None
    
    def _get_table_pragma(self, connection, pragmaname, table_name=None, schema=None):
        """Override to skip PRAGMA commands that aren't supported."""
        # Return empty list instead of executing PRAGMA
        # This prevents table introspection errors
        return []
    
    def _get_column_info(self, connection, table_name, schema=None):
        """Override to skip table_info PRAGMA."""
        # We can't reliably get column info, so return empty
        return {}

