import pytest
import sys

# Run pytest with a coverage report
exitcode = pytest.main([
    "--cov", ".",
    "--cov-report", "html"
])
sys.exit(exitcode)
