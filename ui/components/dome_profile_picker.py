# =============================================================================
# SDSe - Dome Profile Picker (Canvas Edition)
# =============================================================================
# A true 2D drawing board for the Dome Multi-Cone structure.
#
# Built on Streamlit's custom component protocol. The board is an HTML5
# canvas inside an iframe. The user drags five gold control points with
# their finger. The curve updates in real time. On release, the five
# new heights are sent back to Python via Streamlit.setComponentValue.
#
# No sliders. No widgets. A real CAD-style drawing board.
#
# The 5-point profile represents the frame elevation curve:
#   P0 - Left base (at -span/2)
#   P1 - Left quarter
#   P2 - Apex (at 0)
#   P3 - Right quarter
#   P4 - Right base (at +span/2)
#
# Heights are stored in session state under
#   ws_dm_custom_profile   (list of 5 floats, metres)
#
# History:
#   2026-10-18 - Replaced 5-slider version with HTML5 canvas.
# =============================================================================

import json

import streamlit as st
import streamlit.components.v1 as components


PROFILE_KEY = "ws_dm_custom_profile"
_DEFAULT_PROFILE = [0.0, 6.75, 9.0, 6.75, 0.0]


# =============================================================================
# SESSION STATE HELPERS
# =============================================================================

def _get_profile():
    profile = st.session_state.get(PROFILE_KEY, None)
    if profile is None or len(profile) != 5:
        profile = list(_DEFAULT_PROFILE)
        st.session_state[PROFILE_KEY] = profile
    return list(profile)


def _get_dome_inputs():
    diameter = float(st.session_state.get("ws_dm_dome_diameter", 18.0))
    crown = float(st.session_state.get("ws_dm_crown_height", 9.0))
    return diameter, crown


# =============================================================================
# THE CANVAS HTML
# =============================================================================

def _build_canvas_html(profile, diameter, crown):
    """
    Build the HTML + JS + CSS for the drawing board.
    The JS:
      - Draws the grid, reference parabola, custom curve, and 5 points.
      - Listens for touch and mouse drag on the points.
      - Sends the 5 heights back via Streamlit.setComponentValue.
    """
    span = float(max(diameter, 1.0))
    h_max = float(max(crown, 1.0))
    profile_json = json.dumps([float(v) for v in profile])

    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  html, body {{
    margin: 0; padding: 0;
    background: transparent;
    color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow: hidden;
  }}
  #board {{
    position: relative;
    width: 100%;
    height: 320px;
    background: #0e1117;
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 8px;
    touch-action: none;
    user-select: none;
  }}
  canvas {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    display: block;
    cursor: grab;
  }}
  canvas.dragging {{
    cursor: grabbing;
  }}
  #hint {{
    position: absolute;
    bottom: 8px;
    left: 8px;
    font-size: 11px;
    color: rgba(255,255,255,0.55);
    pointer-events: none;
  }}
</style>
</head>
<body>
<div id="board">
  <canvas id="cv"></canvas>
  <div id="hint">Drag the gold points to shape the curve.</div>
</div>

<script>
(function() {{
  const board = document.getElementById("board");
  const cv = document.getElementById("cv");
  const ctx = cv.getContext("2d");

  // ---------- Geometry constants ----------
  const SPAN = {span};
  const H_MAX = {h_max};
  const PROFILE = {profile_json};

  // ---------- Layout ----------
  // Canvas padding inside the board: left, right, top, bottom
  const PAD = {{ left: 40, right: 20, top: 20, bottom: 30 }};

  let cssW = 0, cssH = 0, dpr = window.devicePixelRatio || 1;

  function resize() {{
    const rect = board.getBoundingClientRect();
    cssW = rect.width;
    cssH = rect.height;
    cv.width = Math.floor(cssW * dpr);
    cv.height = Math.floor(cssH * dpr);
    cv.style.width = cssW + "px";
    cv.style.height = cssH + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }}

  // Convert world (x from -SPAN/2 to +SPAN/2, z from 0 to H_MAX) to
  // canvas pixel coords.
  function wx(x) {{
    const innerW = cssW - PAD.left - PAD.right;
    const u = (x + SPAN / 2) / SPAN;
    return PAD.left + u * innerW;
  }}
  function wy(z) {{
    const innerH = cssH - PAD.top - PAD.bottom;
    const v = z / Math.max(H_MAX, 1e-9);
    return PAD.top + (1 - v) * innerH;
  }}
  function px2x(px) {{
    const innerW = cssW - PAD.left - PAD.right;
    const u = (px - PAD.left) / innerW;
    return u * SPAN - SPAN / 2;
  }}
  function py2z(py) {{
    const innerH = cssH - PAD.top - PAD.bottom;
    const v = (py - PAD.top) / innerH;
    return (1 - v) * H_MAX;
  }}

  // ---------- Control points in world coords ----------
  // xs are fixed; zs are the profile.
  function makePoints(profile) {{
    const xs = [-SPAN/2, -SPAN/4, 0, SPAN/4, SPAN/2];
    return xs.map((x, i) => ({{ x: x, z: profile[i] }}));
  }}
  let pts = makePoints(PROFILE);

  // ---------- Draw ----------
  function draw() {{
    ctx.clearRect(0, 0, cssW, cssH);

    // Grid lines
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.lineWidth = 1;
    const nGrid = 6;
    for (let i = 0; i <= nGrid; i++) {{
      const px = PAD.left + (i / nGrid) * (cssW - PAD.left - PAD.right);
      ctx.beginPath();
      ctx.moveTo(px, PAD.top);
      ctx.lineTo(px, cssH - PAD.bottom);
      ctx.stroke();
    }}
    for (let i = 0; i <= nGrid; i++) {{
      const py = PAD.top + (i / nGrid) * (cssH - PAD.top - PAD.bottom);
      ctx.beginPath();
      ctx.moveTo(PAD.left, py);
      ctx.lineTo(cssW - PAD.right, py);
      ctx.stroke();
    }}

    // Reference parabola (faint)
    ctx.strokeStyle = "rgba(255,255,255,0.25)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 6]);
    ctx.beginPath();
    const N = 100;
    for (let i = 0; i <= N; i++) {{
      const u = i / N;
      const x = -SPAN/2 + u * SPAN;
      const r = Math.abs(x) / (SPAN / 2);
      const z = H_MAX * (1 - r * r);
      const cx = wx(x), cy = wy(z);
      if (i === 0) ctx.moveTo(cx, cy); else ctx.lineTo(cx, cy);
    }}
    ctx.stroke();
    ctx.setLineDash([]);

    // Custom curve
    ctx.strokeStyle = "#ffd166";
    ctx.lineWidth = 4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    for (let i = 0; i <= N; i++) {{
      const u = i / N;
      const x = -SPAN/2 + u * SPAN;
      const z = interp(x, pts);
      const cx = wx(x), cy = wy(z);
      if (i === 0) ctx.moveTo(cx, cy); else ctx.lineTo(cx, cy);
    }}
    ctx.stroke();

    // Control points
    for (const p of pts) {{
      const cx = wx(p.x), cy = wy(p.z);
      ctx.beginPath();
      ctx.arc(cx, cy, 12, 0, 2 * Math.PI);
      ctx.fillStyle = "rgba(255, 209, 102, 0.25)";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
      ctx.fillStyle = "#ffd166";
      ctx.fill();
      ctx.strokeStyle = "#0e1117";
      ctx.lineWidth = 2;
      ctx.stroke();
    }}

    // Axes labels
    ctx.fillStyle = "rgba(255,255,255,0.5)";
    ctx.font = "11px -apple-system, sans-serif";
    ctx.textAlign = "right";
    ctx.fillText("0", PAD.left - 6, cssH - PAD.bottom);
    ctx.fillText("H=" + H_MAX.toFixed(1), PAD.left - 6, PAD.top + 10);
    ctx.textAlign = "center";
    ctx.fillText("-" + (SPAN/2).toFixed(1), PAD.left, cssH - PAD.bottom + 16);
    ctx.fillText("+" + (SPAN/2).toFixed(1), cssW - PAD.right, cssH - PAD.bottom + 16);
    ctx.textAlign = "left";
    ctx.fillText("Elevation (m)", PAD.left, PAD.top - 6);
  }}

  // Interpolation for drawing the curve (matches Python's np.interp
  // behaviour, but with 5 control points).
  function interp(x, points) {{
    // points are ordered left to right by x.
    if (x <= points[0].x) return points[0].z;
    if (x >= points[points.length - 1].x) return points[points.length - 1].z;
    for (let i = 0; i < points.length - 1; i++) {{
      const a = points[i], b = points[i + 1];
      if (x >= a.x && x <= b.x) {{
        const t = (x - a.x) / (b.x - a.x || 1e-9);
        return a.z + t * (b.z - a.z);
      }}
    }}
    return 0;
  }}

  // ---------- Drag handling ----------
  let draggingIdx = -1;

  function hitTest(px, py) {{
    for (let i = 0; i < pts.length; i++) {{
      const cx = wx(pts[i].x), cy = wy(pts[i].z);
      const d = Math.hypot(px - cx, py - cy);
      if (d < 22) return i;
    }}
    return -1;
  }}

  function pointerPos(evt) {{
    const rect = cv.getBoundingClientRect();
    let cx, cy;
    if (evt.touches && evt.touches.length > 0) {{
      cx = evt.touches[0].clientX - rect.left;
      cy = evt.touches[0].clientY - rect.top;
    }} else {{
      cx = evt.clientX - rect.left;
      cy = evt.clientY - rect.top;
    }}
    return {{ px: cx, py: cy }};
  }}

  function onDown(evt) {{
    const {{ px, py }} = pointerPos(evt);
    const idx = hitTest(px, py);
    if (idx >= 0) {{
      draggingIdx = idx;
      cv.classList.add("dragging");
      evt.preventDefault();
    }}
  }}

  function onMove(evt) {{
    if (draggingIdx < 0) return;
    const {{ px, py }} = pointerPos(evt);
    // Convert to world z. Only the z moves; x is fixed.
    let z = py2z(py);
    z = Math.max(0, Math.min(H_MAX * 1.2, z));
    pts[draggingIdx].z = z;
    draw();
    evt.preventDefault();
  }}

  function onUp(evt) {{
    if (draggingIdx < 0) return;
    cv.classList.remove("dragging");
    draggingIdx = -1;
    // Send the new profile to Streamlit.
    const profile = pts.map(p => p.z);
    sendToStreamlit(profile);
    evt.preventDefault();
  }}

  // ---------- Streamlit component protocol ----------
  function sendToStreamlit(profile) {{
    if (window.Streamlit && window.Streamlit.setComponentValue) {{
      window.Streamlit.setComponentValue({{ profile: profile }});
    }}
  }}

  // ---------- Event listeners ----------
  cv.addEventListener("mousedown", onDown);
  cv.addEventListener("mousemove", onMove);
  window.addEventListener("mouseup", onUp);
  cv.addEventListener("touchstart", onDown, {{ passive: false }});
  cv.addEventListener("touchmove", onMove, {{ passive: false }});
  window.addEventListener("touchend", onUp, {{ passive: false }});

  // ---------- Init ----------
  window.addEventListener("resize", resize);
  resize();

  // Notify Streamlit the component is ready.
  if (window.Streamlit && window.Streamlit.setFrameHeight) {{
    window.Streamlit.setFrameHeight(340);
  }}
}})();
</script>
</body>
</html>
"""
    return html


# =============================================================================
# PUBLIC RENDERER
# =============================================================================

def render_dome_profile_picker():
    """
    Render the Dome Multi-Cone Profile Picker board (canvas version).

    Reads:
        ws_dm_dome_diameter
        ws_dm_crown_height
        ws_dm_custom_profile

    Writes:
        ws_dm_custom_profile (5 floats)
    """
    diameter, crown = _get_dome_inputs()
    profile = _get_profile()

    st.markdown(
        "<p style='color:#a8b8c8;margin-top:0;'>"
        "Draw the dome elevation curve. Drag the gold points. "
        "The 3D board rebuilds the frame from this curve."
        "</p>",
        unsafe_allow_html=True,
    )

    html = _build_canvas_html(profile, diameter, crown)

    # Render the component. The key ensures the widget is stable across
    # reruns; a new value is only returned when the user releases a point.
    result = components.html(
        html,
        height=340,
        scrolling=False,
    )

    # Read the value returned by the JS.
    # components.html returns the value passed to Streamlit.setComponentValue
    # on the last drag release, or None on a fresh render.
    if result is not None and isinstance(result, dict):
        new_profile = result.get("profile", None)
        if new_profile is not None and len(new_profile) == 5:
            try:
                new_profile = [float(v) for v in new_profile]
                st.session_state[PROFILE_KEY] = new_profile
            except (TypeError, ValueError):
                pass

    # --- Reset button ---
    st.markdown("---")
    if st.button("Reset to Parabolic", use_container_width=True):
        st.session_state[PROFILE_KEY] = list(_DEFAULT_PROFILE)
        st.rerun()


# =============================================================================
# END OF ui/components/dome_profile_picker.py
# =============================================================================
