#!/bin/bash

# Run tests with coverage
echo "Running tests with coverage..."
pytest --cov=agents --cov=core --cov=database --cov-report=html --cov-report=term-missing --cov-fail-under=60

# Display coverage summary
echo "Coverage report generated in htmlcov/index.html"

# Run specific test categories
echo "Running agent tests..."
pytest tests/test_agents.py -v

echo "Running context manager tests..."
pytest tests/test_context_manager.py -v

echo "Running workflow tests..."
pytest tests/test_workflow.py -v
