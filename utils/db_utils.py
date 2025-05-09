import sqlite3
import pandas as pd
import os
from sqlalchemy import create_engine, inspect, text
import tempfile

class DatabaseManager:
    def __init__(self, file_path):
        """Initialize database connection based on file type."""
        self.file_path = file_path
        self.tables = []
        self.conn = None
        self.engine = None
        
        # Handle different file types
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in ['.db', '.sqlite', '.sqlite3']:
            # Direct SQLite database file
            self._connect_sqlite()
        elif file_ext == '.sql':
            # SQL script file - create temporary database and execute script
            self._create_db_from_sql()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Get tables
        self._get_tables()
    
    def _connect_sqlite(self):
        """Connect to an existing SQLite database file."""
        try:
            # SQLite connection
            self.conn = sqlite3.connect(self.file_path)
            
            # SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{self.file_path}")
        except Exception as e:
            raise Exception(f"Failed to connect to SQLite database: {e}")
    
    def _create_db_from_sql(self):
        """Create a temporary database from SQL script file."""
        try:
            # Create temporary database
            temp_db_path = os.path.join(tempfile.gettempdir(), 'temp_db.sqlite')
            
            # Connect to the temporary database
            self.conn = sqlite3.connect(temp_db_path)
            
            # Read SQL script
            with open(self.file_path, 'r') as f:
                sql_script = f.read()
            
            # Execute the script
            self.conn.executescript(sql_script)
            self.conn.commit()
            
            # Update file path to the new temporary database
            self.file_path = temp_db_path
            
            # SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{self.file_path}")
        except Exception as e:
            raise Exception(f"Failed to create database from SQL file: {e}")
    
    def _get_tables(self):
        """Get all tables in the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            self.tables = [table[0] for table in cursor.fetchall()]
        except Exception as e:
            raise Exception(f"Failed to get tables: {e}")
    
    def get_table_schema(self, table_name):
        """Get schema information for a table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            return cursor.fetchall()
        except Exception as e:
            raise Exception(f"Failed to get schema for table {table_name}: {e}")
    
    def get_table_preview(self, table_name, limit=5):
        """Get preview data for a table."""
        try:
            return pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", self.conn)
        except Exception as e:
            raise Exception(f"Failed to get preview for table {table_name}: {e}")
    
    def get_row_count(self, table_name):
        """Get the number of rows in a table."""
        try:
            result = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table_name}", self.conn)
            return result.iloc[0, 0]
        except Exception as e:
            raise Exception(f"Failed to get row count for table {table_name}: {e}")
    
    def get_foreign_keys(self, table_name):
        """Get foreign key information for a table."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            return cursor.fetchall()
        except Exception as e:
            return []  # Some databases might not support this
    
    def execute_query(self, sql_query):
        """Execute an SQL query and return the results as a DataFrame."""
        try:
            return pd.read_sql_query(sql_query, self.conn)
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")
    
    def get_db_schema_info(self):
        """Get comprehensive schema information for all tables."""
        schema_info = {}
        for table in self.tables:
            # Get columns info
            columns = self.get_table_schema(table)
            
            schema_info[table] = {
                "columns": [col[1] for col in columns],
                "primary_key": [col[1] for col in columns if col[5] == 1],
                "column_types": {col[1]: col[2] for col in columns}
            }
            
            # Get foreign keys
            foreign_keys = self.get_foreign_keys(table)
            if foreign_keys:
                schema_info[table]["foreign_keys"] = [
                    {"column": fk[3], "references": f"{fk[2]}.{fk[4]}"} for fk in foreign_keys
                ]
        
        return schema_info
    
    def get_sqlalchemy_url(self):
        """Get SQLAlchemy connection URL for the database."""
        return f"sqlite:///{self.file_path}"
    
    def __del__(self):
        """Close connection when object is destroyed."""
        if self.conn:
            self.conn.close()
