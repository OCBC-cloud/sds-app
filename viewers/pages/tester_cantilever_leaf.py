import math
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from viewers.figures._shared import apply_common_layout


def _init_lab_defaults():
    defaults = {
        "lab_has_column": True,
        
        # Column inputs
        "ws_sl_beam_landing_height": 4.0,
        "ws_sl_tie_landing_height": 5.0,
        
        # Midrib
        "ws_sl_outreach": 6.0,
        "ws_sl_arc_radius": 1.0,
        
        # Veins
        "lab_vein_length": 2.0,
        "ws_sl_rib_tilt": 0,
        "ws_sl_ribs_per_side": 5,
        
        # Pretensions
        "lab_warp_kN": 1.0,
        "lab_weft_kN": 1.0,
        "lab_cable_kN": 1.0,
        
        # Grounded Arch defaults
        "lab_parabolic_rise": 3.0,
        "lab_stub_length": 0.3,
        "lab_stub_direction": "+Y",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _draw_grounded_arch(outreach, rise, vein_length, tilt_deg, n_ribs, stub_length, stub_dir):
    """Custom 3D drawing for the 'No Column' grounded arch configuration."""
    fig = go.Figure()

    t = np.linspace(0, 1, 80)
    beam_x = outreach * t
    beam_z = 4.0 * rise * t * (1.0 - t)
    beam_y = np.zeros_like(t)

    fig.add_trace(go.Scatter3d(
        x=beam_x, y=beam_y, z=beam_z,
        mode="lines", line=dict(color="#FF6B6B", width=10), name="Midrib"
    ))

    stub_t = 0.25
    stub_x = outreach * stub_t
    stub_z = 4.0 * rise * stub_t * (1.0 - stub_t)
    stub_y_end = stub_length if stub_dir == "+Y" else -stub_length
    
    fig.add_trace(go.Scatter3d(
        x=[stub_x, stub_x], y=[0, stub_y_end], z=[stub_z, stub_z],
        mode="lines", line=dict(color="#e67e22", width=6), name="Stub"
    ))
    
    fig.add_trace(go.Scatter3d(
        x=[stub_x], y=[stub_y_end], z=[stub_z],
        mode="markers", marker=dict(color="#f1c40f", size=8), name="Membrane Anchor"
    ))

    rib_ts = np.linspace(0.08, 0.92, n_ribs)
    for rt in rib_ts:
        idx = int(rt * 79)
        rx = beam_x[idx]
        rz = beam_z[idx]
        
        hw = vein_length * (math.sin(math.pi * rt) ** 0.7)
        tilt_rad = math.radians(tilt_deg) * (math.sin(math.pi * rt) ** 0.7)
        tip_z = rz + hw * math.tan(tilt_rad)
        
        fig.add_trace(go.Scatter3d(
            x=[rx, rx], y=[-hw, hw], z=[tip_z, tip_z],
            mode="lines", line=dict(color="#3498db", width=3), showlegend=False
        ))

    n_u, n_v = 24, 24
    X_s, Y_s, Z_s = np.zeros((n_u, n_v)), np.zeros((n_u, n_v)), np.zeros((n_u, n_v))
    
    for i, ut in enumerate(np.linspace(0.02, 0.98, n_u)):
        idx = int(ut * 79)
        bx, bz = beam_x[idx], beam_z[idx]
        
        hw = vein_length * (math.sin(math.pi * ut) ** 0.7)
        tilt_rad = math.radians(tilt_deg) * (math.sin(math.pi * ut) ** 0.7)
        tip_z = bz + hw * math.tan(tilt_rad)

        for j, v in enumerate(np.linspace(-1, 1, n_v)):
            y_loc = v * hw
            z_edge = bz * (1 - abs(v)) + tip_z * abs(v)
            sag = 0.15 * hw * (1 - (2 * abs(v) - 1) ** 2)
            X_s[i, j] = bx
            Y_s[i, j] = y_loc
            Z_s[i, j] = z_edge - sag

    fig.add_trace(go.Surface(
        x=X_s, y=Y_s, z=Z_s,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55, showscale=False, hoverinfo="skip"
    ))

    return apply_common_layout(fig, rise)


def render_tester_cantilever_leaf():
    _init_lab_defaults()

    st.markdown("# Cantilever Leaf — Lab Test")
    st.markdown("Simple UI. 3D visual updates live.")
    st.markdown("---")

    # ============ THE COLUMN TOGGLE ============
    has_col = st.toggle("Column", value=bool(st.session_state["lab_has_column"]))
    st.session_state["lab_has_column"] = has_col

    st.markdown("---")

    if has_col:
        # ============ COLUMN MODE ============
        st.markdown("### 1. Column")
        col1, col2 = st.columns(2)
        with col1:
            beam_h = st.number_input(
                "Beam Landing Height (m)", min_value=1.0, max_value=30.0,
                value=float(st.session_state["ws_sl_beam_landing_height"]),
                step=0.5, format="%.2f", key="lab_beam_landing_input"
            )
            st.session_state["ws_sl_beam_landing_height"] = beam_h
        with col2:
            tie_h = st.number_input(
                "Tie Beam Landing Height (m)", min_value=beam_h + 0.5, max_value=40.0,
                value=max(float(st.session_state["ws_sl_tie_landing_height"]), beam_h + 0.5),
                step=0.5, format="%.2f", key="lab_tie_landing_input"
            )
            st.session_state["ws_sl_tie_landing_height"] = tie_h
            
    else:
        # ============ GROUNDED ARCH MODE ============
        st.markdown("### 1. Grounded Arch Parameters")
        col1, col2 = st.columns(2)
        with col1:
            rise = st.number_input(
                "Parabolic Rise (m)", min_value=1.0, max_value=20.0,
                value=float(st.session_state["lab_parabolic_rise"]),
                step=0.5, format="%.2f", key="lab_rise_input"
            )
            st.session_state["lab_parabolic_rise"] = rise
        with col2:
            stub_l = st.number_input(
                "Stub Length (m)", min_value=0.0, max_value=2.0,
                value=float(st.session_state["lab_stub_length"]),
                step=0.1, format="%.2f", key="lab_stub_len_input"
            )
            st.session_state["lab_stub_length"] = stub_l
            
        stub_dir = st.radio(
            "Stub Direction", ["+Y", "-Y"], 
            index=0 if st.session_state["lab_stub_direction"] == "+Y" else 1,
            horizontal=True, key="lab_stub_dir_input"
        )
        st.session_state["lab_stub_direction"] = stub_dir

    # ============ MIDRIB ============
    st.markdown("### 2. Midrib (Primary Beam)")
    col3, col4 = st.columns(2)
    with col3:
        outreach = st.number_input(
            "Midrib Length (m)", min_value=2.0, max_value=30.0,
            value=float(st.session_state["ws_sl_outreach"]),
            step=0.5, format="%.2f", key="lab_outreach_input"
        )
        st.session_state["ws_sl_outreach"] = outreach
    with col4:
        arc_r = st.number_input(
            "Midrib Arc Radius (m)", min_value=0.0, max_value=20.0,
            value=float(st.session_state["ws_sl_arc_radius"]),
            step=0.25, format="%.2f", key="lab_arc_r_input"
        )
        st.session_state["ws_sl_arc_radius"] = arc_r

    # ============ VEINS ============
    st.markdown("### 3. Veins (Secondary Beams)")
    col5, col6 = st.columns(2)
    with col5:
        vein_length = st.number_input(
            "Vein Length (m)", min_value=0.5, max_value=6.0,
            value=float(st.session_state["lab_vein_length"]),
            step=0.25, format="%.2f", key="lab_vein_length_input"
        )
        st.session_state["lab_vein_length"] = vein_length
    with col6:
        tilt = st.number_input(
            "Vein Tilt Angle (deg)", min_value=-45.0, max_value=45.0,
            value=float(st.session_state["ws_sl_rib_tilt"]),
            step=1.0, format="%.1f", key="lab_tilt_input"
        )
        st.session_state["ws_sl_rib_tilt"] = tilt

    # ============ MESH PRETENSIONS ============
    st.markdown("### 5. Mesh Pretensions")
    col9, col10 = st.columns(2)
    with col9:
        warp = st.number_input(
            "Warp Pretension (kN)", min_value=0.1, max_value=20.0,
            value=float(st.session_state["lab_warp_kN"]),
            step=0.1, format="%.2f", key="lab_warp_input"
        )
        st.session_state["lab_warp_kN"] = warp
    with col10:
        weft = st.number_input(
            "Weft Pretension (kN)", min_value=0.1, max_value=20.0,
            value=float(st.session_state["lab_weft_kN"]),
            step=0.1, format="%.2f", key="lab_weft_input"
        )
        st.session_state["lab_weft_kN"] = weft

    # ============ PERIMETER CABLE ============
    st.markdown("### 6. Perimeter Cable")
    cable = st.number_input(
        "Cable Pretension (kN)", min_value=0.1, max_value=50.0,
        value=float(st.session_state["lab_cable_kN"]),
        step=0.1, format="%.2f", key="lab_cable_input"
    )
    st.session_state["lab_cable_kN"] = cable

    # ============ 3D VISUAL ============
    st.markdown("---")
    st.markdown("### 3D Preview")
    
    if has_col:
        # We are just using the production viewer for the preview for now.
        # Note: The production viewer looks at ws_sl_column_height, which we 
        # haven't set here. So the visual might look a bit weird until we 
        # update the drawing function to use the new tie beam logic.
        from viewers.figures.cantilever_leaf import build_cantilever_leaf
        st.session_state["ws_sl_column_height"] = st.session_state["ws_sl_tie_landing_height"]
        fig = build_cantilever_leaf()
    else:
        fig = _draw_grounded_arch(
            outreach=outreach,
            rise=st.session_state["lab_parabolic_rise"],
            vein_length=vein_length,
            tilt_deg=tilt,
            n_ribs=st.session_state["ws_sl_ribs_per_side"],
            stub_length=st.session_state["lab_stub_length"],
            stub_dir=st.session_state["lab_stub_direction"]
        )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ============ BACK ============
    st.markdown("---")
    if st.button("Back to Lab", key="lab_leaf_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
