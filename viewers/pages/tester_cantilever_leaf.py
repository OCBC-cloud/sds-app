import math
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from viewers.figures._shared import apply_common_layout


def _init_lab_defaults():
    defaults = {
        "ws_sl_beam_landing_height": 4.0,
        "ws_sl_tie_landing_height": 5.0,
        "ws_sl_outreach": 6.0,
        "ws_sl_arc_radius": 1.0,
        "lab_vein_length": 2.0,
        "ws_sl_rib_tilt": 0,
        "ws_sl_ribs_per_side": 5,
        "lab_warp_kN": 1.0,
        "lab_weft_kN": 1.0,
        "lab_cable_kN": 1.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def generate_universal_leaf_data(
    beam_h, tie_h, outreach, arc_r, vein_length, tilt_deg, n_ribs
):
    """
    Creates the Universal Payload (Nodes, Elements, Surfaces).
    """
    nodes = []
    elements = []
    
    # We will build the membrane as a grid of nodes
    n_u = 24
    n_v = 24
    grid_indices = np.zeros((n_u, n_v), dtype=int)

    # 1. Column Base -> Beam Landing
    nodes.append([0.0, 0.0, 0.0]) # Node 0
    nodes.append([0.0, 0.0, beam_h]) # Node 1
    elements.append({"a": 0, "b": 1, "kind": "column"})

    # 2. Column Beam Landing -> Tie Landing
    nodes.append([0.0, 0.0, tie_h]) # Node 2
    elements.append({"a": 1, "b": 2, "kind": "column"})

    # 3. Midrib (Spine)
    n_beam = 20
    t_beam = np.linspace(0, 1, n_beam)
    spine_indices = [1]
    
    for i in range(1, n_beam):
        t = t_beam[i]
        bx = outreach * t
        bz = beam_h + (arc_r * 0.5) * 4.0 * t * (1.0 - t)
        
        idx = len(nodes)
        nodes.append([bx, 0.0, bz])
        spine_indices.append(idx)
        elements.append({"a": spine_indices[-2], "b": idx, "kind": "primary"})

    # 4. Tie Beam
    tie_attach_x = outreach * 0.33
    if arc_r > 0.01:
        target_rise = tie_h - beam_h
        max_rise = arc_r * 0.5 * 4.0 * 0.25 
        if 0 < target_rise <= max_rise:
            S = arc_r * 0.5
            A = -4.0 * S / (outreach ** 2)
            B = 4.0 * S / outreach
            C = -target_rise
            disc = B**2 - 4*A*C
            if disc >= 0:
                x1 = (-B + math.sqrt(disc)) / (2*A)
                if 0 < x1 < outreach:
                    tie_attach_x = x1
                    
    closest_spine_idx = 1
    min_dist = float('inf')
    for idx in spine_indices[1:]:
        dist = abs(nodes[idx][0] - tie_attach_x)
        if dist < min_dist:
            min_dist = dist
            closest_spine_idx = idx
            
    elements.append({"a": 2, "b": closest_spine_idx, "kind": "tie"})

    # 5. Membrane Grid & Veins
    rib_ts = np.linspace(0.08, 0.92, n_ribs)
    
    for i, ut in enumerate(np.linspace(0.02, 0.98, n_u)):
        # Find spine position
        t = ut
        bx = outreach * t
        bz = beam_h + (arc_r * 0.5) * 4.0 * t * (1.0 - t)
        
        hw = vein_length * (math.sin(math.pi * ut) ** 0.7)
        tilt_rad = math.radians(tilt_deg) * (math.sin(math.pi * ut) ** 0.7)
        tip_z = bz + hw * math.tan(tilt_rad)

        # Find the spine node for this u-slice
        spine_idx = spine_indices[int(ut * (n_beam - 1))]
        
        for j, v in enumerate(np.linspace(-1, 1, n_v)):
            y_loc = v * hw
            z_edge = bz * (1 - abs(v)) + tip_z * abs(v)
            sag = 0.15 * hw * (1 - (2 * abs(v) - 1) ** 2)
            z_loc = z_edge - sag
            
            idx = len(nodes)
            nodes.append([bx, y_loc, z_loc])
            grid_indices[i, j] = idx
            
            # Add edge elements for the outer rim
            if j > 0:
                elements.append({"a": grid_indices[i, j-1], "b": idx, "kind": "membrane_edge"})
            if i > 0:
                elements.append({"a": grid_indices[i-1, j], "b": idx, "kind": "membrane_edge"})

        # If this slice is at a rib location, draw the rib elements
        if any(abs(ut - rt) < 0.05 for rt in rib_ts):
            # Left Tip
            l_idx = grid_indices[i, 0]
            elements.append({"a": spine_idx, "b": l_idx, "kind": "rib"})
            # Right Tip
            r_idx = grid_indices[i, -1]
            elements.append({"a": spine_idx, "b": r_idx, "kind": "rib"})

    return nodes, elements, grid_indices


def draw_from_universal_data(nodes, elements, grid_indices, max_height):
    """Takes the universal payload and draws it."""
    fig = go.Figure()
    
    # Draw Membrane Surface
    X_s = np.zeros(grid_indices.shape)
    Y_s = np.zeros(grid_indices.shape)
    Z_s = np.zeros(grid_indices.shape)
    
    for i in range(grid_indices.shape[0]):
        for j in range(grid_indices.shape[1]):
            node = nodes[grid_indices[i, j]]
            X_s[i, j] = node[0]
            Y_s[i, j] = node[1]
            Z_s[i, j] = node[2]
            
    fig.add_trace(go.Surface(
        x=X_s, y=Y_s, z=Z_s,
        colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
        opacity=0.55, showscale=False, hoverinfo="skip"
    ))

    # Draw Elements (Lines)
    for elem in elements:
        a = nodes[elem["a"]]
        b = nodes[elem["b"]]
        kind = elem["kind"]
        
        color = "#ffffff"
        width = 3
        name = ""
        
        if kind == "column":
            color = "#2ecc71"; width = 10; name = "Column"
        elif kind == "primary":
            color = "#FF6B6B"; width = 8; name = "Midrib"
        elif kind == "tie":
            color = "#f39c12"; width = 6; name = "Tie Beam"
        elif kind == "rib":
            color = "#3498db"; width = 3; name = "Veins"
        elif kind == "membrane_edge":
            continue # Don't draw the membrane grid lines, just the surface
            
        fig.add_trace(go.Scatter3d(
            x=[a[0], b[0]], y=[a[1], b[1]], z=[a[2], b[2]],
            mode="lines", line=dict(color=color, width=width), name=name, showlegend=False
        ))

    return apply_common_layout(fig, max_height)


def render_tester_cantilever_leaf():
    _init_lab_defaults()

    st.markdown("# Parametric Leaf — Lab Test")
    st.markdown("Universal Data Pipeline with Membrane.")
    st.markdown("---")

    st.markdown("### 1. Column")
    col1, col2 = st.columns(2)
    with col1:
        beam_h = st.number_input("Beam Landing Height (m)", min_value=1.0, max_value=30.0, value=float(st.session_state["ws_sl_beam_landing_height"]), step=0.5, format="%.2f", key="lab_beam_h")
        st.session_state["ws_sl_beam_landing_height"] = beam_h
    with col2:
        tie_h = st.number_input("Tie Beam Landing Height (m)", min_value=beam_h + 0.5, max_value=40.0, value=max(float(st.session_state["ws_sl_tie_landing_height"]), beam_h + 0.5), step=0.5, format="%.2f", key="lab_tie_h")
        st.session_state["ws_sl_tie_landing_height"] = tie_h

    st.markdown("### 2. Midrib (Primary Beam)")
    col3, col4 = st.columns(2)
    with col3:
        outreach = st.number_input("Midrib Length (m)", min_value=2.0, max_value=30.0, value=float(st.session_state["ws_sl_outreach"]), step=0.5, format="%.2f", key="lab_outreach")
        st.session_state["ws_sl_outreach"] = outreach
    with col4:
        arc_r = st.number_input("Midrib Arc Radius (m)", min_value=0.0, max_value=20.0, value=float(st.session_state["ws_sl_arc_radius"]), step=0.25, format="%.2f", key="lab_arc_r")
        st.session_state["ws_sl_arc_radius"] = arc_r

    st.markdown("### 3. Veins (Secondary Beams)")
    col5, col6 = st.columns(2)
    with col5:
        vein_length = st.number_input("Vein Length (m)", min_value=0.5, max_value=6.0, value=float(st.session_state["lab_vein_length"]), step=0.25, format="%.2f", key="lab_vein_len")
        st.session_state["lab_vein_length"] = vein_length
    with col6:
        tilt = st.number_input("Vein Tilt Angle (deg)", min_value=-45.0, max_value=45.0, value=float(st.session_state["ws_sl_rib_tilt"]), step=1.0, format="%.1f", key="lab_tilt")
        st.session_state["ws_sl_rib_tilt"] = tilt

    st.markdown("---")
    st.markdown("### 3D Preview")
    
    nodes, elements, grid_indices = generate_universal_leaf_data(
        beam_h, tie_h, outreach, arc_r, vein_length, tilt, 
        st.session_state["ws_sl_ribs_per_side"]
    )
    
    fig = draw_from_universal_data(nodes, elements, grid_indices, tie_h)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")
    if st.button("Back to Lab", key="lab_leaf_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
