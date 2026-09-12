# =============================================================================
# SDSe Fluid Design Studio - Workshop Router
# =============================================================================
# Dispatches to the correct variant-specific workshop module based on
# the current variant_key in session state.
#
# Structure:
#   - Each variant workshop lives in its own file under ui/workshops/
#   - Each file exposes a render_<variant>() function
#   - This router imports the correct file and calls its render function
#
# Design (agreed 2026-09-13):
#   - One file per variant (not one giant workshop.py)
#   - Only variants with specs get their own workshop file
#   - Variants without a workshop show "Workshop coming soon"
# =============================================================================

import importlib

import streamlit as st


# =============================================================================
# VARIANT REGISTRY
# =============================================================================
# Maps variant_key to the module path and function name.
# When a new variant workshop is built, add an entry here.

VARIANT_REGISTRY = {
    # Saddle Span family
    "standard_saddle": {
        "module": "ui.workshops.saddle_standard",
        "function": "render_saddle_standard",
    },
    "cantilever_leaf": {
        "module": "ui.workshops.saddle_leaf",
        "function": "render_saddle_leaf",
    },
    # Frame Supported Saddle - not yet built
    "frame_supported_saddle": {
        "module": None,
        "function": None,
    },
    # Cantilever Flower - not yet built
    "cantilever_flower": {
        "module": None,
        "function": None,
    },
    # Tensile Sails family - not yet built
    "hypar_sail_3": {"module": None, "function": None},
    "hypar_sail_4": {"module": None, "function": None},
    "ridge_sail": {"module": None, "function": None},
    "multiple_sails": {"module": None, "function": None},
    "wall_sail": {"module": None, "function": None},
    "column_sail": {"module": None, "function": None},
    # Framed Tensile family - not yet built
    "simple_frame": {"module": None, "function": None},
    "arched_frame": {"module": None, "function": None},
    "trussed_frame": {"module": None, "function": None},
    # Uni-Pole Tensile family - not yet built
    "single_cone": {"module": None, "function": None},
    "multi_cone_cluster": {"module": None, "function": None},
    "umbrella": {"module": None, "function": None},
    # Canopy family - not yet built
    "cantilever_flat": {"module": None, "function": None},
    "cantilever_bell": {"module": None, "function": None},
    "cantilever_pyramid": {"module": None, "function": None},
    "cantilever_cone": {"module": None, "function": None},
    "cable_supported": {"module": None, "function": None},
    "wall_mounted": {"module": None, "function": None},
    "tree_canopy": {"module": None, "function": None},
    # Frame Tent family - not yet built
    "pyramid_tent": {"module": None, "function": None},
    "gable_tent": {"module": None, "function": None},
    "hip_tent": {"module": None, "function": None},
    "sail_tent": {"module": None, "function": None},
    # Portal Frame family - not yet built
    "simple_portal": {"module": None, "function": None},
    "portal_with_mezzanine": {"module": None, "function": None},
    "portal_with_crane": {"module": None, "function": None},
    "multi_bay_portal": {"module": None, "function": None},
}


# =============================================================================
# CSS
# =============================================================================

WORKSHOP_ROUTER_CSS = """
    <style>
    .workshop-coming-soon {
        background-color: #1a2a3a;
        border-left: 4px solid #f39c12;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 2rem 0;
        text-align: center;
    }
    .workshop-coming-soon .title {
        color: #f39c12;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .workshop-coming-soon .desc {
        color: #c8d4e0;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    </style>
"""


# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def render_workshop():
    """
    Route to the correct variant workshop.
    Called by the navigation router when the app state is 'workshop'.
    """
    st.markdown(WORKSHOP_ROUTER_CSS, unsafe_allow_html=True)

    variant_key = st.session_state.get("variant_key", "")
    variant_name = st.session_state.get("variant_name", "Unknown Variant")
    structure_name = st.session_state.get("structure_name", "Unknown Structure")

    # ---- Breadcrumb
    st.markdown(
        '<div style="font-size: 0.85rem; color: #a8b8c8; margin-bottom: 1rem;">'
        'SDSe Fluid Design Studio / '
        '<span style="color: #f39c12; font-weight: 600;">' + structure_name + '</span>'
        ' / '
        '<span style="color: #f39c12; font-weight: 600;">' + variant_name + '</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Look up the variant
    if not variant_key:
        _render_missing()

        st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
        if st.button("Back to Registration", key="ws_back_no_key", use_container_width=True):
            st.session_state.page = "registration"
            st.rerun()
        return

    entry = VARIANT_REGISTRY.get(variant_key, None)

    if entry is None:
        _render_coming_soon(variant_name, reason="This variant is not registered.")
        _render_back_button()
        return

    module_path = entry.get("module")
    function_name = entry.get("function")

    if not module_path or not function_name:
        _render_coming_soon(
            variant_name,
            reason=(
                "The design workshop for this variant is being built. "
                "Check back soon. Only Standard Saddle and Cantilever Leaf "
                "have workshops available at this stage."
            ),
        )
        _render_back_button()
        return

    # ---- Try to import and call
    try:
        mod = importlib.import_module(module_path)
        render_fn = getattr(mod, function_name)
        render_fn()
    except ImportError as e:
        _render_coming_soon(
            variant_name,
            reason="Workshop module not yet deployed. Error: " + str(e),
        )
        _render_back_button()
    except AttributeError as e:
        _render_coming_soon(
            variant_name,
            reason="Workshop function not found in module. Error: " + str(e),
        )
        _render_back_button()
    except Exception as e:
        st.error("Workshop failed to load: " + str(e))
        _render_back_button()


# =============================================================================
# HELPERS
# =============================================================================

def _render_missing():
    """Shown when variant_key is missing."""
    st.markdown(
        '<div class="workshop-coming-soon">'
        '<div class="title">No Variant Selected</div>'
        '<div class="desc">'
        'Please return to Registration and select a variant to continue.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_coming_soon(variant_name, reason=""):
    """Shown when the variant has no workshop yet."""
    st.markdown(
        '<div class="workshop-coming-soon">'
        '<div class="title">Workshop Coming Soon</div>'
        '<div class="desc">'
        '<strong>' + variant_name + '</strong><br><br>'
        + reason +
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_back_button():
    """Back button to return to Registration."""
    st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
    if st.button("Back to Registration", key="ws_back", use_container_width=True):
        st.session_state.page = "registration"
        st.rerun()
