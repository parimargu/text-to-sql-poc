"""Unit tests for context manager."""

import pytest
from datetime import datetime, timedelta

from core.context_manager import ContextManager, ConversationEntry


class TestContextManager:
    """Test cases for ContextManager."""
    
    @pytest.fixture
    def context_manager(self):
        return ContextManager(max_entries=5)
    
    def test_add_entry(self, context_manager):
        """Test adding conversation entries."""
        context_manager.add_entry(
            user_query="Show stores",
            sql_query="SELECT * FROM stores;",
            success=True,
            result_summary="2 rows returned",
            token_count=10
        )
        
        assert len(context_manager.conversation_history) == 1
        assert context_manager.total_tokens == 10
        
        entry = context_manager.conversation_history[0]
        assert entry.user_query == "Show stores"
        assert entry.sql_query == "SELECT * FROM stores;"
        assert entry.success is True
    
    def test_context_window_maintenance(self, context_manager):
        """Test context window size maintenance."""
        # Add more entries than max_entries
        for i in range(7):
            context_manager.add_entry(
                user_query=f"Query {i}",
                sql_query=f"SELECT {i};",
                success=True,
                result_summary=f"Result {i}",
                token_count=5
            )
        
        # Should only keep max_entries (5)
        assert len(context_manager.conversation_history) == 5
        assert context_manager.total_tokens == 25
        
        # Should keep the most recent entries
        assert context_manager.conversation_history[0].user_query == "Query 2"
        assert context_manager.conversation_history[-1].user_query == "Query 6"
    
    def test_token_limit_maintenance(self, context_manager):
        """Test token limit maintenance."""
        # Set a low max_tokens for testing
        context_manager.max_tokens = 20
        
        # Add entries that exceed token limit
        for i in range(5):
            context_manager.add_entry(
                user_query=f"Query {i}",
                token_count=10
            )
        
        # Should remove old entries to stay under token limit
        assert context_manager.total_tokens <= 20
        assert len(context_manager.conversation_history) <= 2
    
    def test_get_context_for_llm(self, context_manager):
        """Test getting context for LLM."""
        # Add some successful and failed queries
        context_manager.add_entry("Query 1", "SELECT 1;", True, "Success")
        context_manager.add_entry("Query 2", None, False, "Failed")
        context_manager.add_entry("Query 3", "SELECT 3;", True, "Success")
        
        context = context_manager.get_context_for_llm()
        
        assert "previous_queries" in context
        # Should only include successful queries with SQL
        successful_queries = context["previous_queries"]
        assert len(successful_queries) == 2
        assert all(q["sql_query"] is not None for q in successful_queries)
    
    def test_get_context_summary(self, context_manager):
        """Test getting context summary."""
        context_manager.add_entry("Query 1", "SELECT 1;", True, "Success")
        context_manager.add_entry("Query 2", None, False, "Failed")
        
        summary = context_manager.get_context_summary()
        
        assert summary["total_conversations"] == 2
        assert summary["successful_queries"] == 1
        assert summary["failed_queries"] == 1
        assert summary["context_window_size"] == 5
        assert summary["context_window_usage"] == 2
    
    def test_clear_context(self, context_manager):
        """Test clearing context."""
        context_manager.add_entry("Query 1", "SELECT 1;", True, "Success")
        context_manager.add_entry("Query 2", "SELECT 2;", True, "Success")
        
        assert len(context_manager.conversation_history) == 2
        assert context_manager.total_tokens > 0
        
        context_manager.clear_context()
        
        assert len(context_manager.conversation_history) == 0
        assert context_manager.total_tokens == 0
    
    def test_get_context_warning(self, context_manager):
        """Test context warning generation."""
        # Test no warning when context is not full
        warning = context_manager.get_context_warning()
        assert warning is None
        
        # Fill context window
        for i in range(5):
            context_manager.add_entry(f"Query {i}", token_count=1)
        
        warning = context_manager.get_context_warning()
        assert "Context window is full" in warning
        
        # Test token limit warning
        context_manager.max_tokens = 10
        context_manager.total_tokens = 9
        
        warning = context_manager.get_context_warning()
        assert "Token limit is near" in warning
    
    def test_export_history(self, context_manager):
        """Test exporting conversation history."""
        context_manager.add_entry("Query 1", "SELECT 1;", True, "Success")
        context_manager.add_entry("Query 2", None, False, "Failed")
        
        history_json = context_manager.export_history()
        
        assert isinstance(history_json, str)
        assert "Query 1" in history_json
        assert "Query 2" in history_json
        assert "SELECT 1;" in history_json
