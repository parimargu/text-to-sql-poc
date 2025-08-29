"""Unit tests for workflow."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from core.workflow import TextToSQLWorkflow
from agents.base_agent import AgentState


class TestTextToSQLWorkflow:
    """Test cases for TextToSQLWorkflow."""
    
    @pytest.fixture
    def workflow(self):
        return TextToSQLWorkflow()
    
    @pytest.mark.asyncio
    async def test_successful_workflow(self, workflow):
        """Test complete successful workflow."""
        with patch.object(workflow.text_to_sql_agent, 'process', new_callable=AsyncMock) as mock_text_to_sql, \
             patch.object(workflow.validator_agent, 'process', new_callable=AsyncMock) as mock_validator, \
             patch.object(workflow.executor_agent, 'process', new_callable=AsyncMock) as mock_executor, \
             patch.object(workflow.formatter_agent, 'process', new_callable=AsyncMock) as mock_formatter:
            
            # Mock agent responses
            mock_text_to_sql.return_value = AgentState(
                user_query="Show stores",
                sql_query="SELECT * FROM stores;"
            )
            
            mock_validator.return_value = AgentState(
                user_query="Show stores",
                sql_query="SELECT * FROM stores;",
                validation_result={"is_valid": True}
            )
            
            mock_executor.return_value = AgentState(
                user_query="Show stores",
                sql_query="SELECT * FROM stores;",
                validation_result={"is_valid": True},
                execution_result={"success": True, "data": [], "row_count": 0}
            )
            
            mock_formatter.return_value = AgentState(
                user_query="Show stores",
                sql_query="SELECT * FROM stores;",
                validation_result={"is_valid": True},
                execution_result={"success": True, "data": [], "row_count": 0},
                formatted_result="Query executed successfully"
            )
            
            result = await workflow.process_query("Show stores")
            
            assert result["success"] is True
            assert result["sql_query"] == "SELECT * FROM stores;"
            assert result["formatted_result"] == "Query executed successfully"
            
            # Verify all agents were called
            mock_text_to_sql.assert_called_once()
            mock_validator.assert_called_once()
            mock_executor.assert_called_once()
            mock_formatter.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validation_failure_workflow(self, workflow):
        """Test workflow when validation fails."""
        with patch.object(workflow.text_to_sql_agent, 'process', new_callable=AsyncMock) as mock_text_to_sql, \
             patch.object(workflow.validator_agent, 'process', new_callable=AsyncMock) as mock_validator, \
             patch.object(workflow.executor_agent, 'process', new_callable=AsyncMock) as mock_executor, \
             patch.object(workflow.formatter_agent, 'process', new_callable=AsyncMock) as mock_formatter:
            
            # Mock agent responses
            mock_text_to_sql.return_value = AgentState(
                user_query="Drop table",
                sql_query="DROP TABLE stores;"
            )
            
            mock_validator.return_value = AgentState(
                user_query="Drop table",
                sql_query="DROP TABLE stores;",
                validation_result={"is_valid": False},
                error_message="Forbidden keyword: DROP"
            )
            
            result = await workflow.process_query("Drop table")
            
            assert result["success"] is False
            assert "DROP" in result["error_message"]
            
            # Verify executor and formatter were not called
            mock_text_to_sql.assert_called_once()
            mock_validator.assert_called_once()
            mock_executor.assert_not_called()
            mock_formatter.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_workflow_exception_handling(self, workflow):
        """Test workflow exception handling."""
        with patch.object(workflow.text_to_sql_agent, 'process', side_effect=Exception("Agent error")):
            result = await workflow.process_query("Test query")
            
            assert result["success"] is False
            assert "Workflow error" in result["error_message"]
            assert "Agent error" in result["error_message"]
    
    def test_should_execute_decision(self, workflow):
        """Test execution decision logic."""
        # Valid state should execute
        valid_state = AgentState(
            user_query="Show stores",
            validation_result={"is_valid": True}
        )
        assert workflow._should_execute(valid_state) == "execute"
        
        # Invalid state should not execute
        invalid_state = AgentState(
            user_query="Drop table",
            validation_result={"is_valid": False},
            error_message="Validation failed"
        )
        assert workflow._should_execute(invalid_state) == "end"
        
        # State with error should not execute
        error_state = AgentState(
            user_query="Show stores",
            validation_result={"is_valid": True},
            error_message="Some error"
        )
        assert workflow._should_execute(error_state) == "end"
    
    def test_context_manager_integration(self, workflow):
        """Test context manager integration."""
        context_manager = workflow.get_context_manager()
        
        # Should be the same instance
        assert context_manager is workflow.context_manager
        
        # Should be properly initialized
        assert context_manager.max_entries > 0
        assert context_manager.conversation_history == []
