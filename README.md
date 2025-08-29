# Text-to-SQL Conversational Chatbot

A sophisticated conversational chatbot that converts natural language queries to SQL and executes them against a retail database. Built with Streamlit, LangGraph, and Groq LLM.

## Features

- **Multi-Agent Architecture**: Uses LangGraph for orchestrating specialized agents
- **Text-to-SQL Conversion**: Converts natural language to SQL queries using Groq LLM
- **SQL Validation**: Validates queries for safety and correctness
- **Query Execution**: Executes validated queries against the database
- **Result Formatting**: Formats results in user-friendly format
- **Context Management**: Maintains conversation history with configurable context window
- **Interactive UI**: Streamlit-based web interface with analytics dashboard

## Architecture

### Agents

1. **TextToSQLAgent**: Converts natural language to SQL using Groq LLM
2. **SQLValidatorAgent**: Validates SQL queries for safety and correctness
3. **SQLExecutorAgent**: Executes validated SQL queries
4. **ResultFormatterAgent**: Formats query results for display

### Database Schema

- **stores**: Store information (id, name, location, manager, etc.)
- **customers**: Customer data (id, name, email, phone, address)
- **products**: Product catalog (id, name, category, price, description)
- **orders**: Order records (id, customer_id, store_id, total_amount, status)
- **order_items**: Order line items (id, order_id, product_id, quantity, unit_price)

## Installation

1. Clone the repository:
\`\`\`bash
git clone <repository-url>
cd text-to-sql-chatbot
\`\`\`

2. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. Set up environment variables:
\`\`\`bash
cp .env.example .env
# Edit .env with your Groq API key
\`\`\`

4. Run the application:
\`\`\`bash
streamlit run app.py
\`\`\`

## Configuration

Environment variables in `.env`:

- `GROQ_API_KEY`: Your Groq API key
- `DATABASE_URL`: Database connection URL (default: SQLite)
- `CONTEXT_WINDOW_SIZE`: Maximum conversation history entries (default: 10)
- `MAX_TOKENS`: Maximum tokens for LLM (default: 4000)
- `MODEL_NAME`: Groq model name (default: mixtral-8x7b-32768)

## Usage

### Example Queries

- "Show me all stores and their managers"
- "What are the top 5 best-selling products?"
- "List customers who have placed orders in the last 30 days"
- "Show total revenue by store"
- "Which products are out of stock?"

### Features

- **Context Awareness**: The chatbot remembers previous queries and can reference them
- **Safety**: Only SELECT queries are allowed, with validation against SQL injection
- **Analytics**: View query success rates and usage statistics
- **Export**: Export conversation history as JSON

## Testing

Run tests with coverage:

\`\`\`bash
pytest --cov=agents --cov=core --cov=database --cov-report=html
\`\`\`

Current test coverage: 60%+

## Development

### Project Structure

\`\`\`
├── agents/                 # Multi-agent system
│   ├── base_agent.py      # Base agent class
│   ├── text_to_sql_agent.py
│   ├── sql_validator_agent.py
│   ├── sql_executor_agent.py
│   └── result_formatter_agent.py
├── core/                  # Core functionality
│   ├── context_manager.py # Conversation context management
│   └── workflow.py        # LangGraph workflow
├── database/              # Database layer
│   ├── models.py          # SQLAlchemy models
│   └── connection.py      # Database connection management
├── config/                # Configuration
│   └── settings.py        # Application settings
├── scripts/               # Utility scripts
│   └── seed_database.py   # Database seeding
├── tests/                 # Unit tests
└── app.py                 # Main Streamlit application
\`\`\`

### Design Patterns

- **Agent Pattern**: Specialized agents for different tasks
- **State Pattern**: Shared state between agents
- **Factory Pattern**: Database connection management
- **Observer Pattern**: Context management and logging
- **Strategy Pattern**: Different formatting strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure test coverage remains above 60%
5. Submit a pull request

## License

MIT License
