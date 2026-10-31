# =============================================================================
# SDSe Fluid Design Studio - Pyodide Integrator Wrapper
# =============================================================================
# Connects Streamlit to the iPhone's browser to run the heavy Matrix Solver.
# =============================================================================

import os
import streamlit.components.v1 as components

_DIR = os.path.dirname(os.path.abspath(__file__))

_component_func = components.declare_component(
    "pyodide_integrator",
    path=_DIR
)

def solve_matrix_on_phone(topology, loads, sections, grade, key=None):
    """
    Sends the 3D topology and loads to the iPhone.
    Waits for the matrix solver to return the reactions and forces.
    """
    # Convert numpy arrays to lists so they can be serialized
    topology_serializable = {
        "nodes": topology["nodes"].tolist() if hasattr(topology["nodes"], "tolist") else topology["nodes"],
        "elements": topology["elements"],
        "fixed_indices": topology["fixed_indices"]
    }
    
    loads_serializable = loads.tolist() if hasattr(loads, "tolist") else loads
    
    sections_serializable = {}
    for k, v in sections.items():
        sections_serializable[k] = v

    return _component_func(
        topology=topology_serializable,
        loads=loads_serializable,
        sections=sections_serializable,
        grade=grade,
        key=key,
        default=None
    )
