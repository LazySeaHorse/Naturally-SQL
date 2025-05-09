import streamlit as st
import os
import tempfile
import pandas as pd
from utils.db_utils import DatabaseManager
from utils.prompt_utils import TextToSQLProcessor
from utils.ui_utils import create_sidebar, display_table_info, display_schema_overview

# Set page config
st.set_page_config(page_title="Text to SQL Query App", layout="wide")
st.title("Text to SQL Query App")

# API Key Input and sidebar setup
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
os.environ["OPENAI_API_KEY"] = api_key
create_sidebar()

# Create tabs
tab1, tab2 = st.tabs(["Database Info", "Text to SQL"])

# Initialize session state
if "db_manager" not in st.session_state:
    st.session_state.db_manager = None

# Database Info Tab
with tab1:
    st.header("Database Information")
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
                st.subheader("Database Tables")
                
                # Display tables and their information
                for table in db_manager.tables:
                    display_table_info(db_manager, table)
            else:
                st.error("No tables found in the database or connection failed.")
        except Exception as e:
            st.error(f"Error connecting to database: {e}")

# Text to SQL Tab
with tab2:
    st.header("Text to SQL Query")
    
    if api_key:
        if st.session_state.db_manager:
            # Get the user's natural language query
            query = st.text_area("Enter your question about the database", height=100)
            
            if st.button("Generate SQL and Run Query"):
                if query:
                    try:
                        with st.spinner("Processing your query..."):
                            # Initialize text to SQL processor
                            processor = TextToSQLProcessor(st.session_state.db_manager, api_key)
                            
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
    else:
        st.warning("Please enter your OpenAI API key in the sidebar.")
