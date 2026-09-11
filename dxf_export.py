# =============================================================================
# SDSe - DXF Export Module
# =============================================================================
# Exports FDS viewer geometry to a valid 3D DXF file for CAD software.
# Self-describing: embeds SDSe metadata in the DXF header so the file
# can be identified on re-import.
#
# Layers used:
#   COLUMN           - vertical column
#   BASEPLATE        - baseplate marker
#   MAIN_BEAM        - main curved beam
#   RIBS             - radial ribs (leaf) or secondary members
#   CABLE_PERIMETER  - perimeter cable segments
#   MEMBRANE         - membrane surface (3D faces)
#   STRUT            - curved strut
#   RING_CABLE       - ring cable (if opening present)
#   NODES            - key nodes (column node, leaf tip)
#
# Usage:
#   from dxf_export import build_dxf_from_leaf_session
#   dxf_bytes = build_dxf_from_leaf_session(st.session_state)
# =============================================================================

import io
import json
from datetime import datetime

import numpy as np

try:
    import ezdxf
    from ezdxf import units
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False


# =============================================================================
# LAYER NAMES (CONVENTION)
# =============================================================================

LAYER_COLUMN = "COLUMN"
LAYER_BASEPLATE = "BASEPLATE"
LAYER_MAIN_BEAM = "MAIN_BEAM"
LAYER_RIBS = "RIBS"
LAYER_CABLE = "CABLE_PERIMETER"
LAYER_MEMBRANE = "MEMBRANE"
LAYER_STRUT = "STRUT"
LAYER_RING = "RING_CABLE"
LAYER_NODES = "NODES"


# =============================================================================
# LAYER STYLE
# =============================================================================

LAYER_STYLES = {
    LAYER_COLUMN: {"color": 3},
    LAYER_BASEPLATE: {"color": 3},
    LAYER_MAIN_BEAM: {"color": 1},
    LAYER_RIBS: {"color": 5},
    LAYER_CABLE: {"color": 2},
    LAYER_MEMBRANE: {"color": 4},
    LAYER_STRUT: {"color": 30},
    LAYER_RING: {"color": 2},
    LAYER_NODES: {"color": 2},
}


# =============================================================================
# GEOMETRY BUILDER
# =============================================================================

def _build_leaf_geometry(state):
    """Rebuild the leaf geometry from session state."""
    col_h = state.get("leaf_column_height", 6.0)
    outreach = state.get("leaf_outreach", 8.0)
    ribs_per_side = int(state.get("leaf_ribs_per_side", 5))
    rib_tilt_deg = state.get("leaf_rib_tilt_deg", 20.0)
    arc_r = state.get("leaf_beam_arc_radius", 5.0)
    sag_pct = state.get("leaf_membrane_sag_pct", 15.0) / 100.0

    n_beam = 80
    t_beam = np.linspace(0, 1, n_beam)
    beam_x = outreach * t_beam
    beam_z = col_h + arc_r * np.sin(t_beam * np.pi * 0.6) * 0.7
    beam_y = np.zeros_like(t_beam)

    def leaf_half_width(t):
        return outreach * 0.42 * (np.sin(np.pi * t) ** 0.7)

    def rib_tilt_at(t):
        return np.radians(rib_tilt_deg) * (np.sin(np.pi * t) ** 0.7)

    rib_ts = np.linspace(0.08, 0.92, ribs_per_side)
    ribs_left = []
    ribs_right = []
    rib_tips_left = []
    rib_tips_right = []

    for t in rib_ts:
        idx = int(t * (n_beam - 1))
        a_x = beam_x[idx]
        a_y = beam_y[idx]
        a_z = beam_z[idx]
        half_w = leaf_half_width(t)
        tilt = rib_tilt_at(t)
        tip_z = a_z + half_w * np.tan(tilt)

        ribs_left.append(((a_x, a_y, a_z), (a_x, -half_w, tip_z)))
        ribs_right.append(((a_x, a_y, a_z), (a_x, +half_w, tip_z)))
        rib_tips_left.append((a_x, -half_w, tip_z))
        rib_tips_right.append((a_x, +half_w, tip_z))

    n_u = 30
    n_v = 30
    X_surf = np.zeros((n_u, n_v))
    Y_surf = np.zeros((n_u, n_v))
    Z_surf = np.zeros((n_u, n_v))

    for i, t in enumerate(np.linspace(0.02, 0.98, n_u)):
        idx = int(t * (n_beam - 1))
        b_x = beam_x[idx]
        b_z = beam_z[idx]
        half_w = leaf_half_width(t)
        tilt = rib_tilt_at(t)
        tip_z_at_t = b_z + half_w * np.tan(tilt)
        for j, v in enumerate(np.linspace(-1, 1, n_v)):
            X_surf[i, j] = b_x
            Y_surf[i, j] = v * half_w
            z_edge = b_z * (1 - abs(v)) + tip_z_at_t * abs(v)
            sag_amount = sag_pct * half_w * (1 - (2 * abs(v) - 1) ** 2)
            Z_surf[i, j] = z_edge - sag_amount

    idx_third = int(0.33 * (n_beam - 1))
    px = beam_x[idx_third]
    py = beam_y[idx_third]
    pz = beam_z[idx_third]
    t_s = np.linspace(0, 1, 25)
    strut_x = px * (1 - t_s)
    strut_y = py * (1 - t_s)
    strut_z = pz + (col_h * 0.4 - pz) * t_s + 0.5 * np.sin(np.pi * t_s) * (col_h * 0.15)

    return {
        "column": ((0, 0, 0), (0, 0, col_h)),
        "baseplate": (0, 0, 0),
        "main_beam": list(zip(beam_x.tolist(), beam_y.tolist(), beam_z.tolist())),
        "ribs_left": ribs_left,
        "ribs_right": ribs_right,
        "tips_left": rib_tips_left,
        "tips_right": rib_tips_right,
        "membrane": {
            "X": X_surf.tolist(),
            "Y": Y_surf.tolist(),
            "Z": Z_surf.tolist(),
        },
        "strut": list(zip(strut_x.tolist(), strut_y.tolist(), strut_z.tolist())),
        "column_node": (0, 0, col_h),
        "leaf_tip": (float(outreach), 0.0, float(beam_z[-1])),
        "meta": {
            "structure": "leaf",
            "column_height": float(col_h),
            "outreach": float(outreach),
            "ribs_per_side": int(ribs_per_side),
            "rib_tilt_deg": float(rib_tilt_deg),
            "arc_radius": float(arc_r),
            "membrane_sag_pct": float(sag_pct * 100.0),
        },
    }


# =============================================================================
# DXF HELPERS
# =============================================================================

def _setup_layers(doc):
    """Create the SDSe layer set."""
    for layer_name, style in LAYER_STYLES.items():
        if layer_name not in doc.layers:
            layer = doc.layers.add(layer_name)
            layer.color = style["color"]


def _add_line(msp, layer, p1, p2):
    """Add a 3D line."""
    msp.add_line(p1, p2, dxfattribs={"layer": layer})


def _add_polyline_3d(msp, layer, points):
    """Add a 3D polyline."""
    if len(points) < 2:
        return
    msp.add_polyline3d(points, dxfattribs={"layer": layer})


def _add_point(msp, layer, p):
    """Add a 3D point marker."""
    msp.add_point(p, dxfattribs={"layer": layer})


def _add_3dface(msp, layer, p1, p2, p3, p4):
    """
    Add a single 3D face. Uses the ezdxf 3DFACE entity via low-level
    new_entity call to avoid signature conflicts across ezdxf versions.
    """
    try:
        face = msp.add_3dface([p1, p2, p3, p4], dxfattribs={"layer": layer})
    except TypeError:
        # Fallback: build the 3DFACE entity via new_entity
        from ezdxf.entities import Face3d
        face = Face3d.new(
            dxfattribs={
                "layer": layer,
                "vtx0": p1,
                "vtx1": p2,
                "vtx2": p3,
                "vtx3": p4,
            }
        )
        msp.add_entity(face)


def _add_mesh(msp, layer, X, Y, Z):
    """Add 3D faces for each grid cell of the membrane surface."""
    n_u = len(X)
    n_v = len(X[0])

    for i in range(n_u - 1):
        for j in range(n_v - 1):
            p00 = (X[i][j], Y[i][j], Z[i][j])
            p01 = (X[i][j + 1], Y[i][j + 1], Z[i][j + 1])
            p10 = (X[i + 1][j], Y[i + 1][j], Z[i + 1][j])
            p11 = (X[i + 1][j + 1], Y[i + 1][j + 1], Z[i + 1][j + 1])
            _add_3dface(msp, layer, p00, p01, p11, p10)


def _embed_metadata(doc, meta):
    """Write SDSe metadata into the DXF header."""
    try:
        doc.header["$PROJECTNAME"] = "SDSe"
        doc.header["$LASTSAVEDBY"] = "SDSe"
    except Exception:
        pass

    meta_json = json.dumps(meta, default=str)
    try:
        doc.header.custom_vars.append("SDSE_META", meta_json[:250])
    except Exception:
        pass


# =============================================================================
# MAIN EXPORT FUNCTION
# =============================================================================

def build_dxf_from_leaf_session(state):
    """
    Build a DXF from the current leaf session state.
    Returns DXF file bytes ready for download.
    """
    if not EZDXF_AVAILABLE:
        raise RuntimeError("ezdxf is not installed. Add 'ezdxf' to requirements.txt.")

    geo = _build_leaf_geometry(state)

    doc = ezdxf.new(setup=True)
    doc.units = units.M
    _setup_layers(doc)

    msp = doc.modelspace()

    # Column
    if state.get("leaf_show_column", True):
        _add_line(msp, LAYER_COLUMN, geo["column"][0], geo["column"][1])
        _add_point(msp, LAYER_BASEPLATE, geo["baseplate"])

    # Main beam
    _add_polyline_3d(msp, LAYER_MAIN_BEAM, geo["main_beam"])

    # Ribs
    if state.get("leaf_show_ribs", True):
        for p1, p2 in geo["ribs_left"] + geo["ribs_right"]:
            _add_line(msp, LAYER_RIBS, p1, p2)

    # Perimeter cables
    if state.get("leaf_show_cables", True):
        _add_polyline_3d(msp, LAYER_CABLE, geo["tips_left"])
        _add_polyline_3d(msp, LAYER_CABLE, geo["tips_right"])

    # Membrane
    if state.get("leaf_show_membrane", True):
        _add_mesh(msp, LAYER_MEMBRANE,
                  geo["membrane"]["X"], geo["membrane"]["Y"], geo["membrane"]["Z"])

    # Strut
    if state.get("leaf_show_strut", True):
        _add_polyline_3d(msp, LAYER_STRUT, geo["strut"])

    # Nodes
    _add_point(msp, LAYER_NODES, geo["column_node"])
    _add_point(msp, LAYER_NODES, geo["leaf_tip"])

    # Metadata
    _embed_metadata(doc, geo["meta"])

    # Write to memory
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


def get_dxf_filename(prefix="sdse_leaf"):
    """Return a dated filename for the exported DXF."""
    today = datetime.now().strftime("%Y-%m-%d")
    return prefix + "_" + today + ".dxf"
