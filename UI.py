"""Backward-compatible Streamlit entrypoint.

Preferred entrypoint: `streamlit run app/dashboard.py`
"""

from app.dashboard import *  # noqa: F401,F403
