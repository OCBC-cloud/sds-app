def generate_curved_beam_3d(params, materials=None, curve_type="parabolic"):
    span = params.get("B", 10.0) if params else 10.0
    rise = params.get("A", 6.0) if params else 6.0
    laa = params.get("LAA", 15.0) if params else 15.0
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = get_curve_shape(x, span, rise, curve_type)
    
    y1 = -laa/2 * (1 - (2 * x / span)**2) * 0.8
    y2 = laa/2 * (1 - (2 * x / span)**2) * 0.8

    fig = go.Figure()

    # Calculate adaptive line width based on structure size
    max_dim = max(span, laa, rise)
    line_width = max(2, min(8, 40 / (max_dim / 10)))

    # Main beams
    fig.add_trace(go.Scatter3d(
        x=x, y=y1, z=z_beam,
        mode='lines',
        line=dict(color='#FF6B6B', width=line_width),
        showlegend=False
    ))
    fig.add_trace(go.Scatter3d(
        x=x, y=y2, z=z_beam,
        mode='lines',
        line=dict(color='#FF6B6B', width=line_width),
        showlegend=False
    ))

    # Membrane surface
    opacity = max(0.25, min(0.5, 30 / (max_dim / 5)))
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, x_pos in enumerate(x):
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = z_beam[i]

        for j, v_val in enumerate(np.linspace(0, 1, num_points)):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            z_pos = z_at_x * (1 - 0.3 * (1 - (2 * v_val - 1)**2))
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig.add_trace(go.Surface(
        x=X_surf, y=Y_surf, z=Z_surf,
        colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
        opacity=opacity, showscale=False, name='Membrane'
    ))

    # Secondary beams (purlins)
    design_results = st.session_state.get("design_results", {})
    if design_results and "secondary_beams" in design_results:
        sec = design_results["secondary_beams"]
        num_purlins = sec.get("num_purlins", 0)
        if num_purlins > 0:
            purlin_positions = np.linspace(-span/2 * 0.8, span/2 * 0.8, min(num_purlins, 12))
            for px in purlin_positions:
                idx = np.argmin(np.abs(x - px))
                z_at_p = z_beam[idx] * 0.85
                y_start = y1[idx] * 0.9
                y_end = y2[idx] * 0.9
                fig.add_trace(go.Scatter3d(
                    x=[px, px],
                    y=[y_start, y_end],
                    z=[z_at_p, z_at_p],
                    mode='lines',
                    line=dict(color='#e67e22', width=line_width * 0.5, dash='dash'),
                    showlegend=False
                ))

    # Rigid ties
    if design_results and "rigid_ties" in design_results:
        ties = design_results["rigid_ties"]
        num_ties = ties.get("num_ties", 0)
        if num_ties > 0:
            tie_positions = np.linspace(-span/2 * 0.7, span/2 * 0.7, min(num_ties, 10))
            for tx in tie_positions:
                idx = np.argmin(np.abs(x - tx))
                fig.add_trace(go.Scatter3d(
                    x=[tx, tx],
                    y=[0, 0],
                    z=[z_beam[idx] * 0.8, 0],
                    mode='lines',
                    line=dict(color='#f1c40f', width=line_width * 0.6),
                    showlegend=False
                ))

    # Cables
    if design_results and "cables" in design_results:
        cables = design_results["cables"]
        num_cables = cables.get("num_cables", 0)
        if num_cables > 0:
            cable_positions = np.linspace(-span/2 * 0.6, span/2 * 0.6, min(num_cables, 8))
            for cx in cable_positions:
                idx = np.argmin(np.abs(x - cx))
                anchor_x = cx * 1.3
                fig.add_trace(go.Scatter3d(
                    x=[cx, anchor_x],
                    y=[0, 0],
                    z=[z_beam[idx] * 0.7, 0],
                    mode='lines',
                    line=dict(color='#3498db', width=line_width * 0.4, dash='dot'),
                    showlegend=False
                ))

    # Adaptive camera distance
    cam_distance = 1.5 * max(1, max_dim / 6)

    # Simplified layout - removing problematic tickfont/titlefont
    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(
                eye=dict(x=cam_distance, y=cam_distance, z=cam_distance * 0.6),
                up=dict(x=0, y=0, z=1)
            ),
            dragmode='turntable',
            hovermode='closest'
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        autosize=True,
        width=None,
        height=None
    )
    return fig
