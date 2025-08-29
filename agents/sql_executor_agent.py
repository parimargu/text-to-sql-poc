"""SQL query execution agent."""

import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.exc import SQLAlchemyError

from agents.base_agent import BaseAgent, AgentState
from database.connection import db_manager


class SQLExecutorAgent(BaseAgent):
    """Agent responsible for executing validated SQL queries."""
    
    def __init__(self):
        super().__init__("SQLExecutorAgent")
        self.max_rows = 1000  # Limit result size
    
    async def process(self, state: AgentState) -> AgentState:
        """Execute the validated SQL query."""
        try:
            self.log_info(f"Executing SQL: {state.sql_query}")
            
            if not state.sql_query:
                state.error_message = "No SQL query to execute"
                return state
            
            if state.validation_result and not state.validation_result.get("is_valid", False):
                state.error_message = "Cannot execute invalid SQL query"
                return state
            
            # Execute the query
            execution_result = self._execute_query(state.sql_query)
            state.execution_result = execution_result
            
            if execution_result.get("success", False):
                self.log_info(f"Query executed successfully. Rows returned: {len(execution_result.get('data', []))}")
            else:
                state.error_message = f"Query execution failed: {execution_result.get('error', 'Unknown error')}"
                self.log_error(f"Execution failed: {execution_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.log_error("SQL execution error", e)
            state.error_message = f"SQL execution error: {str(e)}"
            state.execution_result = {"success": False, "error": str(e)}
        
        return state
    
    def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query and return results."""
        try:
            with db_manager.get_session() as session:
                # Execute query using pandas for better data handling
                df = pd.read_sql_query(sql_query, session.bind)
                
                # Limit result size
                if len(df) > self.max_rows:
                    df = df.head(self.max_rows)
                    truncated = True
                else:
                    truncated = False
                
                # Convert to dictionary format
                data = df.to_dict('records')
                columns = df.columns.tolist()
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "truncated": truncated,
                    "query": sql_query
                }
                
        except SQLAlchemyError as e:
            return {
                "success": False,
                "error": f"Database error: {str(e)}",
                "query": sql_query
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "query": sql_query
            }
    
    def get_query_statistics(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about the query execution."""
        if not execution_result.get("success", False):
            return {"error": "Query failed"}
        
        data = execution_result.get("data", [])
        columns = execution_result.get("columns", [])
        
        stats = {
            "total_rows": len(data),
            "total_columns": len(columns),
            "column_names": columns,
            "truncated": execution_result.get("truncated", False)
        }
        
        # Add basic statistics for numeric columns
        if data:
            df = pd.DataFrame(data)
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_columns:
                stats["numeric_summary"] = {}
                for col in numeric_columns:
                    stats["numeric_summary"][col] = {
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "count": int(df[col].count())
                    }
        
        return stats
