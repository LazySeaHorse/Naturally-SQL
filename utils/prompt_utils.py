from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
import requests
import json

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class LMStudioLLM:
    """Custom LLM wrapper for LM Studio local API."""
    def __init__(self, base_url="http://localhost:1234/v1"):
        self.base_url = base_url
        self.temperature = 0
    
    def invoke(self, prompt):
        """Send request to LM Studio API."""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.temperature,
                    "max_tokens": 1000
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"LM Studio API error: {str(e)}")

class TextToSQLProcessor:
    def __init__(self, db_manager, ai_config):
        """Initialize the text to SQL processor with configurable AI backend."""
        self.db_manager = db_manager
        self.ai_config = ai_config
        self.llm = self._create_llm()
        
        # Create SQLAlchemy database
        self.db = SQLDatabase.from_uri(db_manager.get_sqlalchemy_url())
    
    def _create_llm(self):
        """Create LLM instance based on configuration."""
        backend = self.ai_config["backend"]
        model = self.ai_config["model"]
        api_key = self.ai_config["api_key"]
        
        if backend == "OpenAI":
            return ChatOpenAI(
                temperature=0, 
                model_name=model, 
                api_key=api_key
            )
        elif backend == "Gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("langchain-google-genai package is required for Gemini support. Install with: pip install langchain-google-genai")
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0
            )
        elif backend == "LM Studio":
            return LMStudioLLM(self.ai_config["lm_studio_url"])
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    
    def generate_tables_info(self):
        """Generate formatted information about database tables for the prompt."""
        tables_info = ""
        for table in self.db_manager.tables:
            tables_info += f"Table: {table}\n"
            schema = self.db_manager.get_table_schema(table)
            for col in schema:
                tables_info += f"  - {col[1]} ({col[2]})\n"
            tables_info += "\n"
        return tables_info
    
    def process_query(self, query):
        """Process a natural language query and return SQL, results, and explanation."""
        try:
            if self.ai_config["backend"] == "LM Studio":
                # Handle LM Studio differently since it doesn't work with LangChain chains
                sql_query = self._generate_sql_with_lm_studio(query)
            else:
                # Use LangChain for OpenAI and Gemini
                query_chain = create_sql_query_chain(self.llm, self.db)
                sql_query = query_chain.invoke({"question": query})
            
            # Clean up the SQL query (remove markdown formatting if present)
            sql_query = self._clean_sql_query(sql_query)
            
            # Execute the query
            result_df = self.db_manager.execute_query(sql_query)
            
            # Generate explanation if there are results
            explanation = None
            if not result_df.empty:
                explanation = self._generate_explanation(query, sql_query, result_df)
            
            return sql_query, result_df, explanation
        except Exception as e:
            raise Exception(f"Error processing query with {self.ai_config['backend']}: {str(e)}")
    
    def _generate_sql_with_lm_studio(self, query):
        """Generate SQL query using LM Studio."""
        schema_info = self.generate_tables_info()
        prompt = f"""You are an SQL expert. Convert the following natural language question into a valid SQLite SQL query.

Database schema:
{schema_info}

Question: {query}

Generate only the SQL query, no explanations or markdown formatting:"""
        
        return self.llm.invoke(prompt)
    
    def _clean_sql_query(self, sql_query):
        """Clean SQL query by removing markdown formatting, prefixes, and extra whitespace."""
        # Remove markdown code blocks
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0]
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0]
        
        # Remove extra whitespace and newlines
        sql_query = sql_query.strip()
        
        # Remove common AI response prefixes
        prefixes_to_remove = ["SQLQuery:", "SQL:", "Query:", "sql:", "query:"]
        for prefix in prefixes_to_remove:
            if sql_query.startswith(prefix):
                sql_query = sql_query[len(prefix):].strip()
                break
        
        return sql_query
    
    def _generate_explanation(self, query, sql_query, result_df):
        """Generate an explanation of the query results."""
        if self.ai_config["backend"] == "LM Studio":
            # Handle LM Studio explanation generation
            prompt = f"""The user asked: {query}

The SQL query executed was: {sql_query}

The results were:
{result_df.to_string(max_rows=10, max_cols=10)}

Please provide a concise explanation of these results in relation to the user's question."""
            
            return self.llm.invoke(prompt)
        else:
            # Use LangChain for OpenAI and Gemini
            explain_prompt = PromptTemplate(
                input_variables=["query", "sql_query", "results"],
                template="""
                The user asked: {query}
                
                The SQL query executed was: {sql_query}
                
                The results were:
                {results}
                
                Please provide a concise explanation of these results in relation to the user's question.
                """
            )
            
            explanation_chain = LLMChain(llm=self.llm, prompt=explain_prompt)
            explanation = explanation_chain.run(
                query=query,
                sql_query=sql_query,
                results=result_df.to_string(max_rows=10, max_cols=10)
            )
            
            return explanation


# Additional query templates
SQL_GENERATION_TEMPLATE = """
You are an SQL expert. Your task is to convert natural language questions into SQL queries.

Database schema:
{schema}

User question: {question}

Generate a valid SQLite SQL query that answers the user's question.
Only output the SQL query, nothing else.
"""

SCHEMA_ANALYSIS_TEMPLATE = """
Analyze the following database schema and identify potential relationships between tables:

{schema}

Identify:
1. Primary and foreign key relationships
2. Possible join conditions
3. Table hierarchy (parent-child relationships)
4. Potential data flow
"""