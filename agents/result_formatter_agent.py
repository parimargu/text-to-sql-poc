"""Result formatting agent."""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

from agents.base_agent import BaseAgent, AgentState


class ResultFormatterAgent(BaseAgent):
    """Agent responsible for formatting query results for display."""
    
    def __init__(self):
        super().__init__("ResultFormatterAgent")
    
    async def process(self, state: AgentState) -> AgentState:
        """Format the execution results for user-friendly display."""
        try:
            self.log_info("Formatting query results")
            
            if not state.execution_result:
                state.error_message = "No execution result to format"
                return state
            
            if not state.execution_result.get("success", False):
                state.formatted_result = self._format_error_result(state.execution_result)
            else:
                state.formatted_result = self._format_success_result(state.execution_result)
            
            self.log_info("Results formatted successfully")
            
        except Exception as e:
            self.log_error("Result formatting error", e)
            state.error_message = f"Result formatting error: {str(e)}"
            state.formatted_result = f"Error formatting results: {str(e)}"
        
        return state
    
    def _format_success_result(self, execution_result: Dict[str, Any]) -> str:
        """Format successful query results."""
        data = execution_result.get("data", [])
        columns = execution_result.get("columns", [])
        row_count = execution_result.get("row_count", 0)
        truncated = execution_result.get("truncated", False)
        
        if not data:
            return "✅ Query executed successfully, but no results were found."
        
        # Create formatted output
        result_lines = []
        result_lines.append("✅ **Query Results:**")
        result_lines.append("")
        
        # Add summary information
        result_lines.append(f"📊 **Summary:** {row_count} row(s) returned")
        if truncated:
            result_lines.append(f"⚠️ **Note:** Results truncated to first 1000 rows")
        result_lines.append("")
        
        # Format data as table
        if len(data) <= 20:  # Show full table for small results
            table_str = self._create_table(data, columns)
            result_lines.append("📋 **Data:**")
            result_lines.append("```")
            result_lines.append(table_str)
            result_lines.append("```")
        else:  # Show sample for large results
            sample_data = data[:10]
            table_str = self._create_table(sample_data, columns)
            result_lines.append("📋 **Sample Data (first 10 rows):**")
            result_lines.append("```")
            result_lines.append(table_str)
            result_lines.append("```")
            result_lines.append(f"... and {len(data) - 10} more rows")
        
        # Add statistics if available
        stats = self._calculate_basic_stats(data, columns)
        if stats:
            result_lines.append("")
            result_lines.append("📈 **Statistics:**")
            for stat_line in stats:
                result_lines.append(f"  • {stat_line}")
        
        return "\n".join(result_lines)
    
    def _format_error_result(self, execution_result: Dict[str, Any]) -> str:
        """Format error results."""
        error_msg = execution_result.get("error", "Unknown error")
        return f"❌ **Query Failed:**\n\n{error_msg}"
    
    def _create_table(self, data: List[Dict], columns: List[str]) -> str:
        """Create a formatted table string."""
        if not data or not columns:
            return "No data to display"
        
        # Convert to DataFrame for better formatting
        df = pd.DataFrame(data)
        
        # Format the table
        return df.to_string(index=False, max_rows=20, max_cols=10)
    
    def _calculate_basic_stats(self, data: List[Dict], columns: List[str]) -> List[str]:
        """Calculate basic statistics for the data."""
        if not data:
            return []
        
        stats = []
        df = pd.DataFrame(data)
        
        # Numeric column statistics
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_columns:
            for col in numeric_columns[:3]:  # Limit to first 3 numeric columns
                try:
                    col_stats = df[col].describe()
                    stats.append(f"{col}: avg={col_stats['mean']:.2f}, min={col_stats['min']:.2f}, max={col_stats['max']:.2f}")
                except:
                    continue
        
        # Categorical column statistics
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        if categorical_columns:
            for col in categorical_columns[:2]:  # Limit to first 2 categorical columns
                try:
                    unique_count = df[col].nunique()
                    stats.append(f"{col}: {unique_count} unique values")
                except:
                    continue
        
        return stats
