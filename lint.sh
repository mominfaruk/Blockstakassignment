#!/bin/bash

# Run Ruff linter on the project
echo "Running Ruff linter..."
ruff check .

# Run Ruff formatter
echo "Running Ruff formatter..."
ruff format .

echo "Linting complete!"
