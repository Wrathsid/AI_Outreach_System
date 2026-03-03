import sys
import os

# Add the repo root to Python path so 'backend' package is importable.
# With Vercel's "Include files outside root directory" enabled,
# the entire repo is available — backend/ is at ../backend/ relative to frontend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel Python Serverless Function entry point
# Vercel auto-discovers this file and routes /api/* requests to it.
