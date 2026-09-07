# ===== CABLE CONTROLS =====
st.markdown("**🔗 Cable Controls**")

cables_per_bay = st.selectbox(
    "Cables per Bay (Pairs)",
    [2, 4, 6],
    index=[2, 4, 6].index(st.session_state.cables_per_bay)
)
if cables_per_bay != st.session_state.cables_per_bay:
    st.session_state.cables_per_bay = cables_per_bay
    st.rerun()

cable_vertical_angle = st.slider(
    "📐 Vertical Angle (°)",
    min_value=20,
    max_value=80,
    value=st.session_state.cable_vertical_angle,
    step=5,
    help="Angle from horizontal (20° = shallow, 80° = steep)"
)
if cable_vertical_angle != st.session_state.cable_vertical_angle:
    st.session_state.cable_vertical_angle = cable_vertical_angle
    st.rerun()

cable_spread_angle = st.slider(
    "📐 Spread Angle (°)",
    min_value=0,
    max_value=60,
    value=st.session_state.cable_spread_angle,
    step=5,
    help="How much cables spread outward (0° = straight, 60° = wide)"
)
if cable_spread_angle != st.session_state.cable_spread_angle:
    st.session_state.cable_spread_angle = cable_spread_angle
    st.rerun()
