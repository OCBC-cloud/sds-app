# =============================================================================
# SDSe Engine - Material Database & Ultimate Limit State (ULS) Calculator
# =============================================================================
# This file holds the real-world breaking strengths and calculates the
# Ultimate Limit State (ULS) forces based on building codes.
# =============================================================================

# Breaking strengths in kN/m (Warp / Weft)
# Source: Standard European and ASTM tensile fabric testing.
FABRIC_DATABASE = {
    "PVDF": {
        "Type I": {"warp_kNm": 40.0, "weft_kNm": 35.0, "safety_factor": 6.0},
        "Type II": {"warp_kNm": 50.0, "weft_kNm": 45.0, "safety_factor": 6.0},
        "Type III": {"warp_kNm": 57.5, "weft_kNm": 51.0, "safety_factor": 6.0},
        "Type IV": {"warp_kNm": 70.0, "weft_kNm": 65.0, "safety_factor": 6.0},
    },
    "PTFE": {
        "Type I": {"warp_kNm": 100.0, "weft_kNm": 90.0, "safety_factor": 4.0},
        "Type II": {"warp_kNm": 130.0, "weft_kNm": 120.0, "safety_factor": 4.0},
        "Type III": {"warp_kNm": 160.0, "weft_kNm": 150.0, "safety_factor": 4.0},
        "Type IV": {"warp_kNm": 180.0, "weft_kNm": 170.0, "safety_factor": 4.0},
    },
    "ETFE": {
        "Type I": {"warp_kNm": 40.0, "weft_kNm": 40.0, "safety_factor": 5.0},
        "Type II": {"warp_kNm": 60.0, "weft_kNm": 60.0, "safety_factor": 5.0},
        "Type III": {"warp_kNm": 80.0, "weft_kNm": 80.0, "safety_factor": 5.0},
        "Type IV": {"warp_kNm": 100.0, "weft_kNm": 100.0, "safety_factor": 5.0},
    }
}

# Wind speed codes (Ultimate Basic Wind Velocity in m/s)
WIND_CODES = {
    "MY": {"speed_ms": 33.5, "name": "Malaysia (MS 1553)"},
    "SG": {"speed_ms": 30.0, "name": "Singapore (SS EN 1991-1-4)"},
    "ID": {"speed_ms": 35.0, "name": "Indonesia (SNI 1727)"},
    "TH": {"speed_ms": 30.0, "name": "Thailand (DPT)"},
    "VN": {"speed_ms": 35.0, "name": "Vietnam (QCVN)"},
    "CN": {"speed_ms": 35.0, "name": "China (GB 50009)"},
    "EU": {"speed_ms": 30.0, "name": "Europe (EN 1991-1-4)"},
    "UK": {"speed_ms": 30.0, "name": "UK (BS EN 1991-1-4)"},
    "US": {"speed_ms": 45.0, "name": "US (ASCE 7-22)"},
    "AU": {"speed_ms": 45.0, "name": "Australia (AS 1170.2)"},
}

def calculate_uls_forces(fabric_type, fabric_grade, wind_code_key):
    """
    Calculates the Ultimate Limit State (ULS) tension and wind pressure.
    Returns a dict with the design pressures and tensions.
    """
    # 1. Get the fabric breaking strength
    fabric = FABRIC_DATABASE.get(fabric_type, {}).get(fabric_grade)
    if not fabric:
        # Fallback to PVDF Type III
        fabric = FABRIC_DATABASE["PVDF"]["Type III"]
        
    warp_break_kNm = fabric["warp_kNm"]
    weft_break_kNm = fabric["weft_kNm"]
    sf = fabric["safety_factor"]
    
    # 2. Calculate Allowable Tension (ULS Design Tension)
    # This is the maximum force the fabric is allowed to carry under wind.
    allowable_warp_kNm = warp_break_kNm / sf
    allowable_weft_kNm = weft_break_kNm / sf
    
    # 3. Get the wind speed
    wind_data = WIND_CODES.get(wind_code_key, WIND_CODES["MY"])
    v_ms = wind_data["speed_ms"]
    
    # 4. Calculate Basic Wind Pressure (q)
    # q = 0.613 * V^2 (Pa)
    q_basic_pa = 0.613 * (v_ms ** 2)
    q_basic_kpa = q_basic_pa / 1000.0
    
    # 5. Add pressure coefficient for a dome (Cp)
    # Wind on a curved dome creates suction (uplift) and pressure.
    # A typical dome Cp ranges from -0.8 (suction) to +0.5 (pressure).
    # We design for the worst-case outward pull (suction) which stretches the membrane.
    cp_suction = -0.8
    cp_pressure = 0.5
    
    # Ultimate Wind Design Pressures
    wind_uls_suction_kpa = q_basic_kpa * cp_suction
    wind_uls_pressure_kpa = q_basic_kpa * cp_pressure

    return {
        "fabric_warp_break_kNm": warp_break_kNm,
        "fabric_weft_break_kNm": weft_break_kNm,
        "safety_factor": sf,
        "allowable_warp_kNm": allowable_warp_kNm,
        "allowable_weft_kNm": allowable_weft_kNm,
        "wind_speed_ms": v_ms,
        "q_basic_kpa": q_basic_kpa,
        "wind_uls_suction_kpa": wind_uls_suction_kpa,
        "wind_uls_pressure_kpa": wind_uls_pressure_kpa,
        "wind_code_name": wind_data["name"]
    }
