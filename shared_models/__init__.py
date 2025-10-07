# shared_models\__init__.py
"""
Shared Models Package
---------------------
This package centralizes all Pydantic models used across:

- backend
- ai-worker
- onpageseo-service
- frontend (via OpenAPI → TypeScript codegen)

Usage:
    from shared_models.models import SEOAuditResult, SEOIssue, SEOIssueLevel
"""

# Expose everything from models.py so imports are clean
from .models import *

















# Then you can:

# In dev: just keep shared_models in the repo root and import it normally.

# In prod:

# Either copy shared_models into each service’s Docker image (easy).

# Or publish shared_models as a private pip package (pip install shared-models==0.1.0) and version it cleanly.