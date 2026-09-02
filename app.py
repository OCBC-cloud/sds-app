def generate_saddle_span(params):
    """
    Saddle span with two curved beams that CONVERGE at the supports.
    Membrane surface is a hyperbolic paraboloid (saddle shape).
    """
    span = params.get('span', 15.0)
    rise = params.get('rise', 6.5)
    laa = params.get('laa', 6.0)  # Apex-to-Apex distance
    num_points = 30
    
    # --- Beams ---
    x1 = np.linspace(-span/2, span/2, num_points)
    z1 = rise * (1 - (2 * x1 / span)**2)
    y1 = -laa/2 * (1 - (2 * x1 / span)**2)  # Converges at supports
    
    x2 = np.linspace(-span/2, span/2, num_points)
    z2 = rise * (1 - (2 * x2 / span)**2)
    y2 = laa/2 * (1 - (2 * x2 / span)**2)   # Converges at supports
    
    # --- Apex points ---
    apex1 = (0, -laa/2, rise)
    apex2 = (0, laa/2, rise)
    
    # --- Support points ---
    supports = [(-span/2, 0, 0), (span/2, 0, 0)]
    
    # --- Membrane surface (Hyperbolic Paraboloid / Saddle) ---
    u = np.linspace(0, 1, num_points)
    v = np.linspace(0, 1, num_points)
    X_surf = np.zeros((num_points, num_points))
    Y_surf = np.zeros((num_points, num_points))
    Z_surf = np.zeros((num_points, num_points))
    
    for i, u_val in enumerate(u):
        for j, v_val in enumerate(v):
            x_pos = -span/2 + u_val * span
            
            # Beam y positions at this x
            y_beam1 = -laa/2 * (1 - (2 * x_pos / span)**2)
            y_beam2 = laa/2 * (1 - (2 * x_pos / span)**2)
            
            # Interpolate y between beams
            y_pos = y_beam1 * (1 - v_val) + y_beam2 * v_val
            
            # Beam heights at this x
            z_beam = rise * (1 - (2 * x_pos / span)**2) if abs(x_pos) <= span/2 else 0
            
            # Saddle surface: z = z_beam * (1 - (2*y/laa)^2) * 0.95
            # This creates a hyperbolic paraboloid shape
            if laa > 0:
                y_normalized = (y_pos - y_beam1) / (y_beam2 - y_beam1 + 0.001)
                z_pos = z_beam * (1 - 0.4 * (2 * (y_normalized - 0.5))**2)
                # Ensure z_pos never exceeds beam height
                z_pos = min(z_pos, z_beam * 0.98)
            else:
                z_pos = z_beam * 0.95
            
            X_surf[i, j] = x_pos
            Y_surf[i, j] = y_pos
            Z_surf[i, j] = z_pos
    
    return {
        'type': 'Saddle Span',
        'beams': [
            {'x': x1.tolist(), 'y': y1.tolist(), 'z': z1.tolist(), 'color': '#FF6B6B'},
            {'x': x2.tolist(), 'y': y2.tolist(), 'z': z2.tolist(), 'color': '#FF6B6B'}
        ],
        'apexes': [apex1, apex2],
        'supports': supports,
        'surface': (X_surf.tolist(), Y_surf.tolist(), Z_surf.tolist()),
        'dimensions': {'span': span, 'rise': rise, 'laa': laa}
    }
