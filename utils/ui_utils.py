import streamlit as st
import pandas as pd

def create_sidebar():
    """Create the sidebar content."""
    with st.sidebar:
        st.subheader("AI Backend Configuration")
        
        # Backend selection
        backend = st.selectbox(
            "Select AI Backend",
            ["OpenAI", "Gemini", "LM Studio"],
            key="ai_backend"
        )
        
        # API key input based on backend
        if backend == "OpenAI":
            api_key = st.text_input("OpenAI API Key", type="password", key="openai_key")
            model = st.selectbox(
                "Model",
                ["gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-oss-20b", "gpt-oss-120b", "gpt-5-2025-08-07"],
                key="openai_model"
            )
        elif backend == "Gemini":
            api_key = st.text_input("Google API Key", type="password", key="gemini_key")
            model = st.selectbox(
                "Model",
                ["gemma-3n-e2b-it", "gemma-3-27b-it", "gemini-2.5-flash", "gemini-2.5-pro"],
                key="gemini_model"
            )
        else:  # LM Studio
            api_key = None
            lm_studio_url = st.text_input(
                "LM Studio URL", 
                value="http://localhost:1234/v1",
                key="lm_studio_url"
            )
            st.info("Using currently loaded model in LM Studio")
            model = "local-model"
        
        # Store configuration in session state
        st.session_state.ai_config = {
            "backend": backend,
            "api_key": api_key,
            "model": model,
            "lm_studio_url": lm_studio_url if backend == "LM Studio" else None
        }
        
        st.divider()
        
        st.subheader("About")
        st.write("This app allows you to query databases using natural language.")
        st.write("1. Configure your AI backend above")
        st.write("2. Upload your .db, .sqlite, or .sql file in the 'Database Info' tab.")
        st.write("3. View the tables, schema, and sample data.")
        st.write("4. Switch to the 'Text to SQL' tab to ask questions in plain English.")
        st.write("5. The app will convert your question to SQL and return the results.")
        
        st.subheader("Examples")
        st.write("- 'Show me the top 5 most recent orders'")
        st.write("- 'What is the average price of products in each category?'")
        st.write("- 'Find all customers who made purchases above $100'")
        st.write("- 'Count the number of orders per month in 2023'")
        
        st.subheader("Supported File Types")
        st.write("- SQLite database files (.db, .sqlite, .sqlite3)")
        st.write("- SQL script files (.sql)")

def display_table_info(db_manager, table):
    """Display information about a single table."""
    st.write(f"### Table: {table}")
    
    # Get schema for the table
    schema = db_manager.get_table_schema(table)
    
    # Create and display schema DataFrame
    schema_df = pd.DataFrame(schema, columns=["cid", "name", "type", "notnull", "default_value", "pk"])
    st.write("Schema:")
    st.dataframe(schema_df[["name", "type", "pk"]])
    
    # Display sample data
    try:
        data_df = db_manager.get_table_preview(table)
        st.write("Preview (First 5 rows):")
        st.dataframe(data_df)
        
        # Display row count
        count = db_manager.get_row_count(table)
        st.write(f"Total rows: {count}")
    except Exception as e:
        st.error(f"Error reading data from {table}: {e}")

def display_schema_overview(db_manager):
    """Display a comprehensive overview of the database schema."""
    schema_info = db_manager.get_db_schema_info()
    
    st.subheader("Database Schema Overview")
    for table, info in schema_info.items():
        st.write(f"### Table: {table}")
        st.write(f"Columns: {', '.join(info['columns'])}")
        if info['primary_key']:
            st.write(f"Primary Key: {', '.join(info['primary_key'])}")
        if 'foreign_keys' in info and info['foreign_keys']:
            st.write("Foreign Keys:")
            for fk in info['foreign_keys']:
                st.write(f"  - {fk['column']} → {fk['references']}")

def create_new_database_form():
    """Display form for creating a new database."""
    # Initialize session state for tables if not exists
    if "new_db_tables" not in st.session_state:
        st.session_state.new_db_tables = []
    
    # Database name input (outside form for persistence)
    db_name = st.text_input("Database Name", placeholder="my_database", key="db_name_input")
    
    st.write("**Add Tables:**")
    
    # Table creation form
    with st.form("add_table_form"):
        table_name = st.text_input("Table Name", key="table_name_input")
        
        # Column definition
        st.write("**Define Columns:**")
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            column_name = st.text_input("Column Name", key="column_name_input")
        with col2:
            column_type = st.selectbox("Type", ["TEXT", "INTEGER", "REAL", "BLOB"], key="column_type_input")
        with col3:
            is_primary = st.checkbox("Primary Key", key="is_primary_input")
        with col4:
            not_null = st.checkbox("Not Null", key="not_null_input")
        
        col_add, col_clear = st.columns(2)
        with col_add:
            add_column = st.form_submit_button("Add Column", type="primary")
        with col_clear:
            clear_tables = st.form_submit_button("Clear All Tables")
        
        if add_column:
            if column_name and table_name:
                # Find or create table in session state
                table_found = False
                for table in st.session_state.new_db_tables:
                    if table["name"] == table_name:
                        table["columns"].append({
                            "name": column_name,
                            "type": column_type,
                            "primary_key": is_primary,
                            "not_null": not_null
                        })
                        table_found = True
                        break
                
                if not table_found:
                    st.session_state.new_db_tables.append({
                        "name": table_name,
                        "columns": [{
                            "name": column_name,
                            "type": column_type,
                            "primary_key": is_primary,
                            "not_null": not_null
                        }]
                    })
                
                st.success(f"Added column '{column_name}' to table '{table_name}'")
                st.rerun()
            else:
                st.error("Please provide both table name and column name.")
        
        if clear_tables:
            st.session_state.new_db_tables = []
            st.rerun()
    
    # Display current tables and columns
    if st.session_state.new_db_tables:
        st.write("**Current Tables:**")
        for table in st.session_state.new_db_tables:
            st.write(f"**{table['name']}**")
            for col in table["columns"]:
                flags = []
                if col["primary_key"]:
                    flags.append("PK")
                if col["not_null"]:
                    flags.append("NOT NULL")
                flag_str = f" ({', '.join(flags)})" if flags else ""
                st.write(f"  - {col['name']}: {col['type']}{flag_str}")
    
    # Return the current state
    if db_name and st.session_state.new_db_tables:
        return db_name, st.session_state.new_db_tables
    else:
        return None, None