#!/bin/bash
# Quick test to verify pytest setup

echo "🧪 Testing pytest configuration..."

# Set test environment variables
export ZHIPU_API_KEY="test_key_for_unit_tests"
export DATABASE_PATH="/tmp/test_db.db"
export STORAGE_ROOT="/tmp/test_storage"

# Run a simple test to verify setup
echo "Running: pytest server/tests/test_task_service.py::test_create_task -v"
pytest server/tests/test_task_service.py::test_create_task -v

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Test configuration is working correctly!"
    echo ""
    echo "To run all tests:"
    echo "  pytest server/tests -v"
    echo ""
    echo "To run with coverage:"
    echo "  pytest --cov=server --cov-report=html"
else
    echo ""
    echo "❌ Test configuration has issues. Please check the error messages above."
fi
