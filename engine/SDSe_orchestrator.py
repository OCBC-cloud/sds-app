# =============================================================================
# SDSe Engine - Structural Orchestrator (Forces Only - No Sizing)
# =============================================================================

import numpy as np
from engine.SDSe_frame_topology import build_frame_topology
from engine.SDSe_loads import calculate_uls_loads
from data.materials import FABRIC_PROPERTIES

def run_structural_analysis(data):
    """
    Calculates the true forces. Does not size steel. Does not stop.
    """
    topology = build_frame_topology(data)
    
    fabric_type = data.get("fabric_type", "PVDF")
    fabric_grade = data.get("fabric_grade", "Ferrari 702")
    material_data = FABRIC_PROPERTIES.get(fabric_type, {}).get(fabric_grade, FABRIC_PROPERTIES["PVDF"]["Ferrari 702"])
    
    # Calculate the loads
    loads_dict = calculate_uls_loads(topology, data, material_data)
    
    # We return the raw forces. No sizing. No stopping.
    return {
        "status": "SUCCESS",
        "surface_area": loads_dict["surface_area"],
        "total_wind_uplift_N": loads_dict["total_wind_uplift_N"],
        "total_wind_pressure_N": loads_dict["total_wind_pressure_N"],
        "uplift_loads": loads_dict["uplift"],
        "pressure_loads": loads_dict["pressure"],
        "topology": topology
    }
