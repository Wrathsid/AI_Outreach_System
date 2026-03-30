"""
Root conftest.py — configure pytest collection to skip non-test files
and directories that confuse the collector.
"""

collect_ignore_glob = [
    "test_db_out.*",          # Binary output files
    "backend/scripts/**",     # Scripts are not test suites
    "frontend/**",            # Skip frontend entirely
    "node_modules/**",
    ".venv/**",
]
