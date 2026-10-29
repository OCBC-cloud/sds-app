import math
import streamlit as st

from viewers.figures.cantilever_leaf import build_cantilever_leaf


def _init_lab_defaults():
    """Set only the defaults we need for the visual."""
    defaults = {
        "ws_sl_column_height": 5.0,
        "ws_sl_outreach": 6.0,
        "ws_sl_arc_radius": 1.0,
        "ws_sl_rib_tilt": 0,
        "ws_sl_ribs_per_side": 5,       # default leaves (5 pairs)
        "ws_sl_strut_joint_height": 3.0,
        "ws_sl_strut_angle_deg": 42.0,
        "ws_sl_arrangement": "single",
        "ws_sl_rib_override_active": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Lab-only values (not used by the figure yet)
    if "lab_warp_kN" not in st.session_state:
        st.session_state["lab_warp_kN"] = 1.0
    if "lab_weft_kN" not in st.session_state:
        st.session_state["lab_weft_kN"] = 1.0
    if "lab_cable_kN" not in st.session_state:
        st.session_state["lab_cable_kN"] = 1.0


def render_tester_cantilever_leaf():
    _init_lab_defaults()

    st.markdown("# Cantilever Leaf — Lab Test")
    st.markdown("Simple UI. 3D visual updates live. No solver yet.")

    st.markdown("---")

    # ============ COLUMN ============
    st.markdown("### 1. Column")
    col_h = st.number_input(
        "Column Height (m)",
        min_value=2.0, max_value=30.0,
        value=float(st.session_state["ws_sl_column_height"]),
        step=0.5, format="%.2f",
        key="lab_col_h_input",
    )
    st.session_state["ws_sl_column_height"] = col_h

    # ============ MIDRIB ============
    st.markdown("### 2. Midrib (Primary Beam)")
    col1, col2 = st.columns(2)
    with col1:
        outreach = st.number_input(
            "Midrib Length (m)",
            min_value=2.0, max_value=30.0,
            value=float(st.session_state["ws_sl_outreach"]),
            step=0.5, format="%.2f",
            key="lab_outreach_input",
        )
        st.session_state["ws_sl_outreach"] = outreach
    with col2:
        arc_r = st.number_input(
            "Midrib Arc Radius (m)",
            min_value=0.0, max_value=20.0,
            value=float(st.session_state["ws_sl_arc_radius"]),
            step=0.25, format="%.2f",
            key="lab_arc_r_input",
        )
        st.session_state["ws_sl_arc_radius"] = arc_r

    # ============ VEINS ============
    st.markdown("### 3. Veins (Secondary Beams)")
    col3, col4 = st.columns(2)
    with col3:
        vein_length = st.number_input(
            "Vein Length (m)",
            min_value=0.5, max_value=6.0,
            value=2.0, step=0.25, format="%.2f",
            key="lab_vein_length_input",
        )
        # Map vein length to half-width of the middle rib (2.0 m default)
        # The geometry uses outreach * 0.42 for the mid half width,
        # so adjust outreach-relative factor to match the input exactly.
        # We store it for the future; the drawing uses the production law for now.
        st.session_state["lab_vein_length"] = vein_length
    with col4:
        tilt = st.number_input(
            "Vein Tilt Angle (deg)",
            min_value=-45.0, max_value=45.0,
            value=float(st.session_state["ws_sl_rib_tilt"]),
            step=1.0, format="%.1f",
            key="lab_tilt_input",
        )
        st.session_state["ws_sl_rib_tilt"] = tilt

    # ============ STRUT ============
    st.markdown("### 4. Strut")
    col5, col6 = st.columns(2)
    with col5:
        strut_joint = st.number_input(
            "Strut Joint Height on Column (m)",
            min_value=0.5, max_value=float(col_h),
            value=min(float(st.session_state["ws_sl_strut_joint_height"]), float(col_h)),
            step=0.25, format="%.2f",
            key="lab_strut_joint_input",
        )
        st.session_state["ws_sl_strut_joint_height"] = strut_joint
    with col6:
        strut_angle = st.number_input(
            "Strut Angle (deg from horizontal)",
            min_value=15.0, max_value=85.0,
            value=float(st.session_state["ws_sl_strut_angle_deg"]),
            step=1.0, format="%.1f",
            key="lab_strut_angle_input",
        )
        st.session_state["ws_sl_strut_angle_deg"] = strut_angle

    # ============ MESH PRETENSIONS ============
    st.markdown("### 5. Mesh Pretensions")
    col7, col8 = st.columns(2)
    with col7:
        warp = st.number_input(
            "Warp Pretension (kN)",
            min_value=0.1, max_value=20.0,
            value=float(st.session_state["lab_warp_kN"]),
            step=0.1, format="%.2f",
            key="lab_warp_input",
        )
        st.session_state["lab_warp_kN"] = warp
    with col8:
        weft = st.number_input(
            "Weft Pretension (kN)",
            min_value=0.1, max_value=20.0,
            value=float(st.session_state["lab_weft_kN"]),
            step=0.1, format="%.2f",
            key="lab_weft_input",
        )
        st.session_state["lab_weft_kN"] = weft

    # ============ PERIMETER CABLE ============
    st.markdown("### 6. Perimeter Cable")
    cable = st.number_input(
        "Cable Pretension (kN)",
        min_value=0.1, max_value=50.0,
        value=float(st.session_state["lab_cable_kN"]),
        step=0.1, format="%.2f",
        key="lab_cable_input",
    )
    st.session_state["lab_cable_kN"] = cable

    # ============ 3D VISUAL ============
    st.markdown("---")
    st.markdown("### 3D Preview")
    build_cantilever_leaf()

    # ============ BACK ============
    st.markdown("---")
    if st.button("Back to Lab", key="lab_leaf_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
