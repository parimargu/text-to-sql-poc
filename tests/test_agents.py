"""Unit tests for agents."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from agents.base_agent import AgentState
from agents.text_to_sql_agent import TextToSQLAgent
from agents.sql_validator_agent import SQLValidatorAgent
from agents.sql_executor_agent import SQLExecutorAgent
from agents.result_formatter_agent import ResultFormatterAgent


class TestTextToSQLAgent:
    """Test cases for TextToSQLAgent."""
    
    @pytest.fixture
    def agent(self):
        return TextToSQLAgent()
    
    @pytest.fixture
    def sample_state(self):
        return AgentState(user_query="Show me all stores")
    
    @pytest.mark.asyncio
    async def test_process_success(self, agent, sample_state):
        """Test successful text-to-SQL conversion."""
        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_response = Mock()
            mock_response.content = "SELECT * FROM stores;"
            mock_llm.return_value = mock_response
            
            result = await agent.process(sample_state)
            
            assert result.sql_query == "SELECT * FROM stores;"
            assert result.error_message is None
            mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_with_context(self, agent):
        """Test text-to-SQL conversion with context."""
        state = AgentState(
            user_query="Show me customers from that store",
            context={
                "previous_queries": [
                    {"user_query": "Show stores", "sql_query": "SELECT * FROM stores;"}
                ]
            }
        )
        
        with patch.object(agent.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_response = Mock()
            mock_response.content = "SELECT * FROM customers WHERE store_id = 1;"
            mock_llm.return_value = mock_response
            
            result = await agent.process(state)
            
            assert result.sql_query is not None
            assert "customers" in result.sql_query.lower()
    
    @pytest.mark.asyncio
    async def test_process_error(self, agent, sample_state):
        """Test error handling in text-to-SQL conversion."""
        with patch.object(agent.llm, 'ainvoke', side_effect=Exception("API Error")):
            result = await agent.process(sample_state)
            
            assert result.error_message is not None
            assert "API Error" in result.error_message
    
    def test_clean_sql_query(self, agent):
        """Test SQL query cleaning."""
        test_cases = [
            ("```sql\nSELECT * FROM stores\n```", "SELECT * FROM stores;"),
            ("SQL: SELECT * FROM customers", "SELECT * FROM customers;"),
            ("  SELECT   *   FROM   products  ", "SELECT * FROM products;"),
            ("SELECT * FROM orders;", "SELECT * FROM orders;")
        ]
        
        for input_query, expected in test_cases:
            result = agent._clean_sql_query(input_query)
            assert result == expected


class TestSQLValidatorAgent:
    """Test cases for SQLValidatorAgent."""
    
    @pytest.fixture
    def agent(self):
        return SQLValidatorAgent()
    
    @pytest.mark.asyncio
    async def test_valid_select_query(self, agent):
        """Test validation of valid SELECT query."""
        state = AgentState(
            user_query="Show stores",
            sql_query="SELECT * FROM stores;"
        )
        
        result = await agent.process(state)
        
        assert result.validation_result["is_valid"] is True
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_invalid_table_name(self, agent):
        """Test validation with invalid table name."""
        state = AgentState(
            user_query="Show users",
            sql_query="SELECT * FROM users;"
        )
        
        result = await agent.process(state)
        
        assert result.validation_result["is_valid"] is False
        assert "Invalid table names" in result.error_message
    
    @pytest.mark.asyncio
    async def test_forbidden_keyword(self, agent):
        """Test validation with forbidden keywords."""
        state = AgentState(
            user_query="Delete all data",
            sql_query="DROP TABLE stores;"
        )
        
        result = await agent.process(state)
        
        assert result.validation_result["is_valid"] is False
        assert "Forbidden keyword" in result.error_message
    
    @pytest.mark.asyncio
    async def test_non_select_statement(self, agent):
        """Test validation of non-SELECT statements."""
        state = AgentState(
            user_query="Update store",
            sql_query="UPDATE stores SET name = 'New Name';"
        )
        
        result = await agent.process(state)
        
        assert result.validation_result["is_valid"] is False
        assert "Only SELECT statements are allowed" in result.error_message
    
    def test_extract_table_names(self, agent):
        """Test table name extraction."""
        test_cases = [
            ("SELECT * FROM stores;", ["stores"]),
            ("SELECT * FROM stores JOIN customers ON stores.id = customers.store_id;", 
             ["stores", "customers"]),
            ("SELECT * FROM orders o JOIN order_items oi ON o.id = oi.order_id;", 
             ["orders", "order_items"])
        ]
        
        for query, expected in test_cases:
            result = agent._extract_table_names(query)
            assert set(result) == set(expected)


class TestSQLExecutorAgent:
    """Test cases for SQLExecutorAgent."""
    
    @pytest.fixture
    def agent(self):
        return SQLExecutorAgent()
    
    @pytest.mark.asyncio
    async def test_execute_valid_query(self, agent):
        """Test execution of valid query."""
        state = AgentState(
            user_query="Show stores",
            sql_query="SELECT * FROM stores LIMIT 5;",
            validation_result={"is_valid": True}
        )
        
        with patch('pandas.read_sql_query') as mock_read_sql:
            mock_df = Mock()
            mock_df.to_dict.return_value = [{"id": 1, "name": "Test Store"}]
            mock_df.columns.tolist.return_value = ["id", "name"]
            mock_df.__len__.return_value = 1
            mock_read_sql.return_value = mock_df
            
            result = await agent.process(state)
            
            assert result.execution_result["success"] is True
            assert len(result.execution_result["data"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_invalid_query(self, agent):
        """Test execution with invalid validation."""
        state = AgentState(
            user_query="Show stores",
            sql_query="SELECT * FROM invalid_table;",
            validation_result={"is_valid": False}
        )
        
        result = await agent.process(state)
        
        assert result.error_message == "Cannot execute invalid SQL query"
    
    @pytest.mark.asyncio
    async def test_execute_database_error(self, agent):
        """Test handling of database errors."""
        state = AgentState(
            user_query="Show stores",
            sql_query="SELECT * FROM stores;",
            validation_result={"is_valid": True}
        )
        
        with patch('pandas.read_sql_query', side_effect=Exception("Database connection error")):
            result = await agent.process(state)
            
            assert result.execution_result["success"] is False
            assert "Database connection error" in result.execution_result["error"]


class TestResultFormatterAgent:
    """Test cases for ResultFormatterAgent."""
    
    @pytest.fixture
    def agent(self):
        return ResultFormatterAgent()
    
    @pytest.mark.asyncio
    async def test_format_success_result(self, agent):
        """Test formatting of successful results."""
        state = AgentState(
            user_query="Show stores",
            execution_result={
                "success": True,
                "data": [
                    {"id": 1, "name": "Store 1"},
                    {"id": 2, "name": "Store 2"}
                ],
                "columns": ["id", "name"],
                "row_count": 2
            }
        )
        
        result = await agent.process(state)
        
        assert "✅ **Query Results:**" in result.formatted_result
        assert "2 row(s) returned" in result.formatted_result
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_format_error_result(self, agent):
        """Test formatting of error results."""
        state = AgentState(
            user_query="Show stores",
            execution_result={
                "success": False,
                "error": "Table not found"
            }
        )
        
        result = await agent.process(state)
        
        assert "❌ **Query Failed:**" in result.formatted_result
        assert "Table not found" in result.formatted_result
    
    @pytest.mark.asyncio
    async def test_format_empty_result(self, agent):
        """Test formatting of empty results."""
        state = AgentState(
            user_query="Show stores",
            execution_result={
                "success": True,
                "data": [],
                "columns": ["id", "name"],
                "row_count": 0
            }
        )
        
        result = await agent.process(state)
        
        assert "no results were found" in result.formatted_result
    
    def test_create_table(self, agent):
        """Test table creation."""
        data = [
            {"id": 1, "name": "Store 1"},
            {"id": 2, "name": "Store 2"}
        ]
        columns = ["id", "name"]
        
        result = agent._create_table(data, columns)
        
        assert "Store 1" in result
        assert "Store 2" in result
