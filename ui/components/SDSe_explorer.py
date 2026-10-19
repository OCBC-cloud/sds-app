# ui/components/SDSe_explorer.py
#
# SDSe Explorer — left drawer with a collapsible tree.
# Branches: Model (Geometry, Materials, Sections), Display (Layers), Tables (Element Seeds).
# Selecting a leaf closes the drawer and returns its key.
# Rule 22: one file, one block, one copy.

import streamlit as st

TREE = {
    "Model": {
        "geometry":  "Geometry",
        "materials": "Materials",
        "sections":  "Sections",
    },
    "Display": {
        "layers": "Layers",
    },
    "Tables": {
        "seeds": "Element Seeds",
    },
}

def _key_for(label):
    for branch, leaves in TREE.items():
        for key, leaf in leaves.items():
            if leaf == label:
                return key
    return None

def render_explorer(default="geometry"):
    """Render the drawer. Returns the currently selected leaf key."""
    if "sds_explorer_open" not in st.session_state:
        st.session_state["sds_explorer_open"] = True
    if "sds_explorer_selected" not in st.session_state:
        st.session_state["sds_explorer_selected"] = default

    selected = st.session_state["sds_explorer_selected"]

    # Toggle button (always visible)
    col1, col2 = st.columns([1, 5])
    with col1:
        label = "✕ Close" if st.session_state["sds_explorer_open"] else "☰ Explorer"
        if st.button(label, key="sds_explorer_toggle"):
            st.session_state["sds_explorer_open"] = not st.session_state["sds_explorer_open"]
            st.rerun()

    if not st.session_state["sds_explorer_open"]:
        return selected

    with st.container(border=True):
        st.markdown("**Explorer**")
        for branch, leaves in TREE.items():
            with st.expander(branch, expanded=True):
                for key, leaf in leaves.items():
                    is_active = (key == selected)
                    marker = "▸ " if is_active else "   "
                    if st.button(f"{marker}{leaf}", key=f"sds_leaf_{key}", use_container_width=True):
                        st.session_state["sds_explorer_selected"] = key
                        st.session_state["sds_explorer_open"] = False
                        st.rerun()

    return st.session_state["sds_explorer_selected"]

def current_branch():
    """Return the currently selected leaf key without re-rendering."""
    return st.session_state.get("sds_explorer_selected", "geometry")
