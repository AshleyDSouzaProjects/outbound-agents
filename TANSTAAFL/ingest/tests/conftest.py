"""Make the package importable when pytest is invoked from outside ingest/.

Without this, `pytest TANSTAAFL/ingest/tests` from the repo root fails at
collection with ModuleNotFoundError, which reads like a broken test suite but is
only an import-path problem.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
