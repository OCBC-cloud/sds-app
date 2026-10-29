import math
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from viewers.figures._shared import apply_common_layout
from ui.components.lab_pickerboard import lab_pickerboard


def _init_lab_defaults():
    defaults = {
        "lab_step": 1,
        "lab_support_type": "Ground Stand",
        "ws_sl_beam_landing_height": 4.0,
        "ws_sl_column_top_height": 6.0,
        "ws_sl_outreach": 6.0,
        "ws_sl_arc_radius": 1.0,
        "lab_vein_length": 2.0,
        "ws_sl_rib_tilt": 0,
        "ws_sl_ribs_per_side": 5,
        "lab_warp_kN": 1.0,
        "lab_weft_kN": 1.0,
        "lab_cable_kN": 1.0,
        "lab_active_dots": [],
        "lab_boundary_loop": [],
        "lab_boundary_connected": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def draw_wizard_preview(
    beam_h, col_top_h, outreach, arc_r, vein_length, tilt_deg, n_ribs,
    boundary_loop=None
):
    """Draws a clean 3D preview with correct rib attachments and the boundary loop."""
    fig = go.Figure()

    # 1. Column
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, col_top_h],
        mode="lines", line=dict(color="#2ecc71", width=10), name="Column"
    ))
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers", marker=dict(color="#2ecc71", size=10, symbol="square"), name="Base"
    ))

    # 2. Midrib (Parabolic Arch)
    n_beam = 80 
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_y = np.zeros_like(t_beam)
    beam_z = beam_h + (arc_r * 0.5) * 4.0 * t_beam * (1.0 - t_beam)
    
    fig.add_trace(go.Scatter3d(
        x=beam_x, y=beam_y, z=beam_z,
        mode="lines", line=dict(color="#FF6B6B", width=8), name="Midrib"
    ))

    # 3. Diagonal Tie Beam
    tie_attach_x = outreach / 3.0
    tie_attach_z = beam_h + (arc_r * 0.5) * 4.0 * (1.0/3.0) * (1.0 - 1.0/3.0)
    
    fig.add_trace(go.Scatter3d(
        x=[0, tie_attach_x], y=[0, 0], z=[col_top_h, tie_attach_z],
        mode="lines", line=dict(color="#f39c12", width=6), name="Tie Beam"
    ))

    # 4. Veins
    rib_ts = np.linspace(0.08, 0.92, n_ribs)
    for rt in rib_ts:
        idx = int(rt * (n_beam - 1))
        rx = beam_x[idx]
        rz = beam_z[idx]
        
        hw = vein_length * (math.sin(math.pi * rt) ** 0.7)
        tilt_rad = math.radians(tilt_deg) * (math.sin(math.pi * rt) ** 0.7)
        tip_z = rz + hw * math.tan(tilt_rad)
        
        # Left and Right Vein segments attaching at the centerline
        fig.add_trace(go.Scatter3d(
            x=[rx, rx], y=[0, -hw], z=[rz, tip_z],
            mode="lines", line=dict(color="#3498db", width=3), showlegend=False
        ))
        fig.add_trace(go.Scatter3d(
            x=[rx, rx], y=[0, hw], z=[rz, tip_z],
            mode="lines", line=dict(color="#3498db", width=3), showlegend=False
        ))

    # 5. Membrane Surface
    n_u, n_v = 24, 24
    X_s, Y_s, Z_s = np.zeros((n_u, n_v)), np.zeros((n_u, n_v)), np.zeros((n_u, n_v))
    
    for i, ut in enumerate(np.linspace(0.02, 0.98, n_u)):
        idx = int(ut * (n_beam - 1))
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

    # 6. Boundary Loop (if connected)
    if boundary_loop and len(boundary_loop) > 1:
        lx = [p[0] for p in boundary_loop]
        ly = [p[1] for p in boundary_loop]
        lz = [p[2] for p in boundary_loop]
        # Close the loop
        lx.append(boundary_loop[0][0])
        ly.append(boundary_loop[0][1])
        lz.append(boundary_loop[0][2])
        fig.add_trace(go.Scatter3d(
            x=lx, y=ly, z=lz,
            mode="lines", line=dict(color="#f1c40f", width=6), name="Perimeter Cable"
        ))
        # Add markers at the picked anchor points
        fig.add_trace(go.Scatter3d(
            x=[p[0] for p in boundary_loop], 
            y=[p[1] for p in boundary_loop], 
            z=[p[2] for p in boundary_loop],
            mode="markers", marker=dict(color="#f1c40f", size=6), name="Anchors"
        ))

    return apply_common_layout(fig, col_top_h)


def _build_boundary_loop_from_dots(active_dots, n_ribs, outreach, arc_r, beam_h, vein_length, tilt):
    """
    Converts the active dot indices from the pickerboard into a 3D boundary loop.
    Dots are indexed 0..n_ribs-1 for the ribs (right side), and -1 for the beam tip.
    """
    loop_pts = []
    # We assume the user is picking the right-side tips (in +Y)
    for dot in sorted(active_dots):
        if dot == -1:
            # Beam tip
            bx = outreach
            bz = beam_h + (arc_r * 0.5) * 4.0 * 1.0 * (1.0 - 1.0) # = beam_h
            loop_pts.append([bx, 0.0, bz])
        else:
            rt = dot / max(1, n_ribs - 1)
            bx = outreach * rt
            bz = beam_h + (arc_r * 0.5) * 4.0 * rt * (1.0 - rt)
            hw = vein_length * (math.sin(math.pi * rt) ** 0.7)
            tilt_rad = math.radians(tilt) * (math.sin(math.pi * rt) ** 0.7)
            tip_z = bz + hw * math.tan(tilt_rad)
            loop_pts.append([bx, hw, tip_z])
            
    return loop_pts


def render_tester_cantilever_leaf():
    _init_lab_defaults()
    
    step = st.session_state["lab_step"]
    progress = (step - 1) / 6.0
    st.progress(progress)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # ================= SCREEN 1: FOUNDATION =================
    if step == 1:
        st.markdown("### Step 1: Foundation & Support")
        support_types = ["Ground Stand", "Wall Mounted", "Suspended"]
        support_idx = support_types.index(st.session_state["lab_support_type"])
        support = st.radio("Support Type", support_types, index=support_idx)
        st.session_state["lab_support_type"] = support
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Next: Column ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 2
            st.rerun()

    # ================= SCREEN 2: COLUMN =================
    elif step == 2:
        st.markdown("### Step 2: Column Heights")
        col1, col2 = st.columns(2)
        with col1:
            beam_h = st.number_input("Beam Landing (m)", min_value=1.0, max_value=30.0, value=float(st.session_state["ws_sl_beam_landing_height"]), step=0.5)
            st.session_state["ws_sl_beam_landing_height"] = beam_h
        with col2:
            col_top_h = st.number_input("Column Top Height (m)", min_value=beam_h + 0.5, max_value=40.0, value=max(float(st.session_state["ws_sl_column_top_height"]), beam_h + 0.5), step=0.5)
            st.session_state["ws_sl_column_top_height"] = col_top_h

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        if col_a.button("⬅ Back", use_container_width=True):
            st.session_state["lab_step"] = 1
            st.rerun()
        if col_b.button("Next: Midrib ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 3
            st.rerun()

    # ================= SCREEN 3: MIDRIB =================
    elif step == 3:
        st.markdown("### Step 3: Midrib (Primary Beam)")
        col3, col4 = st.columns(2)
        with col3:
            outreach = st.number_input("Midrib Length (m)", min_value=2.0, max_value=30.0, value=float(st.session_state["ws_sl_outreach"]), step=0.5)
            st.session_state["ws_sl_outreach"] = outreach
        with col4:
            arc_r = st.number_input("Arc Radius (m)", min_value=0.0, max_value=20.0, value=float(st.session_state["ws_sl_arc_radius"]), step=0.25)
            st.session_state["ws_sl_arc_radius"] = arc_r

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        if col_a.button("⬅ Back", use_container_width=True):
            st.session_state["lab_step"] = 2
            st.rerun()
        if col_b.button("Next: Veins ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 4
            st.rerun()

    # ================= SCREEN 4: VEINS =================
    elif step == 4:
        st.markdown("### Step 4: Veins (Secondary Beams)")
        col5, col6 = st.columns(2)
        with col5:
            vein_length = st.number_input("Vein Length (m)", min_value=0.5, max_value=6.0, value=float(st.session_state["lab_vein_length"]), step=0.25)
            st.session_state["lab_vein_length"] = vein_length
        with col6:
            tilt = st.number_input("Vein Tilt (deg)", min_value=-45.0, max_value=45.0, value=float(st.session_state["ws_sl_rib_tilt"]), step=1.0)
            st.session_state["ws_sl_rib_tilt"] = tilt
            
        n_ribs = st.number_input("Number of Ribs (Veins)", min_value=1, max_value=15, value=int(st.session_state["ws_sl_ribs_per_side"]), step=1)
        st.session_state["ws_sl_ribs_per_side"] = n_ribs

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        if col_a.button("⬅ Back", use_container_width=True):
            st.session_state["lab_step"] = 3
            st.rerun()
        if col_b.button("Next: Pretensions ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 5
            st.rerun()

    # ================= SCREEN 5: PRETENSIONS =================
    elif step == 5:
        st.markdown("### Step 5: Pretensions")
        col7, col8, col9 = st.columns(3)
        with col7:
            warp = st.number_input("Warp (kN)", min_value=0.1, max_value=20.0, value=float(st.session_state["lab_warp_kN"]), step=0.1)
            st.session_state["lab_warp_kN"] = warp
        with col8:
            weft = st.number_input("Weft (kN)", min_value=0.1, max_value=20.0, value=float(st.session_state["lab_weft_kN"]), step=0.1)
            st.session_state["lab_weft_kN"] = weft
        with col9:
            cable = st.number_input("Cable (kN)", min_value=0.1, max_value=50.0, value=float(st.session_state["lab_cable_kN"]), step=0.1)
            st.session_state["lab_cable_kN"] = cable

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        if col_a.button("⬅ Back", use_container_width=True):
            st.session_state["lab_step"] = 4
            st.rerun()
        if col_b.button("Next: Pick Boundary ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 6
            st.rerun()

    # ================= SCREEN 6: PICK BOUNDARY =================
    elif step == 6:
        st.markdown("### Step 6: Pick Boundary Anchors")
        st.info("Tap the dots to set the anchor points, then click Connect Loop.")
        
        # Generate the rib_lengths array for the pickerboard to draw
        n_ribs = int(st.session_state["ws_sl_ribs_per_side"])
        outreach = float(st.session_state["ws_sl_outreach"])
        rib_lengths = [outreach * (0.08 + 0.84 * i / max(1, n_ribs - 1)) for i in range(n_ribs)]
        
        # Render the pickerboard
        picker_data = lab_pickerboard(
            shape="leaf",
            reach=outreach,
            width=float(st.session_state["lab_vein_length"]),
            rib_reach=outreach * 0.5,
            rib_lengths=rib_lengths,
            key="lab_picker_1"
        )
        
        # Save the active dots to session state
        if picker_data and "active_dots" in picker_data:
            st.session_state["lab_active_dots"] = picker_data["active_dots"]
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔗 Connect Loop", type="secondary", use_container_width=True):
            active_dots = st.session_state.get("lab_active_dots", [])
            if len(active_dots) > 0:
                loop_pts = _build_boundary_loop_from_dots(
                    active_dots=active_dots,
                    n_ribs=n_ribs,
                    outreach=outreach,
                    arc_r=st.session_state["ws_sl_arc_radius"],
                    beam_h=st.session_state["ws_sl_beam_landing_height"],
                    vein_length=st.session_state["lab_vein_length"],
                    tilt=st.session_state["ws_sl_rib_tilt"]
                )
                st.session_state["lab_boundary_loop"] = loop_pts
                st.session_state["lab_boundary_connected"] = True
                st.success(f"Boundary loop connected with {len(loop_pts)} anchors.")
            else:
                st.warning("Please pick at least one dot to connect.")

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        if col_a.button("⬅ Back", use_container_width=True):
            st.session_state["lab_step"] = 5
            st.rerun()
        if col_b.button("Review Structure ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 7
            st.rerun()

    # ================= SCREEN 7: REVIEW & ANALYZE =================
    elif step == 7:
        st.markdown("### Step 7: Review & Analyze")
        
        fig = draw_wizard_preview(
            beam_h=st.session_state["ws_sl_beam_landing_height"],
            col_top_h=st.session_state["ws_sl_column_top_height"],
            outreach=st.session_state["ws_sl_outreach"],
            arc_r=st.session_state["ws_sl_arc_radius"],
            vein_length=st.session_state["lab_vein_length"],
            tilt_deg=st.session_state["ws_sl_rib_tilt"],
            n_ribs=st.session_state["ws_sl_ribs_per_side"],
            boundary_loop=st.session_state.get("lab_boundary_loop", [])
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Analyze & Size Steel", type="primary", use_container_width=True):
            st.success("Solvers not connected yet. This is where the FDM and Steel Sizing will run!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ Back to Pickerboard", use_container_width=True):
            st.session_state["lab_step"] = 6
            st.rerun()

    # ================= BACK TO LAB =================
    st.markdown("---")
    if st.button("Exit to Lab", key="lab_exit", use_container_width=True):
        st.session_state["lab_step"] = 1
        st.session_state.page = "lab"
        st.rerun()
