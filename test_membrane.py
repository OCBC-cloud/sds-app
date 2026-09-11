# =============================================================================
# Temporary test page for engine/membrane.py - Message 1 verification
# =============================================================================
# Runs the mesh-handling self-test from engine/membrane.py.
# Delete this file once the engine is verified and wired into the main app.
# =============================================================================

import streamlit as st
from engine.membrane import _verify_mesh_handling

st.set_page_config(page_title="Membrane Test", layout="centered")
st.title("Membrane Engine - Message 1 Verification")
st.caption("Runs _verify_mesh_handling() from engine/membrane.py")

res = _verify_mesh_handling()

st.subheader("Summary")
st.write("Edge length test (3,4,5): " + str(res["edge_length_3_4_5"]))
st.write("Edge length OK: " + str(res["edge_length_ok"]))
st.write("Unit vector test: " + str(res["unit_vector_x"]))
st.write("Unit vector OK: " + str(res["unit_vector_ok"]))
st.write("Grid nodes: " + str(res["grid_nodes"]) + "  (expected 9)")
st.write("Grid edges: " + str(res["grid_edges"]) + "  (expected 12)")
st.write("Free nodes: " + str(res["grid_free_count"]) + "  (expected 1)")
st.write("Fixed nodes: " + str(res["grid_fixed_count"]) + "  (expected 8)")
st.write("Interior neighbours: " + str(res["interior_neighbours"]) + "  (expected 4)")
st.write("Uniform edge lengths: " + str(res["uniform_edge_lengths"]))

st.subheader("Raw result")
st.json(res)

if res["pass"]:
    st.success("MESSAGE 1 GATE: PASS")
else:
    st.error("MESSAGE 1 GATE: FAIL")
