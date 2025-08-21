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
            # SQLite connection with thread safety disabled for Streamlit
            self.conn = sqlite3.connect(self.file_path, check_same_thread=False)
            
            # SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{self.file_path}")
        except Exception as e:
            raise Exception(f"Failed to connect to SQLite database: {e}")
    
    def _create_db_from_sql(self):
        """Create a temporary database from SQL script file."""
        try:
            # Create temporary database
            temp_db_path = os.path.join(tempfile.gettempdir(), 'temp_db.sqlite')
            
            # Connect to the temporary database with thread safety disabled for Streamlit
            self.conn = sqlite3.connect(temp_db_path, check_same_thread=False)
            
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
            # Clean up the query
            sql_query = sql_query.strip()
            
            # Check if this is a data-returning query (SELECT, WITH, PRAGMA)
            query_upper = sql_query.upper()
            is_select_query = query_upper.startswith(('SELECT', 'WITH', 'PRAGMA'))
            
            if is_select_query:
                # For SELECT queries, use pandas to get DataFrame
                return pd.read_sql_query(sql_query, self.conn)
            else:
                # For DDL/DML queries (CREATE, INSERT, UPDATE, DELETE, etc.)
                cursor = self.conn.cursor()
                
                # Handle multiple statements
                statements = [stmt.strip() for stmt in sql_query.split(';') if stmt.strip()]
                
                if len(statements) > 1:
                    # Multiple statements - execute each one
                    for stmt in statements:
                        cursor.execute(stmt)
                else:
                    # Single statement
                    cursor.execute(sql_query)
                
                self.conn.commit()
                
                # Refresh tables list in case new tables were created
                self._get_tables()
                
                # Return success DataFrame for non-SELECT queries
                return pd.DataFrame({'Result': ['Query executed successfully']})
                
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")
    
    def execute_multiple_queries(self, sql_queries):
        """Execute multiple SQL queries and return results for each."""
        results = []
        queries = [q.strip() for q in sql_queries.split(';') if q.strip()]
        
        for query in queries:
            try:
                result = self.execute_query(query)
                results.append({'query': query, 'result': result, 'success': True})
            except Exception as e:
                results.append({'query': query, 'error': str(e), 'success': False})
        
        return results
    
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
    
    def save_database_to_file(self, output_path):
        """Save the current database to a specified file path."""
        try:
            import shutil
            
            # Ensure all changes are committed
            if self.conn:
                self.conn.commit()
            
            # Copy the current database file to the output path
            shutil.copy2(self.file_path, output_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to save database to {output_path}: {e}")
    
    def get_database_as_bytes(self):
        """Get the database file as bytes for download."""
        try:
            # Ensure all changes are committed
            if self.conn:
                self.conn.commit()
            
            with open(self.file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read database file: {e}")
    
    def backup_database(self, backup_path=None):
        """Create a backup of the current database."""
        try:
            import shutil
            from datetime import datetime
            
            if backup_path is None:
                # Generate backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.splitext(os.path.basename(self.file_path))[0]
                backup_path = f"{base_name}_backup_{timestamp}.db"
            
            # Ensure all changes are committed
            if self.conn:
                self.conn.commit()
            
            shutil.copy2(self.file_path, backup_path)
            return backup_path
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    @classmethod
    def create_new_database(cls, db_name, tables_config, permanent_location=False):
        """Create a new SQLite database with specified tables and columns."""
        import tempfile
        
        # Create database file path
        if permanent_location:
            # Save in current working directory
            db_path = f"{db_name}.db"
        else:
            # Save in temporary directory (default behavior)
            temp_dir = tempfile.mkdtemp()
            db_path = os.path.join(temp_dir, f"{db_name}.db")
        
        try:
            # Create connection with thread safety disabled for Streamlit
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Create tables
            for table_config in tables_config:
                table_name = table_config["name"]
                columns = table_config["columns"]
                
                # Build CREATE TABLE statement
                column_definitions = []
                for col in columns:
                    col_def = f"{col['name']} {col['type']}"
                    if col.get("primary_key"):
                        col_def += " PRIMARY KEY"
                    if col.get("not_null"):
                        col_def += " NOT NULL"
                    column_definitions.append(col_def)
                
                create_table_sql = f"CREATE TABLE {table_name} ({', '.join(column_definitions)})"
                cursor.execute(create_table_sql)
            
            conn.commit()
            conn.close()
            
            # Return new DatabaseManager instance
            return cls(db_path)
            
        except Exception as e:
            if conn:
                conn.close()
            raise Exception(f"Failed to create database: {e}")
    
    def __del__(self):
        """Close connection when object is destroyed."""
        if self.conn:
            self.conn.close()
