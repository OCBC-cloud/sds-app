# =============================================================================
# SDSe Fluid Design Studio - Dome Multi-Cone Workshop
# =============================================================================
# Renders the Dome Multi-Cone workshop page using the SDSe Explorer drawer.
#
# Branches:
#   geometry  -> the multi-board (Plan / 3D View)
#   layers    -> the visibility checkboxes (read by the viewer)
#   seeds     -> the Element Seed Schedule (reads ws_dm_elements)
#   materials -> placeholder
#   sections  -> placeholder
#
# The recipe inputs are tucked into a closed expander at the bottom.
#
# History:
#   2026-10-19 - Replaced the top-down workshop layout with the explorer
#                drawer pattern. Extracted the Layers and Seeds panels
#                from the viewer.
# =============================================================================

import streamlit as st

from ui.workshops._renderer import render_workshop
from ui.components.dome_cone_picker import render_dome_cone_picker
from ui.components.SDSe_multi_board import render_multi_board
from ui.components.SDSe_explorer import render_explorer, current_branch
from viewers.figures.dome_multi_cone import build_dome_multi_cone
from data.recipes.dome_multi_cone import DOME_MULTI_CONE_RECIPE


# =============================================================================
# PANEL RENDERERS
# =============================================================================

def _render_plan_board():
    """Render the Plan board: the 2D cone picker."""
    dome_diameter = float(st.session_state.get("ws_dm_dome_diameter", 18.0))
    n_x = int(st.session_state.get("ws_dm_meridians_x", 5))
    n_y = int(st.session_state.get("ws_dm_meridians_y", 5))

    picked_raw = st.session_state.get("ws_dm_picked_crossings", None)
    if picked_raw is None:
        picked = set()
    else:
        try:
            picked = set((int(i), int(j)) for (i, j) in picked_raw)
        except (TypeError, ValueError):
            picked = set()

    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0;'>"
        "Click a crossing to place or remove a cone."
        "</p>",
        unsafe_allow_html=True,
    )

    new_picked = render_dome_cone_picker(
        dome_diameter=dome_diameter,
        n_x=n_x,
        n_y=n_y,
        picked=picked,
        key="dome_cone_picker_main",
    )
    st.session_state["ws_dm_picked_crossings"] = set(new_picked)


def _render_profile_board_stub():
    st.info(
        "The Profile board is temporarily unavailable. The custom "
        "elevation picker is under construction."
    )


def _render_3d_board():
    """Render the 3D View board."""
    build_dome_multi_cone()


def _render_geometry_panel():
    """The central drawing area."""
    render_multi_board(
        key="dome",
        plan_label="Plan",
        profile_label="Profile",
        view_3d_label="3D View",
        plan_renderer=_render_plan_board,
        profile_renderer=_render_profile_board_stub,
        view_3d_renderer=_render_3d_board,
    )


def _render_layers_panel():
    """The visibility layers."""
    st.markdown("### Layers & Visibility")
    st.caption("Toggle folders and layers to manage the drawing board.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Structure**")
        st.checkbox("Show Frame", value=True, key="ws_dm_show_frame")
        st.checkbox(
            "Show Anchor Markers",
            value=False,
            key="ws_dm_show_anchor_markers",
            help="Anchor markers are silent by default. Turn on to see them.",
        )
    with c2:
        st.markdown("**Cables**")
        st.checkbox("Show Edge Cable", value=True, key="ws_dm_show_edge_cable")
        st.checkbox("Show Cones", value=True, key="ws_dm_show_cones")
    with c3:
        st.markdown("**Fabric**")
        st.checkbox("Show Membrane", value=True, key="ws_dm_show_membrane")


def _render_seeds_panel():
    """The Element Seed Schedule."""
    st.markdown("### Element Seed Schedule")
    st.caption("Tap a row to select it for editing.")

    elements = st.session_state.get("ws_dm_elements", [])
    if not elements:
        st.info("Switch to the 3D View to build the model and generate elements.")
        return

    element_ids = [el["id"] for el in elements]
    active_id = st.session_state.get("ws_dm_active_element_id", None)
    
    if active_id in element_ids:
        default_index = element_ids.index(active_id) + 1
    else:
        default_index = 0

    selected_id = st.selectbox(
        "Select Element to Edit",
        options=[""] + element_ids,
        index=default_index,
        key="element_selector_box",
    )
    
    if selected_id:
        st.session_state["ws_dm_active_element_id"] = selected_id
    else:
        st.session_state.pop("ws_dm_active_element_id", None)

    # --- HTML Table ---
    css = """
    <style>
    .seed-table {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        overflow: hidden;
    }
    .seed-table th {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 8px 10px;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    .seed-table td {
        padding: 6px 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    .seed-table tr:hover {
        background-color: rgba(255, 255, 255, 0.08);
        cursor: pointer;
    }
    .seed-table tr.selected {
        background-color: rgba(255, 204, 0, 0.2);
        border-left: 3px solid #ffd166;
    }
    .seed-table .btn-select {
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 11px;
    }
    .seed-table .btn-selected {
        background-color: #ffd166;
        color: black;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
    }
    </style>
    """
    
    html = css + '<table class="seed-table">'
    html += '<thead><tr>'
    html += '<th>Select</th><th>ID</th><th>Type</th><th>Role</th>'
    html += '<th>Section/Material</th><th>Start Conn</th><th>End Conn</th>'
    html += '<th>Mesh</th><th>Support</th>'
    html += '</tr></thead><tbody>'
    
    for el in elements:
        is_selected = (el["id"] == selected_id)
        row_class = "selected" if is_selected else ""
        
        html += f'<tr class="{row_class}">'
        if is_selected:
            html += '<td><span class="btn-selected">Active</span></td>'
        else:
            html += '<td><span class="btn-select">Select above</span></td>'
            
        html += f'<td>{el["id"]}</td>'
        html += f'<td>{el["type"]}</td>'
        html += f'<td>{el["seed"].get("role", "-")}</td>'
        html += f'<td>{el["seed"].get("section_material", "-")}</td>'
        html += f'<td>{el["seed"].get("start_conn", "-")}</td>'
        html += f'<td>{el["seed"].get("end_conn", "-")}</td>'
        html += f'<td>{el["seed"].get("mesh_constraint", "-")}</td>'
        html += f'<td>{el["seed"].get("struct_support", "-")}</td>'
        html += '</tr>'
        
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

    if selected_id:
        st.write("---")
        st.write(f"**Editing: {selected_id}**")
        sel_el = next((el for el in elements if el["id"] == selected_id), None)
        if sel_el:
            st.json(sel_el["seed"])
            st.caption("Editing functionality (saving to session) coming in next patch.")


def _render_placeholder_panel(title):
    st.markdown(f"### {title}")
    st.info(f"The {title} panel will be implemented in Step 2B.")


# =============================================================================
# PAGE ENTRY POINT
# =============================================================================

def render_dome_multi_cone():
    """
    Render the Dome Multi-Cone workshop.
    """
    # --- The Drawer ---
    active_branch = render_explorer(default="geometry")

    # --- The Main Area ---
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    if active_branch == "geometry":
        _render_geometry_panel()
    elif active_branch == "layers":
        _render_layers_panel()
    elif active_branch == "seeds":
        _render_seeds_panel()
    elif active_branch == "materials":
        _render_placeholder_panel("Materials")
    elif active_branch == "sections":
        _render_placeholder_panel("Sections")

    # --- The Recipe (Bottom) ---
    st.markdown("---")
    with st.expander("⚙️ Model Inputs & Recipe", expanded=False):
        render_workshop(DOME_MULTI_CONE_RECIPE)
        
        curve_type = str(st.session_state.get("ws_dm_curve_type", "parabolic")).lower()
        if curve_type == "custom":
            st.info(
                "You have selected **Custom (Draw Profile)**. The custom "
                "elevation picker is not yet available. The 3D view will "
                "fall back to the default parabolic curve."
            )


# =============================================================================
# END OF ui/workshops/dome_multi_cone.py
# =============================================================================
