import math
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import streamlit.components.v1 as components

from viewers.figures._shared import apply_common_layout


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
        "lab_picker_key": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def draw_pickerboard_html(reach, width, n_ribs, active_dots, picker_key):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body { margin: 0; background: #0e1117; font-family: sans-serif; color: #a8b8c8; }
      #container { width: 100%; max-width: 600px; aspect-ratio: 4/3; margin: auto; border: 1px solid #1e2a3a; border-radius: 8px; position: relative; }
      svg { width: 100%; height: 100%; display: block; touch-action: manipulation; }
      .grid { stroke: #a0522d; stroke-width: 1.5; stroke-dasharray: 4 4; opacity: 0.6; }
      .border { stroke: #2ecc71; stroke-width: 3; fill: none; }
      .pick { cursor: pointer; transition: fill 0.2s; }
      .pick.off { fill: #3a4a5a; stroke: #556677; stroke-width: 2; }
      .pick.on { fill: #f1c40f; stroke: #fff3b0; stroke-width: 2; }
      #caption { text-align: center; padding: 10px; font-size: 14px; }
      #caption b { color: #f1c40f; }
    </style>
    </head>
    <body>
    <div id="container">
      <div id="svg-container"></div>
    </div>
    <div id="caption">Picked positions: <b><span id="count">0</span></b></div>

    <script>
    var state = {
        reach: __REACH__,
        width: __WIDTH__,
        n_ribs: __N_RIBS__,
        active_dots: __ACTIVE_DOTS__
    };

    var SVG_NS = "http://www.w3.org/2000/svg";
    function el(tag, attrs) { var e = document.createElementNS(SVG_NS, tag); for (var k in attrs) { e.setAttribute(k, attrs[k]); } return e; }

    function render() {
      var container = document.getElementById("svg-container");
      container.innerHTML = "";
      
      var cw = container.clientWidth || 400;
      var ch = container.clientHeight || 300;
      var padding = 30;
      var maxX = state.reach * 1.1;
      var maxY = state.width * 0.6;
      
      var scale = Math.min((cw - padding*2) / maxX, (ch - padding*2) / (maxY*2));
      var ox = padding;
      var oy = ch / 2;

      var svg = el("svg", { viewBox: "0 0 " + cw + " " + ch });

      svg.appendChild(el("rect", { x: ox, y: oy - (maxY*scale), width: maxX*scale, height: maxY*2*scale, class: "border" }));
      svg.appendChild(el("line", { x1: ox, y1: oy, x2: ox + maxX*scale, y2: oy, class: "grid" }));

      function makeDot(x, y, id, square) {
        var on = state.active_dots.indexOf(id) !== -1;
        var cls = "pick " + (on ? "on" : "off");
        var shape = square ? el("rect", { x: x-6, y: y-6, width: 12, height: 12, class: cls }) : el("circle", { cx: x, cy: y, r: 7, class: cls });
        shape.addEventListener("click", function(e) { e.preventDefault(); toggle(id); });
        shape.addEventListener("touchend", function(e) { e.preventDefault(); toggle(id); });
        svg.appendChild(shape);
      }

      makeDot(ox, oy, "root", true);

      var rib_ts = [];
      if (state.n_ribs > 1) { for (var i=0; i<state.n_ribs; i++) rib_ts.push(0.08 + 0.84 * i / (state.n_ribs - 1)); }
      else { rib_ts.push(0.5); }

      for (var i=0; i<rib_ts.length; i++) {
        var t = rib_ts[i];
        var xp = t * maxX;
        var hw = maxY * Math.sin(Math.PI * t);
        var px = ox + xp * scale;
        var py_t = oy - hw * scale;
        var py_b = oy + hw * scale;
        
        svg.appendChild(el("line", { x1: px, y1: oy, x2: px, y2: py_t, class: "grid" }));
        svg.appendChild(el("line", { x1: px, y1: oy, x2: px, y2: py_b, class: "grid" }));
        
        makeDot(px, py_t, "top_" + i, false);
        makeDot(px, py_b, "bot_" + i, false);
      }

      makeDot(ox + maxX * scale, oy, "beam_tip", true);

      document.getElementById("count").textContent = state.active_dots.length;
      container.appendChild(svg);
    }

    function toggle(id) {
      var pos = state.active_dots.indexOf(id);
      if (pos !== -1) { state.active_dots.splice(pos, 1); } 
      else { state.active_dots.push(id); }
      render();
      var msg = { isStreamlitMessage: true, type: "streamlit:setComponentValue", value: { active_dots: state.active_dots }, dataType: "json" };
      window.parent.postMessage(msg, "*");
    }

    window.addEventListener("message", function(event) {
        if (!event.data || event.data.type !== "streamlit:render") return;
        if (event.data.args && event.data.args.active_dots) {
            state.active_dots = event.data.args.active_dots;
            render();
        }
    });

    window.addEventListener("resize", render);
    render();
    </script>
    </body>
    </html>
    """
    
    html = html_template.replace("__REACH__", str(reach))
    html = html.replace("__WIDTH__", str(width))
    html = html.replace("__N_RIBS__", str(n_ribs))
    html = html.replace("__ACTIVE_DOTS__", str(active_dots).replace("'", '"'))
    
    return html


def draw_3d_preview(beam_h, col_top_h, outreach, arc_r, vein_length, tilt_deg, n_ribs, boundary_loop=None):
    fig = go.Figure()

    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[0, col_top_h], mode="lines", line=dict(color="#2ecc71", width=10), name="Column"))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode="markers", marker=dict(color="#2ecc71", size=10, symbol="square"), name="Base"))

    n_beam = 80 
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_y = np.zeros_like(t_beam)
    beam_z = beam_h + (arc_r * 0.5) * 4.0 * t_beam * (1.0 - t_beam)
    
    fig.add_trace(go.Scatter3d(x=beam_x, y=beam_y, z=beam_z, mode="lines", line=dict(color="#FF6B6B", width=8), name="Midrib"))

    tie_attach_x = outreach / 3.0
    tie_attach_z = beam_h + (arc_r * 0.5) * 4.0 * (1.0/3.0) * (1.0 - 1.0/3.0)
    fig.add_trace(go.Scatter3d(x=[0, tie_attach_x], y=[0, 0], z=[col_top_h, tie_attach_z], mode="lines", line=dict(color="#f39c12", width=6), name="Tie Beam"))

    rib_ts = np.linspace(0.08, 0.92, n_ribs)
    for rt in rib_ts:
        idx = int(rt * (n_beam - 1))
        rx = beam_x[idx]
        rz = beam_z[idx]
        
        hw = vein_length * (math.sin(math.pi * rt) ** 0.7)
        tilt_rad = math.radians(tilt_deg) * (math.sin(math.pi * rt) ** 0.7)
        tip_z = rz + hw * math.tan(tilt_rad)
        
        fig.add_trace(go.Scatter3d(x=[rx, rx], y=[0, -hw], z=[rz, tip_z], mode="lines", line=dict(color="#3498db", width=3), showlegend=False))
        fig.add_trace(go.Scatter3d(x=[rx, rx], y=[0, hw], z=[rz, tip_z], mode="lines", line=dict(color="#3498db", width=3), showlegend=False))

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

    fig.add_trace(go.Surface(x=X_s, y=Y_s, z=Z_s, colorscale=[[0, "#1a2a5f"], [0.5, "#4a7a9c"], [1, "#6ab0d4"]], opacity=0.55, showscale=False, hoverinfo="skip"))

    if boundary_loop and len(boundary_loop) > 1:
        lx = [p[0] for p in boundary_loop]
        ly = [p[1] for p in boundary_loop]
        lz = [p[2] for p in boundary_loop]
        lx.append(boundary_loop[0][0])
        ly.append(boundary_loop[0][1])
        lz.append(boundary_loop[0][2])
        
        fig.add_trace(go.Scatter3d(x=lx, y=ly, z=lz, mode="lines", line=dict(color="#f1c40f", width=6), name="Perimeter Cable"))
        fig.add_trace(go.Scatter3d(x=[p[0] for p in boundary_loop], y=[p[1] for p in boundary_loop], z=[p[2] for p in boundary_loop], mode="markers", marker=dict(color="#f1c40f", size=6), name="Anchors"))

    return apply_common_layout(fig, col_top_h)


def _build_boundary_loop_from_dots(active_dots, n_ribs, outreach, arc_r, beam_h, col_top_h, vein_length, tilt):
    loop_pts = []
    for dot in active_dots:
        if dot == "root":
            loop_pts.append([0.0, 0.0, beam_h])
        elif dot == "beam_tip":
            bx = outreach
            bz = beam_h + (arc_r * 0.5) * 4.0 * 1.0 * (1.0 - 1.0)
            loop_pts.append([bx, 0.0, bz])
        elif dot.startswith("top_") or dot.startswith("bot_"):
            side = 1.0 if dot.startswith("top_") else -1.0
            rib_idx = int(dot.split("_")[1])
            if n_ribs > 1:
                rt = 0.08 + (0.92 - 0.08) * rib_idx / (n_ribs - 1)
            else:
                rt = 0.5
            
            bx = outreach * rt
            bz = beam_h + (arc_r * 0.5) * 4.0 * rt * (1.0 - rt)
            hw = vein_length * (math.sin(math.pi * rt) ** 0.7)
            tilt_rad = math.radians(tilt) * (math.sin(math.pi * rt) ** 0.7)
            tip_z = bz + hw * math.tan(tilt_rad)
            
            loop_pts.append([bx, side * hw, tip_z])
    return loop_pts


def render_tester_cantilever_leaf():
    _init_lab_defaults()
    
    step = st.session_state["lab_step"]
    progress = (step - 1) / 6.0
    st.progress(progress)
    st.markdown("<br>", unsafe_allow_html=True)

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

    elif step == 6:
        st.markdown("### Step 6: Pick Boundary Anchors")
        st.info("Tap the dots on the 2D plan. The 3D view below updates live.")
        
        # 1. Draw the 2D Pickerboard
        html_code = draw_pickerboard_html(
            reach=float(st.session_state["ws_sl_outreach"]),
            width=float(st.session_state["lab_vein_length"]),
            n_ribs=int(st.session_state["ws_sl_ribs_per_side"]),
            active_dots=st.session_state["lab_active_dots"],
            picker_key=st.session_state["lab_picker_key"]
        )
        components.html(html_code, height=400)
        
        # 2. Build boundary loop from current picks
        active_dots = st.session_state.get("lab_active_dots", [])
        boundary_loop = _build_boundary_loop_from_dots(
            active_dots=active_dots,
            n_ribs=st.session_state["ws_sl_ribs_per_side"],
            outreach=st.session_state["ws_sl_outreach"],
            arc_r=st.session_state["ws_sl_arc_radius"],
            beam_h=st.session_state["ws_sl_beam_landing_height"],
            col_top_h=st.session_state["ws_sl_column_top_height"],
            vein_length=st.session_state["lab_vein_length"],
            tilt=st.session_state["ws_sl_rib_tilt"]
        )
        
        # 3. Draw the 3D Viewer below
        fig_3d = draw_3d_preview(
            beam_h=st.session_state["ws_sl_beam_landing_height"],
            col_top_h=st.session_state["ws_sl_column_top_height"],
            outreach=st.session_state["ws_sl_outreach"],
            arc_r=st.session_state["ws_sl_arc_radius"],
            vein_length=st.session_state["lab_vein_length"],
            tilt_deg=st.session_state["ws_sl_rib_tilt"],
            n_ribs=st.session_state["ws_sl_ribs_per_side"],
            boundary_loop=boundary_loop
        )
        st.plotly_chart(fig_3d, use_container_width=True, config={"displayModeBar": False})
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Removed Clear Picks. Only Review and Back remain.
        col_a, col_b = st.columns(2)
        if col_a.button("⬅ Back", use_container_width=True):
            st.session_state["lab_step"] = 5
            st.rerun()
        if col_b.button("Review Structure ➔", type="primary", use_container_width=True):
            st.session_state["lab_step"] = 7
            st.rerun()

    elif step == 7:
        st.markdown("### Step 7: Review & Analyze")
        
        active_dots = st.session_state.get("lab_active_dots", [])
        
        boundary_loop = _build_boundary_loop_from_dots(
            active_dots=active_dots,
            n_ribs=st.session_state["ws_sl_ribs_per_side"],
            outreach=st.session_state["ws_sl_outreach"],
            arc_r=st.session_state["ws_sl_arc_radius"],
            beam_h=st.session_state["ws_sl_beam_landing_height"],
            col_top_h=st.session_state["ws_sl_column_top_height"],
            vein_length=st.session_state["lab_vein_length"],
            tilt=st.session_state["ws_sl_rib_tilt"]
        )
        
        fig_3d = draw_3d_preview(
            beam_h=st.session_state["ws_sl_beam_landing_height"],
            col_top_h=st.session_state["ws_sl_column_top_height"],
            outreach=st.session_state["ws_sl_outreach"],
            arc_r=st.session_state["ws_sl_arc_radius"],
            vein_length=st.session_state["lab_vein_length"],
            tilt_deg=st.session_state["ws_sl_rib_tilt"],
            n_ribs=st.session_state["ws_sl_ribs_per_side"],
            boundary_loop=boundary_loop
        )
        st.plotly_chart(fig_3d, use_container_width=True, config={"displayModeBar": False})

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Analyze & Size Steel", type="primary", use_container_width=True):
            st.success("Solvers not connected yet. This is where the FDM and Steel Sizing will run!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ Back to Pickerboard", use_container_width=True):
            st.session_state["lab_step"] = 6
            st.rerun()

    st.markdown("---")
    if st.button("Exit to Lab", key="lab_exit", use_container_width=True):
        st.session_state["lab_step"] = 1
        st.session_state.page = "lab"
        st.rerun()
