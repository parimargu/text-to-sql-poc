"""LangGraph workflow for the multi-agent system."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
import asyncio

from agents.base_agent import AgentState
from agents.text_to_sql_agent import TextToSQLAgent
from agents.sql_validator_agent import SQLValidatorAgent
from agents.sql_executor_agent import SQLExecutorAgent
from agents.result_formatter_agent import ResultFormatterAgent
from core.context_manager import ContextManager


class TextToSQLWorkflow:
    """Multi-agent workflow for Text-to-SQL processing."""
    
    def __init__(self):
        self.text_to_sql_agent = TextToSQLAgent()
        self.validator_agent = SQLValidatorAgent()
        self.executor_agent = SQLExecutorAgent()
        self.formatter_agent = ResultFormatterAgent()
        self.context_manager = ContextManager()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("text_to_sql", self._text_to_sql_node)
        workflow.add_node("validate_sql", self._validate_sql_node)
        workflow.add_node("execute_sql", self._execute_sql_node)
        workflow.add_node("format_result", self._format_result_node)
        
        # Add edges
        workflow.set_entry_point("text_to_sql")
        workflow.add_edge("text_to_sql", "validate_sql")
        workflow.add_conditional_edges(
            "validate_sql",
            self._should_execute,
            {
                "execute": "execute_sql",
                "end": END
            }
        )
        workflow.add_edge("execute_sql", "format_result")
        workflow.add_edge("format_result", END)
        
        return workflow.compile()
    
    async def _text_to_sql_node(self, state: AgentState) -> AgentState:
        """Text-to-SQL conversion node."""
        return await self.text_to_sql_agent.process(state)
    
    async def _validate_sql_node(self, state: AgentState) -> AgentState:
        """SQL validation node."""
        return await self.validator_agent.process(state)
    
    async def _execute_sql_node(self, state: AgentState) -> AgentState:
        """SQL execution node."""
        return await self.executor_agent.process(state)
    
    async def _format_result_node(self, state: AgentState) -> AgentState:
        """Result formatting node."""
        return await self.formatter_agent.process(state)
    
    def _should_execute(self, state: AgentState) -> str:
        """Determine if SQL should be executed based on validation."""
        if (state.validation_result and 
            state.validation_result.get("is_valid", False) and 
            not state.error_message):
            return "execute"
        return "end"
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the workflow."""
        try:
            # Create initial state with context
            context = self.context_manager.get_context_for_llm()
            initial_state = AgentState(
                user_query=user_query,
                context=context
            )
            
            # Run the workflow
            workflow_result = await self.workflow.ainvoke(initial_state)
            
            if isinstance(workflow_result, dict):
                final_state = AgentState(**workflow_result)
            else:
                final_state = workflow_result
            
            # Update context manager
            success = (final_state.execution_result and 
                      final_state.execution_result.get("success", False))
            
            result_summary = ""
            if success and final_state.execution_result:
                row_count = final_state.execution_result.get("row_count", 0)
                result_summary = f"Returned {row_count} rows"
            elif final_state.error_message:
                result_summary = f"Error: {final_state.error_message}"
            
            # Estimate token count (rough approximation)
            token_count = len(user_query.split()) + len((final_state.sql_query or "").split())
            
            self.context_manager.add_entry(
                user_query=user_query,
                sql_query=final_state.sql_query,
                success=success,
                result_summary=result_summary,
                token_count=token_count
            )
            
            # Prepare response
            response = {
                "success": success,
                "user_query": user_query,
                "sql_query": final_state.sql_query,
                "formatted_result": final_state.formatted_result,
                "error_message": final_state.error_message,
                "context_summary": self.context_manager.get_context_summary(),
                "context_warning": self.context_manager.get_context_warning()
            }
            
            return response
            
        except Exception as e:
            error_msg = f"Workflow error: {str(e)}"
            self.context_manager.add_entry(
                user_query=user_query,
                success=False,
                result_summary=error_msg,
                token_count=len(user_query.split())
            )
            
            return {
                "success": False,
                "user_query": user_query,
                "error_message": error_msg,
                "context_summary": self.context_manager.get_context_summary()
            }
    
    def get_context_manager(self) -> ContextManager:
        """Get the context manager instance."""
        return self.context_manager
