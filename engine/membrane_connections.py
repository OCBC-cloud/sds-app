"""SDSe Engine — Universal Membrane Connection Types.

Defines the four fundamental connection types for any tension membrane roof,
regardless of shape (multi-cone, dome, hypar, saddle, leaf).

Every membrane boundary edge connects to structure via one of these four
types:

    CONNECTION_RIGID   — membrane clamped directly to a member
    CONNECTION_CABLE   — membrane attached to a boundary cable, cable to anchors
    CONNECTION_SPOKE   — membrane attached to a radial spoke/rod
    CONNECTION_KADER   — membrane slides along a member (transverse only)

Shape-specific workshops (multi-cone, hypar, dome) choose which connection
type applies to each boundary edge. The universal loader uses this module
to transfer membrane forces to the 3D steel frame.

This module has no dependencies on other engine modules.
"""

import numpy as np

EPS = 1e-12


# =============================================================================
# CONNECTION TYPE CONSTANTS
# =============================================================================

CONNECTION_RIGID = "rigid"
CONNECTION_CABLE = "cable"
CONNECTION_SPOKE = "spoke"
CONNECTION_KADER = "kader"

ALL_CONNECTION_TYPES = [
    CONNECTION_RIGID,
    CONNECTION_CABLE,
    CONNECTION_SPOKE,
    CONNECTION_KADER,
]


# =============================================================================
# UTILITIES
# =============================================================================

def normalize(v):
    """Return unit vector. Zero vector returns zero."""
    n = float(np.linalg.norm(v))
    if n < EPS:
        return np.zeros_like(v)
    return v / n


def project_onto_axis(force, axis):
    """Return the axial component of force along axis.
    
    force: (3,) array
    axis:  (3,) array (unit vector)
    returns: (3,) array, the component along axis
    """
    axis = normalize(axis)
    if np.linalg.norm(axis) < EPS:
        return np.zeros_like(force)
    axial_mag = float(np.dot(force, axis))
    return axial_mag * axis


def project_onto_transverse(force, axis):
    """Return the transverse (perpendicular-to-axis) component of force.
    
    force: (3,) array
    axis:  (3,) array (unit vector)
    returns: (3,) array, the component perpendicular to axis
    """
    axis = normalize(axis)
    if np.linalg.norm(axis) < EPS:
        return force.copy()
    axial = project_onto_axis(force, axis)
    return force - axial


def vector_sum(forces):
    """Sum a list of (3,) force vectors."""
    if not forces:
        return np.zeros(3)
    return np.sum(np.asarray(forces, dtype=float), axis=0)


# =============================================================================
# TRANSFER FUNCTIONS
# =============================================================================
# Each function returns a list of (node_id, force_vector) contributions to
# add to the 3D frame nodes. The caller (steel_frame_builder) accumulates
# these into a global loads array.

def transfer_rigid(membrane_force_on_node, target_node_id):
    """Rigid connection: the full membrane force goes to the member node.
    
    membrane_force_on_node: (3,) force vector that the membrane exerts on
                             the structural member at the boundary node.
    target_node_id:         the 3D frame node id of the structural member.
    returns:                [(target_node_id, membrane_force_on_node)]
    """
    return [(int(target_node_id), np.asarray(membrane_force_on_node, dtype=float).copy())]


def transfer_cable(cable_tension_N, cable_end_a_node_id, cable_end_b_node_id,
                    cable_direction):
    """Cable-supported connection: the cable tension goes to both anchors.
    
    cable_tension_N:        scalar tension (N), positive.
    cable_end_a_node_id:    node id of anchor A on the 3D frame.
    cable_end_b_node_id:    node id of anchor B on the 3D frame.
    cable_direction:        (3,) unit vector from A to B (or use any direction
                             consistent with the anchor reactions).
    returns:                [(a_id, +T*dir), (b_id, -T*dir)]
    
    The anchor at A sees the cable pulling toward B, so A is pulled along
    +dir by T. The anchor at B sees the cable pulling toward A, so B is
    pulled along -dir by T. This is the standard cable end-reaction
    convention used in the corner plate design.
    """
    direction = normalize(np.asarray(cable_direction, dtype=float))
    T_vec = float(cable_tension_N) * direction
    return [
        (int(cable_end_a_node_id), T_vec.copy()),
        (int(cable_end_b_node_id), -T_vec.copy()),
    ]


def transfer_spoke(membrane_force_on_ring_node, spoke_target_node_id,
                    spoke_direction):
    """Radial spoke connection: only the axial component goes to the target.
    
    The spoke is a tension/compression rod from the ring to the drop member.
    It only carries axial force. The membrane's pull on the ring node
    projects onto the spoke axis, and only that axial component transfers
    to the spoke's far end.
    
    membrane_force_on_ring_node: (3,) force vector that the membrane
                                  exerts on the ring node.
    spoke_target_node_id:        node id where the spoke terminates
                                  (typically on the drop member).
    spoke_direction:             (3,) unit vector along the spoke axis,
                                  from ring node to target node.
    returns:                     [(target_node_id, F_axial)]
    """
    F_axial_vec = project_onto_axis(membrane_force_on_ring_node, spoke_direction)
    return [(int(spoke_target_node_id), F_axial_vec)]


def transfer_kader(membrane_force_on_node, beam_axis, target_node_id):
    """Kader sliding connection: only the transverse component goes to beam.
    
    The membrane slides along the beam. It transfers perpendicular force
    only. The axial component is free (the slider allows movement along
    the beam).
    
    membrane_force_on_node: (3,) force vector the membrane exerts at the
                             sliding node.
    beam_axis:              (3,) unit vector along the beam.
    target_node_id:         node id on the beam.
    returns:                [(target_node_id, F_transverse)]
    """
    F_transverse_vec = project_onto_transverse(membrane_force_on_node, beam_axis)
    return [(int(target_node_id), F_transverse_vec)]


# =============================================================================
# HIGH-LEVEL DISPATCHER
# =============================================================================

def transfer_connection(connection_type, membrane_force_on_node,
                         target_node_id, **kwargs):
    """Universal dispatcher: transfer membrane force to the frame for any
    connection type.
    
    connection_type: one of CONNECTION_RIGID, CONNECTION_CABLE,
                      CONNECTION_SPOKE, CONNECTION_KADER.
    membrane_force_on_node: (3,) force vector at the membrane node.
    target_node_id: the frame node the connection targets.
    
    kwargs depend on connection type:
        RIGID: no extra kwargs
        CABLE: cable_tension_N, cable_end_b_node_id, cable_direction
        SPOKE: spoke_direction (spoke_target is target_node_id)
        KADER: beam_axis
    
    returns: list of (node_id, force_vector) contributions.
    """
    if connection_type == CONNECTION_RIGID:
        return transfer_rigid(membrane_force_on_node, target_node_id)
    
    elif connection_type == CONNECTION_CABLE:
        cable_tension_N = kwargs.get("cable_tension_N", 0.0)
        cable_end_b_node_id = kwargs.get("cable_end_b_node_id", target_node_id)
        cable_direction = kwargs.get("cable_direction", np.array([1.0, 0.0, 0.0]))
        return transfer_cable(cable_tension_N, target_node_id,
                               cable_end_b_node_id, cable_direction)
    
    elif connection_type == CONNECTION_SPOKE:
        spoke_direction = kwargs.get("spoke_direction", np.array([0.0, 0.0, 1.0]))
        return transfer_spoke(membrane_force_on_node, target_node_id,
                               spoke_direction)
    
    elif connection_type == CONNECTION_KADER:
        beam_axis = kwargs.get("beam_axis", np.array([1.0, 0.0, 0.0]))
        return transfer_kader(membrane_force_on_node, beam_axis, target_node_id)
    
    else:
        raise ValueError("Unknown connection type: %s" % connection_type)


# =============================================================================
# SELF-TEST
# =============================================================================

def _test_connections():
    """Quick self-test for the transfer functions."""
    print("SDSe membrane_connections self-test")
    
    # RIGID
    result = transfer_rigid(np.array([1.0, 2.0, 3.0]), target_node_id=5)
    assert result[0][0] == 5
    assert np.allclose(result[0][1], [1.0, 2.0, 3.0])
    
    # CABLE
    result = transfer_cable(
        cable_tension_N=100.0,
        cable_end_a_node_id=3,
        cable_end_b_node_id=7,
        cable_direction=np.array([1.0, 0.0, 0.0]),
    )
    assert result[0][0] == 3 and np.allclose(result[0][1], [100.0, 0.0, 0.0])
    assert result[1][0] == 7 and np.allclose(result[1][1], [-100.0, 0.0, 0.0])
    
    # SPOKE
    result = transfer_spoke(
        membrane_force_on_ring_node=np.array([10.0, 5.0, 0.0]),
        spoke_target_node_id=9,
        spoke_direction=np.array([1.0, 0.0, 0.0]),
    )
    assert result[0][0] == 9 and np.allclose(result[0][1], [10.0, 0.0, 0.0])
    
    # KADER
    result = transfer_kader(
        membrane_force_on_node=np.array([10.0, 5.0, 3.0]),
        beam_axis=np.array([1.0, 0.0, 0.0]),
        target_node_id=11,
    )
    assert result[0][0] == 11 and np.allclose(result[0][1], [0.0, 5.0, 3.0])
    
    print("All tests passed.")


if __name__ == "__main__":
    _test_connections()
