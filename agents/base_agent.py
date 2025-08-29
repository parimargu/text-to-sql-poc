"""Base agent class for the multi-agent system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """State model for agent communication."""
    user_query: str
    sql_query: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    formatted_result: Optional[str] = None
    error_message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """Process the agent's task and return updated state."""
        pass
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str, error: Exception = None):
        """Log error message."""
        if error:
            self.logger.error(f"[{self.name}] {message}: {error}")
        else:
            self.logger.error(f"[{self.name}] {message}")
