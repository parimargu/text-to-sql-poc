"""SQL query validation agent."""

import sqlparse
from sqlparse import sql, tokens
from typing import Dict, Any, List
import re

from agents.base_agent import BaseAgent, AgentState
from database.connection import db_manager


class SQLValidatorAgent(BaseAgent):
    """Agent responsible for validating SQL queries."""
    
    def __init__(self):
        super().__init__("SQLValidatorAgent")
        self.allowed_keywords = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
            'GROUP', 'BY', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'AS', 'ON',
            'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS', 'NULL',
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT'
        }
        self.forbidden_keywords = {
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'CREATE', 'ALTER', 'TRUNCATE',
            'EXEC', 'EXECUTE', 'UNION', 'GRANT', 'REVOKE'
        }
        self.valid_tables = {
            'stores', 'customers', 'products', 'orders', 'order_items'
        }
    
    async def process(self, state: AgentState) -> AgentState:
        """Validate the SQL query."""
        try:
            self.log_info(f"Validating SQL: {state.sql_query}")
            
            if not state.sql_query:
                state.error_message = "No SQL query to validate"
                return state
            
            validation_result = self._validate_query(state.sql_query)
            state.validation_result = validation_result
            
            if not validation_result["is_valid"]:
                state.error_message = f"SQL validation failed: {validation_result['error']}"
                self.log_error(f"Validation failed: {validation_result['error']}")
            else:
                self.log_info("SQL query validation passed")
            
        except Exception as e:
            self.log_error("SQL validation error", e)
            state.error_message = f"SQL validation error: {str(e)}"
            state.validation_result = {"is_valid": False, "error": str(e)}
        
        return state
    
    def _validate_query(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL query for safety and correctness."""
        try:
            # Parse the SQL query
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return {"is_valid": False, "error": "Unable to parse SQL query"}
            
            statement = parsed[0]
            
            # Check for forbidden keywords
            forbidden_found = self._check_forbidden_keywords(sql_query)
            if forbidden_found:
                return {
                    "is_valid": False,
                    "error": f"Forbidden keyword found: {forbidden_found}"
                }
            
            # Check if it's a SELECT statement
            if not self._is_select_statement(statement):
                return {
                    "is_valid": False,
                    "error": "Only SELECT statements are allowed"
                }
            
            # Validate table names
            invalid_tables = self._validate_table_names(sql_query)
            if invalid_tables:
                return {
                    "is_valid": False,
                    "error": f"Invalid table names: {', '.join(invalid_tables)}"
                }
            
            # Check for SQL injection patterns
            injection_risk = self._check_sql_injection(sql_query)
            if injection_risk:
                return {
                    "is_valid": False,
                    "error": f"Potential SQL injection detected: {injection_risk}"
                }
            
            return {
                "is_valid": True,
                "parsed_query": statement,
                "tables_used": self._extract_table_names(sql_query)
            }
            
        except Exception as e:
            return {"is_valid": False, "error": f"Validation error: {str(e)}"}
    
    def _check_forbidden_keywords(self, sql_query: str) -> str:
        """Check for forbidden SQL keywords."""
        query_upper = sql_query.upper()
        for keyword in self.forbidden_keywords:
            if re.search(r'\b' + keyword + r'\b', query_upper):
                return keyword
        return None
    
    def _is_select_statement(self, statement) -> bool:
        """Check if the statement is a SELECT statement."""
        for token in statement.flatten():
            if token.ttype is tokens.Keyword.DML:
                return token.value.upper() == 'SELECT'
        return False
    
    def _validate_table_names(self, sql_query: str) -> List[str]:
        """Validate that all table names exist in the schema."""
        table_names = self._extract_table_names(sql_query)
        invalid_tables = []
        
        for table in table_names:
            if table.lower() not in self.valid_tables:
                invalid_tables.append(table)
        
        return invalid_tables
    
    def _extract_table_names(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query."""
        # Simple regex-based extraction (could be improved with proper parsing)
        pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql_query, re.IGNORECASE)
        return list(set(matches))
    
    def _check_sql_injection(self, sql_query: str) -> str:
        """Check for common SQL injection patterns."""
        injection_patterns = [
            r"';.*--",  # Comment injection
            r"union.*select",  # Union-based injection
            r"or.*1=1",  # Boolean-based injection
            r"and.*1=1",  # Boolean-based injection
        ]
        
        query_lower = sql_query.lower()
        for pattern in injection_patterns:
            if re.search(pattern, query_lower):
                return f"Pattern: {pattern}"
        
        return None
