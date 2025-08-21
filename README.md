# 💾 Naturally SQL

A powerful Streamlit application that converts natural language questions into SQL queries and executes them against databases. Create, upload, explore, and query databases using plain English with support for multiple AI backends.

## Features

### 🤖 Multiple AI Backend Support
- **OpenAI**: GPT-5 Mini, GPT-5 Nano, GPT-OSS models, and GPT-5
- **Google Gemini**: Gemma-3n, Gemma-3-27b, Gemini-2.5 Flash, and Gemini-2.5 Pro
- **LM Studio**: Use local models running on your machine

### 📊 Database Management
- **Upload**: SQLite database files (.db, .sqlite, .sqlite3) or SQL script files (.sql)
- **Create**: Build new databases from scratch with custom tables and columns
- **Explore**: View database tables, schema, column types, and preview data
- **Download**: Export databases to your local machine
- **Backup**: Create timestamped backups of your databases
- **Save**: Persist databases permanently or work with temporary copies

### 🔍 Query Capabilities
- **Natural Language**: Convert plain English questions to SQL queries
- **Direct SQL**: Execute raw SQL commands with syntax validation
- **Multiple Queries**: Run multiple SQL statements in sequence
- **Query Templates**: Quick access to common SQL patterns
- **Results Export**: Download query results as CSV files

### 📈 Advanced Features
- **Schema Analysis**: Comprehensive database structure overview
- **Table Relationships**: Identify foreign keys and table connections
- **Query Explanations**: AI-powered explanations of query results
- **Error Handling**: Helpful suggestions for common SQL errors
- **Real-time Validation**: Check SQL syntax before execution

## Installation

1. Clone this repository:
```bash
git clone https://github.com/LazySeaHorse/Naturally-SQL
cd naturally-sql
```

2. Create a virtual environment and install the required packages:
```bash
python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
pip install -r requirements.txt
```

3. Run the Streamlit app:
```bash
streamlit run app.py
```

# Demo

https://github.com/user-attachments/assets/b91d789e-5e3b-4052-9660-43925227d37e

### Dependencies
- streamlit
- langchain
- langchain_community
- openai
- pandas
- sqlalchemy
- langchain-google-genai
- requests

## Usage

### Getting Started
1. **Configure AI Backend**: Choose between OpenAI, Gemini, or LM Studio in the sidebar
2. **Set up Authentication**: Enter your API key (for OpenAI/Gemini) or LM Studio URL
3. **Load Database**: Upload existing database files or create new ones
4. **Start Querying**: Use natural language or direct SQL to interact with your data

### Detailed Workflow

#### Database Setup
- **Upload Existing**: Drag and drop .db, .sqlite, .sqlite3, or .sql files
- **Create New**: Use the interactive form to build databases with custom tables and columns
- **Explore Structure**: View table schemas, data types, and relationships

#### Querying Data
- **Natural Language Tab**: Ask questions in plain English
  - "Show me the top 5 customers by revenue"
  - "What's the average order value by month?"
  - "Find all products with low inventory"
- **Direct SQL Tab**: Write and execute raw SQL queries
  - Syntax validation and error suggestions
  - Query templates for common operations
  - Multiple statement execution

#### Managing Results
- **View Results**: Interactive data tables with sorting and filtering
- **Export Data**: Download query results as CSV files
- **Save Changes**: Persist database modifications permanently

## Project Structure

```
naturally-sql/
├── app.py                 # Main Streamlit application with three-tab interface
├── requirements.txt       # Python dependencies
├── utils/
│   ├── db_utils.py       # Database management, creation, and query execution
│   ├── prompt_utils.py   # AI backend integration and prompt templates
│   └── ui_utils.py       # User interface components and forms
└── README.md             # This file
```

### Core Components

- **`app.py`**: Main application with Database Info, Text to SQL, and Direct SQL tabs
- **`db_utils.py`**: DatabaseManager class handling SQLite operations, schema analysis, and file management
- **`prompt_utils.py`**: TextToSQLProcessor with multi-backend AI support (OpenAI, Gemini, LM Studio)
- **`ui_utils.py`**: Reusable UI components for database creation, table display, and configuration

## AI Backend Configuration

### OpenAI
- Requires OpenAI API key
- Supports latest GPT models including GPT-5 series
- Best for complex query generation and explanations

### Google Gemini
- Requires Google API key
- Supports Gemini 2.5 and Gemma models
- Good alternative to OpenAI with competitive performance

### LM Studio
- No API key required
- Uses locally running models
- Complete privacy and offline capability
- Requires LM Studio installation and running model

## System Requirements

- Python 3.8 or higher
- 4GB+ RAM (8GB+ recommended for local AI models)
- Internet connection (for cloud AI backends)
- Modern web browser

### Natural Language Examples
- "Show me the top 10 customers by total purchase amount"
- "What's the average price of products in each category?"
- "Find all orders placed in the last 30 days"
- "Which products have never been ordered?"
- "Calculate monthly revenue growth for 2023"
- "List customers who made more than 5 purchases"

### Direct SQL Examples
```sql
-- View all tables
SELECT name FROM sqlite_master WHERE type='table';

-- Get table schema
PRAGMA table_info(customers);

-- Complex join query
SELECT c.name, COUNT(o.id) as order_count, SUM(o.total) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
ORDER BY total_spent DESC;
```

## Advanced Features

### Database Creation
Create custom databases with:
- Multiple tables with relationships
- Various data types (TEXT, INTEGER, REAL, BLOB)
- Primary keys and constraints
- Foreign key relationships

### Query Analysis
- **Schema Overview**: Visual representation of table relationships
- **Query Explanations**: AI-powered explanations of results
- **Error Suggestions**: Helpful hints for common SQL mistakes
- **Performance Tips**: Optimization suggestions for complex queries

### Data Management
- **Backup System**: Automatic timestamped backups
- **Export Options**: Download databases and query results
- **Temporary vs Permanent**: Choose between temporary testing and permanent storage
- **Multi-format Support**: SQLite databases and SQL script files

## Troubleshooting

### Common Issues

**API Key Errors**
- Ensure your API key is valid and has sufficient credits
- Check that the correct backend is selected
- Verify API key permissions for the chosen model

**Database Connection Issues**
- Ensure uploaded files are valid SQLite databases or SQL scripts
- Check file permissions and size limits
- Try creating a new database if upload fails

**Query Execution Errors**
- Use the query validation feature before execution
- Check table and column names in the Database Info tab
- Review SQL syntax for common mistakes

**LM Studio Connection**
- Ensure LM Studio is running and a model is loaded
- Verify the correct URL (default: http://localhost:1234/v1)
- Check that the model supports chat completions

### Performance Tips
- Use LIMIT clauses for large datasets
- Create indexes for frequently queried columns
- Use the schema overview to understand table relationships
- Test queries with small datasets first