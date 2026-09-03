"""SPC Project: Statistical Process Control & Prompt Engineering Engine."""

import sys
from pathlib import Path

# Centralize all bytecode caching into .cache/pycache
_cache_prefix = Path(__file__).resolve().parent.parent / ".cache" / "pycache"
_cache_prefix.mkdir(parents=True, exist_ok=True)
sys.pycache_prefix = str(_cache_prefix)

__version__ = "0.1.0"
