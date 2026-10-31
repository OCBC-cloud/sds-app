# =============================================================================
# SDSe Fluid Design Studio - Pyodide Integrator Wrapper
# =============================================================================
# This file connects Streamlit to the local HTML/JS component that runs
# Pyodide (Python in WebAssembly) on the user's iPhone.
# =============================================================================

import os
import streamlit.components.v1 as components

# Get the absolute path to the directory containing this file
_DIR = os.path.dirname(os.path.abspath(__file__))

# Declare the component to Streamlit
_component_func = components.declare_component(
    "pyodide_integrator",
    path=_DIR
)

def calculate_forces_on_phone(coords, triangles, boundary_nodes, warp_pre, weft_pre, key=None):
    """
    Sends the mesh data to the browser, runs the FEA math on the iPhone,
    and returns the nodal forces.
    """
    # Convert numpy arrays to lists so they can be serialized to JSON
    coords_list = coords.tolist() if hasattr(coords, "tolist") else coords
    tris_list = triangles.tolist() if hasattr(triangles, "tolist") else triangles
    boundary_list = list(boundary_nodes)

    # Call the HTML component
    return _component_func(
        coords=coords_list,
        tris=tris_list,
        boundary_nodes=boundary_list,
        warp_pre=float(warp_pre),
        weft_pre=float(weft_pre),
        key=key,
        default=None
    )
