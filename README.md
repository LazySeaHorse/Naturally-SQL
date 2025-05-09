# Text to SQL Streamlit App

A Streamlit application that converts natural language questions into SQL queries and executes them against uploaded databases.

# Demo

https://github.com/user-attachments/assets/b91d789e-5e3b-4052-9660-43925227d37e

## Features

- Upload SQLite database files (.db, .sqlite, .sqlite3) or SQL script files (.sql)
- Explore database tables, schema, and preview data
- Convert natural language questions to SQL queries using OpenAI's GPT models
- Execute SQL queries and view results
- Get explanations of query results

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install streamlit langchain langchain_community openai pandas sqlalchemy
```

3. Run the Streamlit app:

```bash
streamlit run app.py
```

## Usage

1. Enter your OpenAI API key in the sidebar
2. Upload a database file (.db, .sqlite, .sqlite3) or SQL script file (.sql)
3. Explore the database structure in the "Database Info" tab
4. Switch to the "Text to SQL" tab to ask questions about your data
5. Enter your question in natural language and click "Generate SQL and Run Query"

## Project Structure

- `app.py`: Main Streamlit application
- `utils/`
  - `db_utils.py`: Database management functions
  - `prompt_utils.py`: Prompt templates and LLM utilities
  - `ui_utils.py`: UI helper functions

## Requirements

- Python 3.8 or higher
- OpenAI API key
- Streamlit
- Langchain
- SQLAlchemy
- Pandas