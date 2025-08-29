"""Text-to-SQL conversion agent."""

from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

from agents.base_agent import BaseAgent, AgentState
from config.settings import settings
from database.connection import db_manager


class TextToSQLAgent(BaseAgent):
    """Agent responsible for converting natural language to SQL queries."""
    
    def __init__(self):
        super().__init__("TextToSQLAgent")
        self.llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.model_name,
            max_tokens=settings.max_tokens,
            temperature=0.1
        )
        self.prompt_template = self._create_prompt_template()
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create prompt template for text-to-SQL conversion."""
        template = """
        You are an expert SQL query generator for a retail database.
        
        Database Schema:
        {schema_info}
        
        Previous Context (if any):
        {context}
        
        User Query: {user_query}
        
        Instructions:
        1. Generate a valid SQL query based on the user's natural language request
        2. Use proper SQL syntax and follow best practices
        3. Only use tables and columns that exist in the schema
        4. If the query is ambiguous, make reasonable assumptions
        5. Return ONLY the SQL query without any explanation or formatting
        6. Use appropriate JOINs when querying multiple tables
        7. Consider the context from previous queries if relevant
        
        SQL Query:
        """
        
        return PromptTemplate(
            input_variables=["schema_info", "context", "user_query"],
            template=template
        )
    
    async def process(self, state: AgentState) -> AgentState:
        """Convert natural language query to SQL."""
        try:
            self.log_info(f"Converting query: {state.user_query}")
            
            # Get database schema information
            schema_info = db_manager.get_schema_info()
            
            # Prepare context from previous interactions
            context = ""
            if state.context and "previous_queries" in state.context:
                recent_queries = state.context["previous_queries"][-3:]  # Last 3 queries
                context = "\n".join([
                    f"Previous Query: {q['user_query']} -> SQL: {q['sql_query']}"
                    for q in recent_queries
                ])
            
            # Generate SQL query
            prompt = self.prompt_template.format(
                schema_info=schema_info,
                context=context,
                user_query=state.user_query
            )
            
            response = await self.llm.ainvoke(prompt)
            sql_query = response.content.strip()
            
            # Clean up the SQL query
            sql_query = self._clean_sql_query(sql_query)
            
            state.sql_query = sql_query
            self.log_info(f"Generated SQL: {sql_query}")
            
        except Exception as e:
            self.log_error("Failed to convert text to SQL", e)
            state.error_message = f"Text-to-SQL conversion failed: {str(e)}"
        
        return state
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and format the generated SQL query."""
        # Remove common prefixes/suffixes that LLM might add
        sql_query = sql_query.replace("```sql", "").replace("```", "")
        sql_query = sql_query.replace("SQL:", "").replace("Query:", "")
        
        # Remove extra whitespace and ensure proper formatting
        sql_query = " ".join(sql_query.split())
        
        # Ensure query ends with semicolon
        if not sql_query.endswith(";"):
            sql_query += ";"
        
        return sql_query
