import pytest
import sys
from flake8.main.application import Application

# Run flake
app = Application()
ret = app.run(["--max-line-length", "120", "py/", "scripts/"])
flake_exitcode = app.exit_code()
print(flake_exitcode)

# Run pytest
pytest_exitcode = pytest.main()

# Exit based on the two codes
sys.exit(flake_exitcode + pytest_exitcode)
