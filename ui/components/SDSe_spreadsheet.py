# =============================================================================
# SDSe Fluid Design Studio - Interactive Spreadsheet Component
# =============================================================================
# A live data editor for the Element Seed Schedule.
# The "Family" and "Auto-Size" columns are locked and display
# "Pending Engine" until the Auto-Design logic is built.
# =============================================================================

import streamlit as st
import pandas as pd

def render_element_spreadsheet(elements, key_prefix="dome"):
    """
    Renders the interactive data editor.
    Returns the updated list of elements.
    """
    if not elements:
        st.info("No elements to display.")
        return elements

    access_mode = str(st.session_state.get("access_mode", "owner")).lower()
    is_locked = access_mode not in ("owner", "pro")

    if is_locked:
        st.warning("🔒 **Pro Feature:** Upgrade to Pro to edit element IDs, choose sections, and generate BoQ reports.")
    else:
        st.caption("Click any cell to edit. Engine sizing is locked until v1.0.")

    rows = []
    for el in elements:
        # Ensure the SDSe_ prefix
        display_id = el["id"] if el["id"].startswith("SDSe_") else f"SDSe_{el['id']}"
        
        rows.append({
            "Visible": True, 
            "ID": display_id,
            "Type": el["type"],
            "Role": el["seed"].get("role", ""),
            "Family": "Pending Engine", 
            "Auto-Size": "Pending Engine", 
            "Baseplate": el["seed"].get("baseplate", "-"),
            "Bolts": el["seed"].get("bolts", "-"),
            "Gusset": el["seed"].get("gusset", "-"),
        })
    
    df = pd.DataFrame(rows)

    column_config = {
        "Visible": st.column_config.CheckboxColumn("👁️", default=True, width="small"),
        "ID": st.column_config.TextColumn("Element ID", required=True, width="medium"),
        "Type": st.column_config.TextColumn("Type", disabled=True, width="small"),
        "Role": st.column_config.TextColumn("Role", disabled=True, width="medium"),
        "Family": st.column_config.TextColumn("Family", disabled=True, width="small"),
        "Auto-Size": st.column_config.TextColumn("Auto-Size", disabled=True, width="medium"),
        "Baseplate": st.column_config.TextColumn("Baseplate", width="small"),
        "Bolts": st.column_config.TextColumn("Bolts", width="small"),
        "Gusset": st.column_config.TextColumn("Gusset", width="small"),
    }

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed", 
        disabled=is_locked, 
        key=f"{key_prefix}_data_editor"
    )

    updated_elements = []
    for index, row in edited_df.iterrows():
        # FIX APPLIED HERE: Strip the display prefix to find the real ID
        raw_id = row["ID"].replace("SDSe_", "", 1)
        
        # Match against the raw ID
        original_el = next((e for e in elements if e["id"] == raw_id), None)
        
        if original_el:
            new_el = original_el.copy()
            # Save the raw ID back to the engine state
            new_el["id"] = raw_id
            new_el["visible"] = row["Visible"]
            new_el["seed"]["baseplate"] = row["Baseplate"]
            new_el["seed"]["bolts"] = row["Bolts"]
            new_el["seed"]["gusset"] = row["Gusset"]
            updated_elements.append(new_el)

    return updated_elements
