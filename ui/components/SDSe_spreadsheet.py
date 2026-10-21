# =============================================================================
# SDSe Fluid Design Studio - Interactive Spreadsheet Component
# =============================================================================
# A live data editor for the Element Seed Schedule.
# Splits elements by type and displays the Auto-Design results.
# =============================================================================

import streamlit as st
import pandas as pd

try:
    from data.sections import SECTION_PROPERTIES
    from data.materials import CABLE_PROPERTIES, FABRIC_PROPERTIES
except ImportError:
    SECTION_PROPERTIES = {}
    CABLE_PROPERTIES = {}
    FABRIC_PROPERTIES = {}

# Extract available families for the dropdowns
STEEL_TYPES = list(set([props["type"] for props in SECTION_PROPERTIES.values()])) if SECTION_PROPERTIES else ["CHS", "SHS", "RHS", "I-Beam"]
CABLE_TYPES = list(CABLE_PROPERTIES.keys()) if CABLE_PROPERTIES else ["Strand", "Locked Coil"]
FABRIC_TYPES = list(FABRIC_PROPERTIES.keys()) if FABRIC_PROPERTIES else ["PVDF", "PTFE", "ETFE"]


def _build_dataframe(elements, default_family, valid_options):
    rows = []
    for el in elements:
        display_id = el["id"] if el["id"].startswith("SDSe_") else f"SDSe_{el['id']}"
        
        current_family = el["seed"].get("section_material", default_family)
        if current_family not in valid_options:
            current_family = default_family
            
        auto_size = el["seed"].get("auto_size", "Pending Engine")

        rows.append({
            "Visible": True, 
            "ID": display_id,
            "Role": el["seed"].get("role", ""),
            "Family": current_family,
            "Solver Output": auto_size,  # The Engine recommendation
            "Baseplate": el["seed"].get("baseplate", "-"),
            "Bolts": el["seed"].get("bolts", "-"),
            "Gusset": el["seed"].get("gusset", "-"),
        })
    return pd.DataFrame(rows)


def _render_editor(df, options, key, is_locked, include_solver_col=True):
    column_config = {
        "Visible": st.column_config.CheckboxColumn("👁️", default=True, width="small"),
        "ID": st.column_config.TextColumn("Element ID", required=True, width="medium"),
        "Role": st.column_config.TextColumn("Role", disabled=True, width="medium"),
        "Family": st.column_config.SelectboxColumn("User Choice", options=options, width="small"),
        "Solver Output": st.column_config.TextColumn("Solver Output", disabled=True, width="medium"),
        "Baseplate": st.column_config.TextColumn("Baseplate", width="small"),
        "Bolts": st.column_config.TextColumn("Bolts", width="small"),
        "Gusset": st.column_config.TextColumn("Gusset", width="small"),
    }
    
    if not include_solver_col:
        del column_config["Solver Output"]

    return st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed", 
        disabled=is_locked, 
        key=key
    )


def render_element_spreadsheet(elements, key_prefix="dome"):
    if not elements:
        st.info("No elements to display.")
        return elements

    access_mode = str(st.session_state.get("access_mode", "owner")).lower()
    is_locked = access_mode not in ("owner", "pro")

    if is_locked:
        st.warning("🔒 **Pro Feature:** Upgrade to Pro to edit element IDs, choose sections, and generate BoQ reports.")
    else:
        st.caption("Select a family, and the engine will suggest the exact section below.")

    # Group elements
    steel_elements = [e for e in elements if e["type"] == "rigid_member"]
    cable_elements = [e for e in elements if e["type"] == "cable"]
    membrane_elements = [e for e in elements if e["type"] == "membrane"]
    other_elements = [e for e in elements if e["type"] not in ("rigid_member", "cable", "membrane")]

    updated_elements = []

    # 1. Steel Members
    if steel_elements:
        st.markdown("### Steel Members")
        df_steel = _build_dataframe(steel_elements, "CHS", STEEL_TYPES)
        edited_steel = _render_editor(df_steel, STEEL_TYPES, f"{key_prefix}_steel_editor", is_locked)
        
        for index, row in edited_steel.iterrows():
            orig = next((e for e in steel_elements if e["id"] == df_steel.iloc[index]["ID"]), None)
            if orig:
                new_el = orig.copy()
                new_el["id"] = row["ID"]
                new_el["visible"] = row["Visible"]
                new_el["seed"]["section_material"] = row["Family"]
                new_el["seed"]["baseplate"] = row["Baseplate"]
                new_el["seed"]["bolts"] = row["Bolts"]
                new_el["seed"]["gusset"] = row["Gusset"]
                updated_elements.append(new_el)

    # 2. Cables
    if cable_elements:
        st.markdown("### Cables")
        df_cables = _build_dataframe(cable_elements, "Locked Coil", CABLE_TYPES)
        edited_cables = _render_editor(df_cables, CABLE_TYPES, f"{key_prefix}_cable_editor", is_locked)
        
        for index, row in edited_cables.iterrows():
            orig = next((e for e in cable_elements if e["id"] == df_cables.iloc[index]["ID"]), None)
            if orig:
                new_el = orig.copy()
                new_el["id"] = row["ID"]
                new_el["visible"] = row["Visible"]
                new_el["seed"]["section_material"] = row["Family"]
                updated_elements.append(new_el)

    # 3. Membranes
    if membrane_elements:
        st.markdown("### Membrane Fabric")
        df_membrane = _build_dataframe(membrane_elements, "PVDF", FABRIC_TYPES)
        edited_membrane = _render_editor(df_membrane, FABRIC_TYPES, f"{key_prefix}_membrane_editor", is_locked)
        
        for index, row in edited_membrane.iterrows():
            orig = next((e for e in membrane_elements if e["id"] == df_membrane.iloc[index]["ID"]), None)
            if orig:
                new_el = orig.copy()
                new_el["id"] = row["ID"]
                new_el["visible"] = row["Visible"]
                new_el["seed"]["section_material"] = row["Family"]
                updated_elements.append(new_el)

    # 4. Other
    if other_elements:
        st.markdown("### Nodes & Anchors")
        for el in other_elements:
            updated_elements.append(el)

    return updated_elements
