import streamlit as st
import pandas as pd

def create_sidebar():
    """Create the sidebar content."""
    with st.sidebar:
        st.subheader("About")
        st.write("This app allows you to query databases using natural language.")
        st.write("1. Upload your .db, .sqlite, or .sql file in the 'Database Info' tab.")
        st.write("2. View the tables, schema, and sample data.")
        st.write("3. Switch to the 'Text to SQL' tab to ask questions in plain English.")
        st.write("4. The app will convert your question to SQL and return the results.")
        
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