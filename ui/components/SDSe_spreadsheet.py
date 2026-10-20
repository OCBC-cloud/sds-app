# =============================================================================
# SDSe Fluid Design Studio - Interactive Spreadsheet Component
# =============================================================================
# A live data editor for the Element Seed Schedule.
# Locks editing for Free tier users.
# =============================================================================

import streamlit as st
import pandas as pd

try:
    from data.sections import SECTION_PROPERTIES
    from data.materials import STEEL_MATERIALS
except ImportError:
    SECTION_PROPERTIES = {}
    STEEL_MATERIALS = {}

# Extract available section families (CHS, SHS, I-Beam, etc.)
SECTION_TYPES = list(set([props["type"] for props in SECTION_PROPERTIES.values()])) if SECTION_PROPERTIES else ["CHS", "SHS", "RHS", "I-Beam"]

def render_element_spreadsheet(elements, key_prefix="dome"):
    """
    Renders the interactive data editor.
    Returns the updated list of elements.
    """
    if not elements:
        st.info("No elements to display.")
        return elements

    # Check access tier
    access_mode = str(st.session_state.get("access_mode", "owner")).lower()
    is_locked = access_mode not in ("owner", "pro")

    if is_locked:
        st.warning("🔒 **Pro Feature:** Upgrade to Pro to edit element IDs, choose sections, and generate BoQ reports.")
    else:
        st.caption("Click any cell to edit. Check the box to hide in 3D.")

    # Convert the list of dictionaries into a pandas DataFrame for the editor.
    rows = []
    for el in elements:
        # Strip the "SDSe_" prefix for display, or add it if it's missing
        display_id = el["id"] if el["id"].startswith("SDSe_") else f"SDSe_{el['id']}"
        
        rows.append({
            "Visible": True, 
            "ID": display_id,
            "Type": el["type"],
            "Role": el["seed"].get("role", ""),
            "Element Family": el["seed"].get("section_material", "CHS"),
            "Auto-Size": "Pending Engine", 
            "Baseplate": el["seed"].get("baseplate", "-"),
            "Bolts": el["seed"].get("bolts", "-"),
            "Gusset": el["seed"].get("gusset", "-"),
        })
    
    df = pd.DataFrame(rows)

    column_config = {
        "Visible": st.column_config.CheckboxColumn(
            "👁️",
            help="Toggle visibility in the 3D view",
            default=True,
            width="small"
        ),
        "ID": st.column_config.TextColumn(
            "Element ID",
            help="Rename this element",
            required=True,
            width="medium"
        ),
        "Type": st.column_config.TextColumn(
            "Type",
            disabled=True,
            width="small"
        ),
        "Role": st.column_config.TextColumn(
            "Role",
            disabled=True,
            width="medium"
        ),
        "Element Family": st.column_config.SelectboxColumn(
            "Family",
            options=SECTION_TYPES,
            help="Select the cross-section family (e.g., CHS, I-Beam)",
            width="small"
        ),
        "Auto-Size": st.column_config.TextColumn(
            "Auto-Size",
            disabled=True,
            help="The solver will recommend the exact section here.",
            width="medium"
        ),
        "Baseplate": st.column_config.TextColumn(
            "Baseplate",
            help="e.g., 300x300x15",
            width="small"
        ),
        "Bolts": st.column_config.TextColumn(
            "Bolts",
            help="e.g., 4x M16",
            width="small"
        ),
        "Gusset": st.column_config.TextColumn(
            "Gusset",
            help="e.g., 10mm",
            width="small"
        ),
    }

    # Render the editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed", 
        disabled=is_locked, # This is the magic lock
        key=f"{key_prefix}_data_editor"
    )

    # Reconstruct the elements list from the edited DataFrame
    updated_elements = []
    for index, row in edited_df.iterrows():
        original_el = next((e for e in elements if e["id"] == df.iloc[index]["ID"]), None)
        
        if original_el:
            new_el = original_el.copy()
            new_el["id"] = row["ID"]
            new_el["visible"] = row["Visible"]
            new_el["seed"]["section_material"] = row["Element Family"] 
            new_el["seed"]["baseplate"] = row["Baseplate"]
            new_el["seed"]["bolts"] = row["Bolts"]
            new_el["seed"]["gusset"] = row["Gusset"]
            updated_elements.append(new_el)

    return updated_elements
