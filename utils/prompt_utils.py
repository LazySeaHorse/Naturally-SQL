from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain

class TextToSQLProcessor:
    def __init__(self, db_manager, api_key):
        """Initialize the text to SQL processor."""
        self.db_manager = db_manager
        self.api_key = api_key
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", api_key=api_key)
        
        # Create SQLAlchemy database
        self.db = SQLDatabase.from_uri(db_manager.get_sqlalchemy_url())
    
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
        # Create the SQL query chain
        query_chain = create_sql_query_chain(self.llm, self.db)
        
        # Generate the SQL query
        sql_query = query_chain.invoke({"question": query})
        
        # Execute the query
        result_df = self.db_manager.execute_query(sql_query)
        
        # Generate explanation if there are results
        explanation = None
        if not result_df.empty:
            explanation = self._generate_explanation(query, sql_query, result_df)
        
        return sql_query, result_df, explanation
    
    def _generate_explanation(self, query, sql_query, result_df):
        """Generate an explanation of the query results."""
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