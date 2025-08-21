import streamlit as st
import os
import tempfile
import pandas as pd
from utils.db_utils import DatabaseManager
from utils.prompt_utils import TextToSQLProcessor
from utils.ui_utils import create_sidebar, display_table_info, display_schema_overview, create_new_database_form

# Set page config
st.set_page_config(page_title="💾 Naturally SQL", layout="wide")
st.title("💾 Naturally SQL")

# Sidebar setup with AI configuration
create_sidebar()

# Get AI configuration from session state
ai_config = st.session_state.get("ai_config", {
    "backend": "OpenAI",
    "api_key": None,
    "model": "gpt-3.5-turbo",
    "lm_studio_url": None
})

# Set environment variables for backward compatibility
if ai_config.get("api_key"):
    if ai_config["backend"] == "OpenAI":
        os.environ["OPENAI_API_KEY"] = ai_config["api_key"]
    elif ai_config["backend"] == "Gemini":
        os.environ["GOOGLE_API_KEY"] = ai_config["api_key"]

# Create tabs
tab1, tab2, tab3 = st.tabs(["Database Info", "Text to SQL", "Direct SQL"])

# Initialize session state
if "db_manager" not in st.session_state:
    st.session_state.db_manager = None

# Database Info Tab
with tab1:
    st.header("Database Information")
    
    # Create two columns for upload and create options
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upload Existing Database")
        uploaded_file = st.file_uploader("Upload Database File", type=["db", "sqlite", "sqlite3", "sql"])
        
        if uploaded_file is not None:
            # Save the uploaded file to a temporary location
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Initialize database manager
            try:
                db_manager = DatabaseManager(temp_path)
                st.session_state.db_manager = db_manager
                
                # Check if we have tables
                if db_manager.tables:
                    st.success(f"Successfully connected to database: {uploaded_file.name}")
                    # Clear new database tables from session state
                    if "new_db_tables" in st.session_state:
                        del st.session_state.new_db_tables
                else:
                    st.error("No tables found in the database or connection failed.")
            except Exception as e:
                st.error(f"Error connecting to database: {e}")
    
    with col2:
        st.subheader("Create New Database")
        db_name, tables_config = create_new_database_form()
        
        if db_name and tables_config:
            # Add option to save permanently
            save_permanently = st.checkbox("Save database permanently to current directory", 
                                         help="If unchecked, database will be created in temporary location")
            
            if st.button("Create Database", type="primary"):
                try:
                    with st.spinner("Creating new database..."):
                        db_manager = DatabaseManager.create_new_database(
                            db_name, tables_config, permanent_location=save_permanently
                        )
                        st.session_state.db_manager = db_manager
                        
                        if save_permanently:
                            st.success(f"Successfully created database: {db_name}.db in current directory")
                        else:
                            st.success(f"Successfully created database: {db_name}.db (temporary)")
                            st.info("💡 Use the 'Save to Local File' button below to save permanently")
                        
                        # Clear the tables from session state
                        if "new_db_tables" in st.session_state:
                            st.session_state.new_db_tables = []
                        st.rerun()
                except Exception as e:
                    st.error(f"Error creating database: {e}")
        elif db_name and not tables_config:
            st.info("💡 Add at least one table with columns to create the database")
        elif not db_name and tables_config:
            st.info("💡 Enter a database name to create the database")
    
    # Display database information if we have a connection
    if st.session_state.db_manager:
        st.divider()
        
        # Database actions section
        st.subheader("Database Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download database button
            try:
                db_bytes = st.session_state.db_manager.get_database_as_bytes()
                db_filename = os.path.basename(st.session_state.db_manager.file_path)
                if not db_filename.endswith('.db'):
                    db_filename = f"{db_filename}.db"
                
                st.download_button(
                    label="📥 Download Database",
                    data=db_bytes,
                    file_name=db_filename,
                    mime="application/x-sqlite3",
                    help="Download the current database file to your computer"
                )
            except Exception as e:
                st.error(f"Error preparing download: {e}")
        
        with col2:
            # Save to local file
            if st.button("💾 Save to Local File", help="Save database to current directory"):
                try:
                    db_filename = os.path.basename(st.session_state.db_manager.file_path)
                    if not db_filename.endswith('.db'):
                        db_filename = f"{db_filename}.db"
                    
                    # Save to current working directory
                    local_path = os.path.join(os.getcwd(), db_filename)
                    st.session_state.db_manager.save_database_to_file(local_path)
                    st.success(f"Database saved to: {local_path}")
                except Exception as e:
                    st.error(f"Error saving database: {e}")
        
        with col3:
            # Create backup
            if st.button("🔄 Create Backup", help="Create a timestamped backup of the database"):
                try:
                    backup_path = st.session_state.db_manager.backup_database()
                    st.success(f"Backup created: {backup_path}")
                except Exception as e:
                    st.error(f"Error creating backup: {e}")
        
        st.divider()
        
        # Database tables section with refresh button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Database Tables")
        with col2:
            if st.button("🔄 Refresh Tables", help="Refresh the list of tables and their information"):
                # Refresh the tables list
                st.session_state.db_manager._get_tables()
                st.success("Tables refreshed!")
                st.rerun()
        
        # Display tables and their information
        if st.session_state.db_manager.tables:
            for table in st.session_state.db_manager.tables:
                display_table_info(st.session_state.db_manager, table)
        else:
            st.info("No tables found in the database. Create tables using the 'Direct SQL' tab or upload a database with existing tables.")

# Text to SQL Tab
with tab2:
    st.header("Text to SQL Query")
    
    # Check if AI configuration is valid
    ai_ready = False
    if ai_config["backend"] == "LM Studio":
        ai_ready = ai_config.get("lm_studio_url") is not None
        if not ai_ready:
            st.warning("Please configure LM Studio URL in the sidebar.")
    else:
        ai_ready = ai_config.get("api_key") is not None
        if not ai_ready:
            st.warning(f"Please enter your {ai_config['backend']} API key in the sidebar.")
    
    if ai_ready:
        if st.session_state.db_manager:
            # Display current AI configuration
            st.info(f"Using {ai_config['backend']} with model: {ai_config['model']}")
            
            # Get the user's natural language query
            query = st.text_area("Enter your question about the database", height=100)
            
            if st.button("Generate SQL and Run Query"):
                if query:
                    try:
                        with st.spinner(f"Processing your query with {ai_config['backend']}..."):
                            # Initialize text to SQL processor with AI configuration
                            processor = TextToSQLProcessor(st.session_state.db_manager, ai_config)
                            
                            # Generate and execute SQL query
                            sql_query, result_df, explanation = processor.process_query(query)
                            
                            # Display the generated SQL
                            st.subheader("Generated SQL Query")
                            st.code(sql_query, language="sql")
                            
                            # Display results
                            st.subheader("Query Results")
                            st.dataframe(result_df)
                            
                            # Display explanation
                            if explanation:
                                st.subheader("Explanation")
                                st.write(explanation)
                    except Exception as e:
                        st.error(f"Error executing query: {e}")
                else:
                    st.warning("Please enter a query")
            
            # Additional feature to display all tables and their relationships
            if st.button("Show Database Schema Overview"):
                with st.spinner("Analyzing database schema..."):
                    display_schema_overview(st.session_state.db_manager)
        else:
            st.info("Please upload a database file in the 'Database Info' tab first.")

# Direct SQL Tab
with tab3:
    st.header("Direct SQL Query")
    
    if st.session_state.db_manager:
        st.info("Execute SQL commands directly against your database")
        
        # SQL query input
        sql_query = st.text_area(
            "Enter your SQL query", 
            height=150,
            placeholder="SELECT * FROM table_name LIMIT 10;"
        )
        
        # Query execution buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            execute_query = st.button("Execute Query", type="primary")
        
        with col2:
            validate_query = st.button("Validate Query")
        
        with col3:
            # Quick query templates
            template = st.selectbox(
                "Quick Templates",
                ["Custom Query", "Show All Tables", "Count Rows", "Show Schema"],
                key="sql_template"
            )
        
        # Handle template selection
        if template != "Custom Query":
            if template == "Show All Tables":
                sql_query = "SELECT name FROM sqlite_master WHERE type='table';"
            elif template == "Count Rows":
                if st.session_state.db_manager.tables:
                    first_table = st.session_state.db_manager.tables[0]
                    sql_query = f"SELECT COUNT(*) as row_count FROM {first_table};"
            elif template == "Show Schema":
                if st.session_state.db_manager.tables:
                    first_table = st.session_state.db_manager.tables[0]
                    sql_query = f"PRAGMA table_info({first_table});"
            
            # Update the text area with template
            st.rerun()
        
        # Validate query
        if validate_query and sql_query:
            try:
                # Simple validation - check if it's a SELECT statement for safety
                query_upper = sql_query.strip().upper()
                if query_upper.startswith(('SELECT', 'WITH')):
                    st.success("✅ Query appears to be valid (SELECT/WITH statement)")
                elif query_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE')):
                    st.warning("⚠️ This is a data modification query. Use with caution!")
                else:
                    st.info("ℹ️ Query syntax will be validated when executed")
            except Exception as e:
                st.error(f"Query validation error: {e}")
        
        # Execute query
        if execute_query and sql_query:
            try:
                with st.spinner("Executing SQL query..."):
                    # Check if this is a data modification query
                    query_upper = sql_query.strip().upper()
                    is_modification = query_upper.startswith(('INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE'))
                    
                    # Check if there are multiple statements
                    statements = [stmt.strip() for stmt in sql_query.split(';') if stmt.strip()]
                    
                    if len(statements) > 1:
                        # Multiple queries
                        st.subheader("Multiple Query Results")
                        results = st.session_state.db_manager.execute_multiple_queries(sql_query)
                        
                        for i, result in enumerate(results, 1):
                            st.write(f"**Query {i}:** `{result['query']}`")
                            
                            if result['success']:
                                if len(result['result']) > 0 and 'Result' not in result['result'].columns:
                                    # Data-returning query
                                    st.dataframe(result['result'], use_container_width=True)
                                    st.info(f"Returned {len(result['result'])} rows")
                                else:
                                    # Non-data-returning query
                                    st.success("✅ Executed successfully")
                            else:
                                st.error(f"❌ Error: {result['error']}")
                            
                            st.divider()
                    else:
                        # Single query
                        result_df = st.session_state.db_manager.execute_query(sql_query)
                        
                        # Display results
                        st.subheader("Query Results")
                        
                        if len(result_df) > 0 and 'Result' not in result_df.columns:
                            # Data-returning query
                            st.dataframe(result_df, use_container_width=True)
                            
                            # Show result summary
                            st.info(f"Query returned {len(result_df)} rows and {len(result_df.columns)} columns")
                            
                            # Option to download results
                            csv = result_df.to_csv(index=False)
                            st.download_button(
                                label="Download results as CSV",
                                data=csv,
                                file_name="query_results.csv",
                                mime="text/csv"
                            )
                        else:
                            # Non-data-returning query
                            if is_modification:
                                st.success("✅ Data modification query executed successfully")
                                st.warning("💾 Remember to save your database to preserve changes permanently!")
                            else:
                                st.success("✅ Query executed successfully")
                    
                    # Show save reminder for modification queries
                    if is_modification:
                        st.info("💡 Your changes are in memory. Use the 'Database Actions' in the 'Database Info' tab to save permanently.")
                        
            except Exception as e:
                st.error(f"Query execution failed: {e}")
                
                # Provide helpful error suggestions
                error_str = str(e).lower()
                if "no such table" in error_str:
                    st.info("💡 Tip: Check available tables in the 'Database Info' tab")
                elif "syntax error" in error_str:
                    st.info("💡 Tip: Check your SQL syntax. Common issues include missing quotes or semicolons")
                elif "no such column" in error_str:
                    st.info("💡 Tip: Check column names in the table schema")
        
        # Display available tables for reference
        if st.session_state.db_manager.tables:
            with st.expander("Available Tables", expanded=False):
                st.write("**Tables in your database:**")
                for table in st.session_state.db_manager.tables:
                    st.write(f"• {table}")
                
                # Show quick schema info
                selected_table = st.selectbox("View table schema:", st.session_state.db_manager.tables)
                if selected_table:
                    schema = st.session_state.db_manager.get_table_schema(selected_table)
                    schema_df = pd.DataFrame(schema, columns=["cid", "name", "type", "notnull", "default_value", "pk"])
                    st.dataframe(schema_df[["name", "type", "pk"]], use_container_width=True)
        
        # SQL Reference
        with st.expander("SQL Reference", expanded=False):
            st.markdown("""
            **Common SQL Commands:**
            - `SELECT * FROM table_name` - Get all data from a table
            - `SELECT column1, column2 FROM table_name` - Get specific columns
            - `SELECT * FROM table_name WHERE condition` - Filter data
            - `SELECT COUNT(*) FROM table_name` - Count rows
            - `SELECT * FROM table_name ORDER BY column_name` - Sort results
            - `SELECT * FROM table_name LIMIT 10` - Limit results
            
            **SQLite Specific:**
            - `PRAGMA table_info(table_name)` - Show table schema
            - `SELECT name FROM sqlite_master WHERE type='table'` - List all tables
            """)
    
    else:
        st.info("Please upload or create a database in the 'Database Info' tab first.")
