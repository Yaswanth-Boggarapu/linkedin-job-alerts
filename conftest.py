"""Put the repo root on sys.path so tests can import the modules directly.

Without this, a bare `pytest tests/` fails while `python -m pytest` works,
because only the latter adds the working directory to sys.path.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
