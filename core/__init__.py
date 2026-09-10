# =============================================================================
# SDSe - core package
# =============================================================================
# Convenience exports so callers can do:
#   from core import apply_theme, init_session_state
# instead of:
#   from core.theme import apply_theme
#   from core.state import init_session_state
# =============================================================================

from core.theme import apply_theme, DARK_MODE_CSS
from core.state import init_session_state, clear_previous_project_data

__all__ = [
    "apply_theme",
    "DARK_MODE_CSS",
    "init_session_state",
    "clear_previous_project_data",
]
