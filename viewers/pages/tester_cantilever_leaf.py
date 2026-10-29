import math
import streamlit as st
import numpy as np
import plotly.graph_objects as go

from viewers.figures._shared import apply_common_layout
from ui.components.lab_pickerboard import lab_pickerboard


def _init_lab_defaults():
    defaults = {
        "lab_step": 1,
        "lab_shape": "leaf",
        "lab_reach": 6.0,
        "lab_width": 4.0,
        "lab_rib_lengths": [],
        "lab_picked_dots": [],
        
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


def draw_wizard_preview(beam_h, tie_h, outreach, arc_r, vein_length, tilt_deg, n_ribs):
    """Draws a clean 3D preview."""
    fig = go.Figure()

    # 1. Column
    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, tie_h],
        mode="lines", line=dict(color="#2ecc71", width=10), name="Column"
    ))
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers", marker=dict(color="#2ecc71", size=10, symbol="square"), name="Base"
    ))

    # 2. Midrib
    n_beam = 40
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_y = np.zeros_like(t_beam)
    beam_z = beam_h + (arc_r * 0.5) * 4.0 * t_beam * (1.0 - t_beam)
    
    fig.add_trace(go.Scatter3d(
        x=beam_x, y=beam_y, z=beam_z,
        mode="lines", line=dict(color="#FF6B6B", width=8), name="Midrib"
    ))

    # 3. Tie Beam
    tie_attach_x = outreach * 0.33
    if arc_r > 0.01:
        target_rise = tie_h - beam_h
        max_rise = arc_r * 0.5
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

    fig.add_trace(go.Scatter3d(
        x=[0, tie_attach_x], y=[0, 0], z=[tie_h, tie_h],
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
        
        fig.add_trace(go.Scatter3d(
            x=[rx, rx], y=[-hw, hw], z=[tip_z, tip_z],
            mode="lines", line=dict(color="#3498db", width=3), showlegend=False
        ))

    # 5. Membrane
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

    return apply_common_layout(fig, tie_h)


def render_tester_cantilever_leaf():
    _init_lab_defaults()
    
    step = st.session_state["lab_step"]
    progress = (step - 1) / 5.0
    st.progress(progress)
    st.markdown("<br>", unsafe_allow_html=True)

    # ================= SCREEN 1: PICKERBOARD =================
    if step == 1:
        st.markdown("### Step 1: Plan View Pickers")
        st.info("Tap the dots on the plan view to set the anchor points.")
        
        # The pickerboard takes the current state
        picker_data = lab_pickerboard(
            shape="leaf",
            reach=float(st.session_state["lab_reach"]),
            width=float(st.session_state["lab_width"]),
            rib_reach=float(st.session_state["lab_reach"] * 0.5),
            rib_lengths=st.session_state["lab_rib_lengths"],
            key="lab_picker_1"
        )
        
        # Save the picked dots to session state
        if picker_data and "rib_lengths" in picker_data:
            st.session_state["lab_rib_lengths"] = picker_data["rib_lengths"]
            # Note: the HTML sends back rib_lengths, we'll store the picked ones
            # For now, we assume all returned dots are the picked ones.
            # In a future version, the HTML will explicitly send "picked_indices".
            st.session_state["lab_picked_dots"] = picker_data["rib_lengths"]

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
            tie_h = st.number_input("Tie Beam Landing (m)", min_value=beam_h + 0.5, max_value=40.0, value=max(float(st.session_state["ws_sl_tie_landing_height"]), beam_h + 0.5), step=0.5)
            st.session_state["ws_sl_tie_landing_height"] = tie_h

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
        if col_b.button("Review Structure ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 6
            st.rerun()

    # ================= SCREEN 6: REVIEW & ANALYZE =================
    elif step == 6:
        st.markdown("### Step 6: Review & Analyze")
        
        fig = draw_wizard_preview(
            beam_h=st.session_state["ws_sl_beam_landing_height"],
            tie_h=st.session_state["ws_sl_tie_landing_height"],
            outreach=st.session_state["ws_sl_outreach"],
            arc_r=st.session_state["ws_sl_arc_radius"],
            vein_length=st.session_state["lab_vein_length"],
            tilt_deg=st.session_state["ws_sl_rib_tilt"],
            n_ribs=st.session_state["ws_sl_ribs_per_side"]
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Analyze & Size Steel", type="primary", use_container_width=True):
            st.success("Solvers not connected yet. This is where the FDM and Steel Sizing will run!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ Back to Pretensions", use_container_width=True):
            st.session_state["lab_step"] = 5
            st.rerun()

    # ================= BACK TO LAB =================
    st.markdown("---")
    if st.button("Exit to Lab", key="lab_exit", use_container_width=True):
        st.session_state["lab_step"] = 1
        st.session_state.page = "lab"
        st.rerun()
