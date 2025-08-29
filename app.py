"""Main Streamlit application."""

import streamlit as st
import asyncio
import logging
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from core.workflow import TextToSQLWorkflow
from config.settings import settings
from scripts.seed_database import seed_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=settings.app_title,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .success-message {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
    }
    .context-info {
        background-color: #fff3e0;
        border: 1px solid #ff9800;
        border-radius: 0.25rem;
        padding: 0.75rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "workflow" not in st.session_state:
        st.session_state.workflow = TextToSQLWorkflow()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "database_seeded" not in st.session_state:
        st.session_state.database_seeded = False


def seed_database_if_needed():
    """Seed database if not already done."""
    if not st.session_state.database_seeded:
        with st.spinner("Initializing database with sample data..."):
            try:
                seed_database()
                st.session_state.database_seeded = True
                st.success("Database initialized successfully!")
            except Exception as e:
                st.error(f"Failed to initialize database: {e}")


def display_chat_history():
    """Display chat history."""
    for i, entry in enumerate(st.session_state.chat_history):
        # User message
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong> {entry['user_query']}
        </div>
        """, unsafe_allow_html=True)
        
        # Assistant response
        if entry['success']:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>Assistant:</strong><br>
                {entry['formatted_result']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show SQL query in expander
            if entry['sql_query']:
                with st.expander(f"View SQL Query #{i+1}"):
                    st.code(entry['sql_query'], language='sql')
        else:
            st.markdown(f"""
            <div class="chat-message error-message">
                <strong>Error:</strong> {entry['error_message']}
            </div>
            """, unsafe_allow_html=True)


def display_context_info():
    """Display context information in sidebar."""
    context_manager = st.session_state.workflow.get_context_manager()
    context_summary = context_manager.get_context_summary()
    
    st.sidebar.markdown("### 📊 Context Information")
    
    # Context usage
    usage_percentage = (context_summary['context_window_usage'] / 
                       context_summary['context_window_size']) * 100
    
    st.sidebar.metric(
        "Context Usage",
        f"{context_summary['context_window_usage']}/{context_summary['context_window_size']}",
        f"{usage_percentage:.1f}%"
    )
    
    # Query statistics
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Successful", context_summary['successful_queries'])
    with col2:
        st.metric("Failed", context_summary['failed_queries'])
    
    # Token usage
    token_percentage = (context_summary['token_usage'] / 
                       context_summary['max_tokens']) * 100
    st.sidebar.metric(
        "Token Usage",
        f"{context_summary['token_usage']}/{context_summary['max_tokens']}",
        f"{token_percentage:.1f}%"
    )
    
    # Context warning
    warning = context_manager.get_context_warning()
    if warning:
        st.sidebar.warning(warning)
    
    # Clear context button
    if st.sidebar.button("🗑️ Clear Context"):
        context_manager.clear_context()
        st.session_state.chat_history = []
        st.rerun()


def display_database_schema():
    """Display database schema information."""
    with st.sidebar.expander("📋 Database Schema"):
        st.markdown("""
        **Tables:**
        - `stores`: Store information
        - `customers`: Customer data
        - `products`: Product catalog
        - `orders`: Order records
        - `order_items`: Order line items
        
        **Sample Queries:**
        - "Show me all stores"
        - "What are the top 5 products by sales?"
        - "List customers who ordered in the last month"
        - "Show total revenue by store"
        """)


def display_analytics():
    """Display analytics dashboard."""
    st.markdown("### 📈 Query Analytics")
    
    if not st.session_state.chat_history:
        st.info("No queries executed yet. Start chatting to see analytics!")
        return
    
    # Prepare data
    history_df = pd.DataFrame([
        {
            'timestamp': datetime.now(),  # In real app, store actual timestamps
            'success': entry['success'],
            'query_length': len(entry['user_query']),
            'has_sql': bool(entry.get('sql_query'))
        }
        for entry in st.session_state.chat_history
    ])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        success_rate = (history_df['success'].sum() / len(history_df)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col2:
        avg_query_length = history_df['query_length'].mean()
        st.metric("Avg Query Length", f"{avg_query_length:.0f} chars")
    
    with col3:
        total_queries = len(history_df)
        st.metric("Total Queries", total_queries)
    
    # Success/Failure chart
    if len(history_df) > 1:
        success_counts = history_df['success'].value_counts()
        fig = px.pie(
            values=success_counts.values,
            names=['Failed' if not x else 'Successful' for x in success_counts.index],
            title="Query Success Rate"
        )
        st.plotly_chart(fig, use_container_width=True)


async def process_user_query(user_query: str):
    """Process user query through the workflow."""
    try:
        with st.spinner("Processing your query..."):
            result = await st.session_state.workflow.process_query(user_query)
            
            # Add to chat history
            st.session_state.chat_history.append(result)
            
            return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        error_result = {
            'success': False,
            'user_query': user_query,
            'error_message': f"System error: {str(e)}",
            'sql_query': None,
            'formatted_result': None
        }
        st.session_state.chat_history.append(error_result)
        return error_result


def main():
    """Main application function."""
    # Initialize
    initialize_session_state()
    seed_database_if_needed()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Text-to-SQL Conversational Chatbot</h1>', 
                unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666;'>{settings.app_description}</p>", 
                unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🛠️ Controls")
    display_context_info()
    display_database_schema()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📈 Analytics", "⚙️ Settings"])
    
    with tab1:
        # Chat interface
        st.markdown("### Ask questions about the retail database in natural language!")
        
        # Example queries
        with st.expander("💡 Example Queries"):
            examples = [
                "Show me all stores and their managers",
                "What are the top 5 best-selling products?",
                "List customers who have placed orders in the last 30 days",
                "Show total revenue by store",
                "Which products are out of stock?",
                "Show me orders with status 'shipped'",
                "What's the average order value?",
                "List all electronics products under $200"
            ]
            
            for example in examples:
                if st.button(example, key=f"example_{hash(example)}"):
                    # Process example query
                    result = asyncio.run(process_user_query(example))
                    st.rerun()
        
        # Chat input
        user_query = st.text_input(
            "Enter your question:",
            placeholder="e.g., Show me the top 10 customers by total order value",
            key="user_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            submit_button = st.button("🚀 Submit", type="primary")
        with col2:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        # Process query
        if submit_button and user_query:
            result = asyncio.run(process_user_query(user_query))
            st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("---")
            display_chat_history()
    
    with tab2:
        display_analytics()
    
    with tab3:
        st.markdown("### ⚙️ Configuration")
        
        # Display current settings
        st.markdown("**Current Settings:**")
        st.json({
            "Model": settings.model_name,
            "Max Tokens": settings.max_tokens,
            "Context Window Size": settings.context_window_size,
            "Database URL": settings.database_url
        })
        
        # Export conversation history
        if st.button("📥 Export Conversation History"):
            context_manager = st.session_state.workflow.get_context_manager()
            history_json = context_manager.export_history()
            st.download_button(
                label="Download History",
                data=history_json,
                file_name=f"conversation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()
