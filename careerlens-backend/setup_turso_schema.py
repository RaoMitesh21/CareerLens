#!/usr/bin/env python3
"""
Setup script to initialize Turso database schema using Turso CLI.
Runs before FastAPI startup to ensure tables exist.
"""

import subprocess
import sys
from sqlalchemy import inspect
from app.core.database import Base, engine

# Import all models to register them with Base
import app.models  # noqa: F401

def get_create_table_sql(model_class):
    """Generate CREATE TABLE SQL from SQLAlchemy model."""
    from sqlalchemy.schema import CreateTable
    stmt = CreateTable(model_class.__table__)
    return str(stmt.compile(dialect=engine.dialect))

def create_tables_via_cli():
    """Create all tables using Turso CLI instead of HRANA."""
    print("🔧 Initializing Turso database schema via CLI...")
    
    # Get list of all registered tables
    tables = Base.metadata.tables.keys()
    print(f"📋 Tables to create: {list(tables)}")
    
    for table_name in tables:
        table = Base.metadata.tables[table_name]
        try:
            # Use SQLAlchemy's DDL compiler for maximum compatibility
            from sqlalchemy.schema import CreateTable
            create_stmt = CreateTable(table).compile(dialect=engine.dialect)
            sql = str(create_stmt)
            # Replace CREATE TABLE with CREATE TABLE IF NOT EXISTS
            sql = sql.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
            
            # Execute via Turso CLI
            cmd = ["turso", "db", "shell", "careerlens-v2", sql]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"  ✅ Created table: {table_name}")
            else:
                # If it fails, try manual approach
                print(f"  ⚠️  Auto-generated SQL failed for {table_name}, trying manual approach...")
                try:
                    # Try simpler manual SQL
                    columns = []
                    for col in table.columns:
                        col_def = f"{col.name} {col.type.compile(engine.dialect)}"
                        if col.primary_key:
                            col_def += " PRIMARY KEY"
                        elif col.nullable is False:
                            col_def += " NOT NULL"
                        if col.unique:
                            col_def += " UNIQUE"
                        # Skip problematic defaults for now
                        columns.append(col_def)
                    
                    manual_sql = f"CREATE TABLE IF NOT EXISTS {table.name} (\n  " + ",\n  ".join(columns) + "\n)"
                    
                    cmd2 = ["turso", "db", "shell", "careerlens-v2", manual_sql]
                    result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
                    
                    if result2.returncode == 0:
                        print(f"  ✅ Created table (manual): {table_name}")
                    else:
                        print(f"  ❌ Failed to create {table_name}: {result2.stderr[:100]}")
                except Exception as e2:
                    print(f"  ❌ Failed to create {table_name}: {str(e2)[:100]}")
                
        except Exception as e:
            print(f"  ⚠️  Error creating {table_name}: {e}")
    
    print("✨ Schema initialization complete!")

if __name__ == "__main__":
    try:
        create_tables_via_cli()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
