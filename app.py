def generate_saddle_span(params, annotations=None):
    span = params.get("B", 5.0)
    rise = params.get("A", 13.0)
    laa = params.get("LAA", 10.0)
    num_points = 50

    if span <= 0 or rise <= 0 or laa <= 0:
        return go.Figure()

    x = np.linspace(-span/2, span/2, num_points)
    z_beam = rise * (1 - (2 * x / span)**2)
    y1 = -laa/2 * (1 - (2 * x / span)**2)
    y2 = laa/2 * (1 - (2 * x / span)**2)

    u = np.linspace(0, 1, num_points)
    v = np.linspace(0, 1, num_points)

    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))

    for i, u_val in enumerate(u):
        x_pos = -span/2 + u_val * span
        y_beam1 = y1[i]
        y_beam2 = y2[i]
        z_at_x = rise * (1 - (2 * x_pos / span)**2) if abs(x_pos) <= span/2 else 0

        for j, v_val in enumerate(v):
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            saddle_factor = 1 - 0.3 * (1 - (2 * v_val - 1)**2)
            z_pos = z_at_x * saddle_factor
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos

    fig = go.Figure()

    # Beams
    fig.add_trace(go.Scatter3d(x=x, y=y1, z=z_beam, mode='lines', name='Beam 1', line=dict(color='#FF6B6B', width=8)))
    fig.add_trace(go.Scatter3d(x=x, y=y2, z=z_beam, mode='lines', name='Beam 2', line=dict(color='#FF6B6B', width=8)))

    # Membrane
    fig.add_trace(go.Surface(x=X_surf, y=Y_surf, z=Z_surf, 
                             colorscale=[[0, '#2a3a5f'], [0.5, '#4a7a9c'], [1, '#6ab0d4']],
                             opacity=0.8, showscale=False))

    # Apex markers
    fig.add_trace(go.Scatter3d(x=[0], y=[y1[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 1', marker=dict(color='#FFD93D', size=12, symbol='diamond')))
    fig.add_trace(go.Scatter3d(x=[0], y=[y2[num_points//2]], z=[rise], 
                               mode='markers', name='Apex 2', marker=dict(color='#FFD93D', size=12, symbol='diamond')))

    # Support markers
    fig.add_trace(go.Scatter3d(x=[-span/2], y=[0], z=[0], 
                               mode='markers', name='Support 1', marker=dict(color='#4ECDC4', size=10, symbol='square')))
    fig.add_trace(go.Scatter3d(x=[span/2], y=[0], z=[0], 
                               mode='markers', name='Support 2', marker=dict(color='#4ECDC4', size=10, symbol='square')))

    # Engineering Annotations
    if annotations:
        if annotations.get("show_wind", True):
            fig.add_trace(go.Scatter3d(
                x=[-span/4, -span/4], y=[-laa/4, -laa/4], z=[rise*0.8, rise*1.2],
                mode='lines',
                name='Wind Load',
                line=dict(color='#FF6B6B', width=4, dash='dash')
            ))
            fig.add_trace(go.Scatter3d(
                x=[span/4, span/4], y=[laa/4, laa/4], z=[rise*0.8, rise*1.2],
                mode='lines',
                name='Wind Load',
                line=dict(color='#FF6B6B', width=4, dash='dash')
            ))

        if annotations.get("show_tie_down", True):
            fig.add_trace(go.Scatter3d(
                x=[-span/2, -span/2, span/2, span/2],
                y=[-1, 1, -1, 1],
                z=[-0.5, -0.5, -0.5, -0.5],
                mode='markers',
                name='Tie-Down Anchors',
                marker=dict(color='#4ECDC4', size=14, symbol='x')
            ))

        if annotations.get("show_load_path", True):
            fig.add_trace(go.Scatter3d(
                x=[0, 0], y=[0, 0], z=[rise, rise-2],
                mode='lines',
                name='Load Path',
                line=dict(color='#FFD93D', width=5)
            ))

    fig.update_layout(
        scene=dict(
            xaxis_title='Span (m)',
            yaxis_title='Width (m)',
            zaxis_title='Height (m)',
            xaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            yaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            zaxis=dict(color='#b0c4de', gridcolor='#1a2a3a'),
            bgcolor='#0a0e17',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0))
        ),
        paper_bgcolor='#0a0e17',
        margin=dict(l=0, r=0, b=0, t=0),
        legend=dict(
            font=dict(color='#ffffff'),
            bgcolor='rgba(10,14,23,0.8)',
            bordercolor='#2a3a4f',
            borderwidth=1
        )
    )
    return fig
