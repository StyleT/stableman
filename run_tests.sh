#!/bin/bash

echo "🧪 Running Blanketing Logic Unit Tests..."
echo "=========================================="

# Run the unit tests
python3 test_blanketing_logic.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All blanketing logic tests passed!"
    echo ""
    echo "🔍 Test Coverage:"
    echo "- Housing status determination (heat index, rain protection)"
    echo "- Temperature threshold logic (OUT vs IN)"  
    echo "- Anti-overheating logic and step-down rules"
    echo "- Care instruction generation"
    echo "- Edge cases and boundary conditions"
    echo ""
    echo "🛡️  Business logic is protected against regression bugs."
else
    echo ""
    echo "❌ Tests failed! Check output above for details."
    exit 1
fi