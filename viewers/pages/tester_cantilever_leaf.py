import streamlit as st
import numpy as np
import plotly.graph_objects as go

from viewers.figures.cantilever_leaf_lab import compute_lab_leaf_geometry, build_cantilever_leaf_lab_figure
from engine.membrane_boundary import build_and_solve
from engine.cantilever_frame_builder import build_cantilever_frame
from engine.frame_analysis import analyze_and_size_frame
from viewers.figures._shared import apply_common_layout

LAB_TESTER_CSS = """
    <style>
    .stApp > header { display: none !important; }
    .block-container { padding-top: 1.2rem !important; max-width: 1200px; }
    .ctl-topbar { display: flex; justify-content: space-between; align-items: center; padding: 0 0 0.6rem 0; border-bottom: 1px solid #1e2a3a; margin-bottom: 1.2rem; }
    .ctl-wordmark { font-size: 1.1rem; font-weight: 700; color: #f39c12; letter-spacing: 2px; }
    .ctl-header { font-size: 1.4rem; font-weight: 700; color: #ffffff; margin: 0.4rem 0 0.3rem 0; }
    .ctl-sub { font-size: 0.9rem; color: #a8b8c8; margin-bottom: 1.2rem; line-height: 1.4; }
    </style>
"""

def render_tester_cantilever_leaf():
    st.markdown(LAB_TESTER_CSS, unsafe_allow_html=True)
    st.markdown('<div class="ctl-topbar"><div class="ctl-wordmark">SDSe LAB</div><div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="ctl-header">Cantilever Leaf — Universal Boundary Engine</div>', unsafe_allow_html=True)
    
    # Number Inputs
    st.markdown("### Leaf Geometry Inputs")
    col1, col2, col3 = st.columns(3)
    with col1:
        col_h = st.number_input("Column Height (m)", value=6.0, step=0.5, format="%.2f")
        outreach = st.number_input("Outreach (m)", value=5.0, step=0.5, format="%.2f")
        half_w = st.number_input("Middle Half-Width (m)", value=2.0, step=0.5, format="%.2f")
    with col2:
        tilt = st.number_input("Rib Tilt (deg)", value=0.0, step=1.0, format="%.1f")
        arc_r = st.number_input("Arc Radius (m)", value=1.0, step=0.1, format="%.2f")
    with col3:
        strut_j = st.number_input("Strut Joint (m)", value=3.0, step=0.5, format="%.2f")
        strut_a = st.number_input("Strut Angle (deg)", value=42.0, step=1.0, format="%.1f")
        n_ribs = st.number_input("Rib Pairs", value=3, step=1)

    st.markdown("### Pretension Forces (kN)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        mem_q = st.number_input("Membrane Pretension (kN)", value=2.0, step=0.5, format="%.2f")
    with col_t2:
        cab_q = st.number_input("Cable Pretension (kN)", value=5.0, step=0.5, format="%.2f")

    geom = compute_lab_leaf_geometry(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
    
    col_l, col_r = st.columns([2, 1])
    plot_placeholder = col_l.empty()

    with plot_placeholder:
        st.plotly_chart(build_cantilever_leaf_lab_figure(geom), use_container_width=True, config={"displayModeBar": False})

    with col_r:
        st.markdown("### Structural Auto-Sizing")
        if st.button("Run Universal Mesh & Size Steel", type="primary", use_container_width=True):
            
            with st.spinner("1. Constructing Boundary Loop..."):
                # 1. Build the master boundary loop (just the anchor points)
                pts = []
                
                # Start at Beam Tip
                b_tip = np.array([geom["beam"]["x"][-1], geom["beam"]["y"][-1], geom["beam"]["z"][-1]])
                pts.append(b_tip)
                
                # Left side (Tip -> Root)
                for rib in reversed(geom["ribs"]):
                    pts.append(np.array(rib["left_tip"]))
                
                # Root (Column joint)
                root_pt = np.array([0.0, 0.0, col_h])
                pts.append(root_pt)
                
                # Right side (Root -> Tip)
                for rib in geom["ribs"]:
                    pts.append(np.array(rib["right_tip"]))
                
                # Now we subdivide the boundary to create a smooth mesh
                subdiv_boundary = []
                anchor_indices = []
                edge_types = []
                
                for i in range(len(pts)):
                    a = pts[i]
                    b = pts[(i + 1) % len(pts)]
                    
                    # Allocate 4 sub-nodes per segment
                    n_sub = 4
                    for k in range(n_sub):
                        t = k / float(n_sub)
                        subdiv_boundary.append(a + (b - a) * t)
                    
                    # Record the start index of the segment as an anchor
                    anchor_indices.append(len(subdiv_boundary) - n_sub)
                    edge_types.append("cable")
                
                # Add the final closure point
                subdiv_boundary.append(pts[0])
                
                boundary_array = np.array(subdiv_boundary)
                
                # Since we passed anchor_indices and edge_types as lists of the segment starts,
                # we need to map them correctly. The builder expects anchor_indices to point to 
                # specific node indices in the boundary array.
                # We will pass every node as an "anchor" but only the start of each segment as "cable" start.
                # Actually, looking at the builder, it wants the indices of the nodes that separate edge types.
                # Let's pass all nodes as anchors, and set the edge type for each segment.
                full_anchor_indices = list(range(len(boundary_array)))
                full_edge_types = []
                for i in range(len(pts)):
                    for k in range(4):
                        full_edge_types.append("cable")
                full_edge_types.append("cable") # final closure

                # Wait, the builder requires `anchor_indices` and `edge_types` to be the same length.
                # It uses the indices in `anchor_indices` to look up coordinates in `boundary`.
                # We will pass the START of each segment.
                
                seg_starts = [i * 4 for i in range(len(pts))]
                
                # The builder logic for _boundary_as_four_sides wants to know the anchor points.
                # To make it perfectly map to 4 sides, we will pass the 4 corners of the leaf.
                # Let's just use the actual builder logic. It's much smarter than us!
                
                # Pass the exact corners
                corners = [
                    0,                                   # Beam Tip
                    len(pts) // 2,                       # Root
                    len(pts) - 1,                        # Rightmost tip
                    0                                    # Back to start
                ]
                
                # Actually, let's keep it simple and feed it the raw boundary.
                # The builder will figure out the 4 sides based on the edge types.
                # We will pass the edge types for the segments between anchors.
                
                raw_anchors = list(range(len(pts)))
                raw_types = ["cable"] * len(pts)

            with st.spinner("2. Running Universal TFI Mesh + FDM..."):
                # Use the universal builder with the raw anchor loop
                res = build_and_solve(
                    boundary=np.array(pts),
                    anchor_indices=raw_anchors,
                    edge_types=raw_types,
                    nx=21, ny=21,
                    membrane_q=mem_q * 1000.0,
                    cable_q=cab_q * 1000.0,
                )
                coords = res["coordinates"]
                mesh = res["mesh"]
                reactions_N = res["solve_result"]["reactions"] * 1000.0

            with st.spinner("3. Drawing the Bowed Shape..."):
                fig = go.Figure()
                
                # Draw the settled membrane surface
                X_settled = coords[:, 0].reshape((21, 21))
                Y_settled = coords[:, 1].reshape((21, 21))
                Z_settled = coords[:, 2].reshape((21, 21))
                
                fig.add_trace(go.Surface(
                    x=X_settled, y=Y_settled, z=Z_settled,
                    colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]],
                    opacity=0.5, showscale=False, hoverinfo="skip"
                ))

                # Draw the rigid steel frame
                b = geom["beam"]
                fig.add_trace(go.Scatter3d(x=b["x"], y=b["y"], z=b["z"], mode="lines", line=dict(color="#FF6B6B", width=8), name="Main beam"))
                fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0,col_h], mode="lines", line=dict(color="#2ecc71", width=10), name="Column"))
                for rib in geom["ribs"]:
                    ax, ay, az = rib["attach"]
                    lx, ly, lz = rib["left_tip"]
                    rx, ry, rz = rib["right_tip"]
                    fig.add_trace(go.Scatter3d(x=[lx, ax, rx], y=[ly, ay, ry], z=[lz, az, rz], mode="lines", line=dict(color="#3498db", width=3), showlegend=False))

                with plot_placeholder:
                    st.plotly_chart(apply_common_layout(fig, col_h), use_container_width=True, config={"displayModeBar": False})

            with st.spinner("4. Transferring Loads & Auto-Sizing..."):
                frame_data = build_cantilever_frame(col_h, outreach, half_w, tilt, arc_r, strut_j, strut_a, n_ribs)
                
                applied_loads = {}
                steel_nodes = frame_data["nodes"]
                
                fixed_nodes = mesh["fixed_indices"]
                for idx in fixed_nodes:
                    mem_pos = coords[idx]
                    dists = np.linalg.norm(steel_nodes - mem_pos, axis=1)
                    s_idx = np.argmin(dists)
                    
                    force = -reactions_N[idx]
                    if s_idx not in applied_loads:
                        applied_loads[s_idx] = np.zeros(3)
                    applied_loads[s_idx] += force

                result = analyze_and_size_frame(frame_data, applied_loads, grade="S355", family="CHS")
                
                if "error" in result:
                    st.error(f"Sizing Failed: {result['error']}")
                else:
                    st.success(f"Sizing Converged in {result.get('iterations', '?')} iterations!")
                    st.markdown("#### Selected Sections:")
                    for kind, sec in result["sections"].items():
                        st.write(f"- **{kind.capitalize()}**: `{sec}`")
                    st.markdown("#### Utilization:")
                    for kind, util in result["details"].items():
                        color = "#ff4b4b" if util > 0.85 else "#00cc66"
                        st.markdown(f"- **{kind.capitalize()}**: <span style='color:{color}'>{util*100:.1f}%</span>", unsafe_allow_html=True)

    if st.button("Back to Lab", key="tcl_back", use_container_width=True):
        st.session_state.page = "lab"
        st.rerun()
