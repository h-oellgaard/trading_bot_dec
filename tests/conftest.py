"""Shared pytest fixtures for test modules."""
import sys
from pathlib import Path

# Add project root to path so tests can import from project
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
