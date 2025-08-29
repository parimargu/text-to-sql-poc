"""Context management for conversation history."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from config.settings import settings


@dataclass
class ConversationEntry:
    """Single conversation entry."""
    timestamp: datetime
    user_query: str
    sql_query: Optional[str]
    success: bool
    result_summary: str
    token_count: int = 0


class ContextManager:
    """Manages conversation context and history."""
    
    def __init__(self, max_entries: int = None):
        self.max_entries = max_entries or settings.context_window_size
        self.conversation_history: List[ConversationEntry] = []
        self.total_tokens = 0
        self.max_tokens = settings.max_tokens
    
    def add_entry(self, 
                  user_query: str,
                  sql_query: Optional[str] = None,
                  success: bool = False,
                  result_summary: str = "",
                  token_count: int = 0) -> None:
        """Add a new conversation entry."""
        entry = ConversationEntry(
            timestamp=datetime.utcnow(),
            user_query=user_query,
            sql_query=sql_query,
            success=success,
            result_summary=result_summary,
            token_count=token_count
        )
        
        self.conversation_history.append(entry)
        self.total_tokens += token_count
        
        # Maintain context window size
        self._maintain_context_window()
    
    def _maintain_context_window(self) -> None:
        """Maintain the context window size and token limits."""
        # Remove old entries if exceeding max entries
        while len(self.conversation_history) > self.max_entries:
            removed_entry = self.conversation_history.pop(0)
            self.total_tokens -= removed_entry.token_count
        
        # Remove old entries if exceeding token limit
        while (self.total_tokens > self.max_tokens * 0.8 and 
               len(self.conversation_history) > 1):
            removed_entry = self.conversation_history.pop(0)
            self.total_tokens -= removed_entry.token_count
    
    def get_context_for_llm(self) -> Dict[str, Any]:
        """Get context formatted for LLM consumption."""
        if not self.conversation_history:
            return {"previous_queries": []}
        
        # Get recent successful queries for context
        recent_queries = []
        for entry in self.conversation_history[-5:]:  # Last 5 entries
            if entry.success and entry.sql_query:
                recent_queries.append({
                    "user_query": entry.user_query,
                    "sql_query": entry.sql_query,
                    "timestamp": entry.timestamp.isoformat()
                })
        
        return {
            "previous_queries": recent_queries,
            "total_conversations": len(self.conversation_history),
            "context_window_usage": f"{len(self.conversation_history)}/{self.max_entries}"
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context state."""
        successful_queries = sum(1 for entry in self.conversation_history if entry.success)
        failed_queries = len(self.conversation_history) - successful_queries
        
        return {
            "total_conversations": len(self.conversation_history),
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "context_window_size": self.max_entries,
            "context_window_usage": len(self.conversation_history),
            "token_usage": self.total_tokens,
            "max_tokens": self.max_tokens,
            "is_context_full": len(self.conversation_history) >= self.max_entries,
            "is_token_limit_near": self.total_tokens > self.max_tokens * 0.8
        }
    
    def clear_context(self) -> None:
        """Clear all conversation history."""
        self.conversation_history.clear()
        self.total_tokens = 0
    
    def export_history(self) -> str:
        """Export conversation history as JSON."""
        history_data = []
        for entry in self.conversation_history:
            entry_dict = asdict(entry)
            entry_dict['timestamp'] = entry.timestamp.isoformat()
            history_data.append(entry_dict)
        
        return json.dumps(history_data, indent=2)
    
    def get_context_warning(self) -> Optional[str]:
        """Get warning message if context limits are being approached."""
        summary = self.get_context_summary()
        
        warnings = []
        
        if summary["is_context_full"]:
            warnings.append(f"Context window is full ({summary['context_window_usage']}/{summary['context_window_size']}). Older conversations will be removed.")
        
        if summary["is_token_limit_near"]:
            warnings.append(f"Token limit is near ({summary['token_usage']}/{summary['max_tokens']}). Context may be truncated.")
        
        return " ".join(warnings) if warnings else None
