# =============================================================================
# SDSe Fluid Design Studio - Universal Workshop Renderer
# =============================================================================
# Reads a workshop recipe. Builds the input page. Enforces the
# accordion pattern. Enforces no sliders. Supports five input types.
#
# The renderer does not know any structure. It knows:
#   - a recipe dict (groups, inputs, preview/warning/info callables),
#   - a session-state prefix (e.g. "ws_ss" for Standard Saddle).
#
# The recipe owns all structure-specific knowledge.
#
# Public API:
#   render_workshop(recipe)
#
# Recipe shape (see UI_ARCHITECTURE.md Part 3):
#   {
#     "title":            str,
#     "breadcrumb":       (structure_name, variant_name),
#     "structure_label":  str,
#     "prefix":           str,
#     "defaults":         {session_key_suffix: default_value, ...},
#     "groups":           [ group, ... ],
#     "viewer_strings":   callable or None,
#     "actions":          {back_page, primary_label, primary_page},
#   }
#
# Group shape:
#   {
#     "key":      str,
#     "name":     str,
#     "help":     str,
#     "inputs":   [ input, ... ],
#     "preview":  callable(state, prefix) -> str or None,
#     "warning":  callable(state, prefix) -> str or None,
#     "info":     callable(state, prefix) -> str or None,
#     "defaults": {key_suffix: value, ...}  (optional; Foundation only)
#   }
#
# Input shape:
#   {
#     "key":      str,
#     "label":    str,
#     "type":     "number" | "integer" | "dropdown" | "radio" | "toggle",
#     "default":  value,
#     "min":      number  (numeric types only),
#     "max":      number  (numeric types only),
#     "step":     number  (numeric types only),
#     "options":  [ [value, label], ... ]  (dropdown / radio),
#     "help":     str or None,
#     "show_if":  callable(state, prefix) -> bool,
#   }
#
# History:
#   2026-09-28 - First build. Step 1 of UI_ARCHITECTURE.md Part 9.
# =============================================================================

import streamlit as st

from ui.workshops._shared import (
    WORKSHOP_CSS,
    section_header,
    render_breadcrumb,
    render_project_header,
    info_box,
    preview_box,
    warning_box,
)


_VALID_INPUT_TYPES = (
    "number", "integer", "dropdown", "radio", "toggle",
)


def _validate_recipe(recipe):
    """Raise ValueError if the recipe is malformed."""
    required = (
        "title", "breadcrumb", "structure_label",
        "prefix", "defaults", "groups", "actions",
    )
    for key in required:
        if key not in recipe:
            raise ValueError("recipe missing required key: " + key)

    if not isinstance(recipe["breadcrumb"], (tuple, list)):
        raise ValueError("recipe['breadcrumb'] must be a tuple")

    if len(recipe["breadcrumb"]) != 2:
        raise ValueError(
            "recipe['breadcrumb'] must be (structure_name, variant_name)"
        )

    for group in recipe["groups"]:
        for gk in ("key", "name", "inputs"):
            if gk not in group:
                raise ValueError("group missing required key: " + gk)
        for inp in group["inputs"]:
            for ik in ("key", "label", "type"):
                if ik not in inp:
                    raise ValueError("input missing required key: " + ik)
            if inp["type"] not in _VALID_INPUT_TYPES:
                raise ValueError(
                    "invalid input type %r for key %r"
                    % (inp["type"], inp["key"])
                )

    actions = recipe["actions"]
    for ak in ("back_page", "primary_label", "primary_page"):
        if ak not in actions:
            raise ValueError("actions missing required key: " + ak)






def _state_key(prefix, key):
    """Return the fully-qualified session-state key."""
    return prefix + "_" + key


def _init_defaults(recipe):
    """Write default values into session state. Safe to call every rerun."""
    prefix = recipe["prefix"]
    defaults = recipe.get("defaults", {})
    for suffix, value in defaults.items():
        full = _state_key(prefix, suffix)
        if full not in st.session_state:
            st.session_state[full] = value


def _get(prefix, key, fallback=None):
    """Read a session-state value by its short key."""
    return st.session_state.get(_state_key(prefix, key), fallback)


def _set(prefix, key, value):
    """Write a session-state value by its short key."""
    st.session_state[_state_key(prefix, key)] = value


def _reset_group_defaults(recipe, group, gen):
    """
    Handle the Foundation 'Default' button.

    When pressed, this writes the group's 'defaults' dict into
    session state, bumps the generation counter, and reruns.

    The generation counter forces Streamlit to recreate the
    widgets under new keys, so the user sees the new values.

    Must be called BEFORE the group's widgets are drawn.
    """
    prefix = recipe["prefix"]
    defaults = group.get("defaults", None)
    if not defaults:
        return gen

    button_key = prefix + "_" + group["key"] + "_default"
    if st.button("Default", key=button_key):
        for suffix, value in defaults.items():
            _set(prefix, suffix, value)
        st.session_state[prefix + "_found_widget_generation"] = gen + 1
        st.rerun()

    return gen


def _gen_suffix(recipe, gen):
    """
    Return the widget-key suffix that changes with the generation
    counter. Only the Foundation group's widgets use this, so that
    a Default press actually refreshes them.

    Returns an empty string if no gen counter is active, so other
    groups are unaffected.
    """
    return "_g" + str(gen)






def _draw_number(recipe, inp, gen_suffix):
    """Draw a number input. Writes to session state on change."""
    prefix = recipe["prefix"]
    suffix = inp["key"]
    full = _state_key(prefix, suffix)
    widget_key = full + "_input" + gen_suffix
    current = st.session_state.get(full, inp.get("default", 0.0))
    value = st.number_input(
        inp["label"],
        min_value=float(inp.get("min", 0.0)),
        max_value=float(inp.get("max", 1e9)),
        value=float(current),
        step=float(inp.get("step", 1.0)),
        key=widget_key,
        help=inp.get("help", None),
    )
    _set(prefix, suffix, value)
    return value


def _draw_integer(recipe, inp, gen_suffix):
    """Draw an integer input. Writes to session state on change."""
    prefix = recipe["prefix"]
    suffix = inp["key"]
    full = _state_key(prefix, suffix)
    widget_key = full + "_input" + gen_suffix
    current = st.session_state.get(full, inp.get("default", 0))
    value = st.number_input(
        inp["label"],
        min_value=int(inp.get("min", 0)),
        max_value=int(inp.get("max", 10**6)),
        value=int(current),
        step=int(inp.get("step", 1)),
        key=widget_key,
        help=inp.get("help", None),
    )
    _set(prefix, suffix, value)
    return value


def _draw_dropdown(recipe, inp, gen_suffix):
    """Draw a selectbox. Options are [value, label] pairs."""
    prefix = recipe["prefix"]
    suffix = inp["key"]
    full = _state_key(prefix, suffix)
    widget_key = full + "_select" + gen_suffix
    options = inp.get("options", [])
    values = [o[0] for o in options]
    labels = [o[1] for o in options]
    current = st.session_state.get(full, inp.get("default", values[0]))
    if current not in values:
        current = values[0]
    idx = values.index(current)
    choice_label = st.selectbox(
        inp["label"],
        labels,
        index=idx,
        key=widget_key,
        help=inp.get("help", None),
    )
    choice = values[labels.index(choice_label)]
    _set(prefix, suffix, choice)
    return choice


def _draw_radio(recipe, inp, gen_suffix):
    """Draw a radio. Options are [value, label] pairs."""
    prefix = recipe["prefix"]
    suffix = inp["key"]
    full = _state_key(prefix, suffix)
    widget_key = full + "_radio" + gen_suffix
    options = inp.get("options", [])
    values = [o[0] for o in options]
    labels = [o[1] for o in options]
    current = st.session_state.get(full, inp.get("default", values[0]))
    if current not in values:
        current = values[0]
    idx = values.index(current)
    choice_label = st.radio(
        inp["label"],
        labels,
        index=idx,
        key=widget_key,
        help=inp.get("help", None),
    )
    choice = values[labels.index(choice_label)]
    _set(prefix, suffix, choice)
    return choice


def _draw_toggle(recipe, inp, gen_suffix):
    """Draw an on/off toggle. Options: [label_off, label_on]."""
    prefix = recipe["prefix"]
    suffix = inp["key"]
    full = _state_key(prefix, suffix)
    widget_key = full + "_toggle" + gen_suffix
    current = bool(st.session_state.get(full, inp.get("default", False)))
    labels = inp.get("options", ["Off", "On"])
    value = st.toggle(
        inp["label"],
        value=current,
        key=widget_key,
        help=inp.get("help", None),
    )
    _set(prefix, suffix, value)
    return value


def _draw_input(recipe, inp, gen_suffix):
    """Dispatch to the correct drawer based on inp['type']."""
    t = inp["type"]
    if t == "number":
        return _draw_number(recipe, inp, gen_suffix)
    if t == "integer":
        return _draw_integer(recipe, inp, gen_suffix)
    if t == "dropdown":
        return _draw_dropdown(recipe, inp, gen_suffix)
    if t == "radio":
        return _draw_radio(recipe, inp, gen_suffix)
    if t == "toggle":
        return _draw_toggle(recipe, inp, gen_suffix)
    raise ValueError("unknown input type: " + t)






def _input_is_visible(recipe, inp):
    """Return True if the input should be drawn."""
    show_if = inp.get("show_if", None)
    if show_if is None:
        return True
    try:
        return bool(show_if(st.session_state, recipe["prefix"]))
    except Exception:
        return True


def _draw_group(recipe, group, gen, gen_suffix):
    """Draw one accordion group with its inputs and boxes."""
    prefix = recipe["prefix"]
    gname = group["name"]
    ghelp = group.get("help", "")

    expand_this = group.get("expanded", False)

    with st.expander(gname, expanded=expand_this):
        section_header(gname, ghelp)

        # Foundation group: draw Default button first, refresh gen.
        if group.get("defaults", None):
            gen = _reset_group_defaults(recipe, group, gen)
            gen_suffix = _gen_suffix(recipe, gen)

        # Draw inputs two per row for numeric types, one for others.
        numeric_buffer = []
        for inp in group["inputs"]:
            if not _input_is_visible(recipe, inp):
                continue
            if inp["type"] in ("number", "integer"):
                numeric_buffer.append(inp)
                if len(numeric_buffer) == 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        _draw_input(recipe, numeric_buffer[0], gen_suffix)
                    with col2:
                        _draw_input(recipe, numeric_buffer[1], gen_suffix)
                    numeric_buffer = []
            else:
                if numeric_buffer:
                    col1, col2 = st.columns(2)
                    with col1:
                        _draw_input(recipe, numeric_buffer[0], gen_suffix)
                    numeric_buffer = []
                _draw_input(recipe, inp, gen_suffix)

        # Flush any odd numeric input left in the buffer.
        if numeric_buffer:
            col1, col2 = st.columns(2)
            with col1:
                _draw_input(recipe, numeric_buffer[0], gen_suffix)

        # Info box.
        info_fn = group.get("info", None)
        if info_fn is not None:
            msg = info_fn(st.session_state, prefix)
            if msg:
                info_box(msg)

        # Preview box.
        prev_fn = group.get("preview", None)
        if prev_fn is not None:
            msg = prev_fn(st.session_state, prefix)
            if msg:
                preview_box(msg)

        # Warning box.
        warn_fn = group.get("warning", None)
        if warn_fn is not None:
            msg = warn_fn(st.session_state, prefix)
            if msg:
                warning_box(msg)

    return gen






def _draw_action_buttons(recipe):
    """Draw Back and primary action buttons."""
    actions = recipe["actions"]
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button(
            "Back to Registration",
            key=recipe["prefix"] + "_back",
            use_container_width=True,
        ):
            st.session_state.page = actions["back_page"]
            st.rerun()
    with col_b:
        if st.button(
            actions["primary_label"],
            key=recipe["prefix"] + "_run",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.page = actions["primary_page"]
            st.rerun()


def render_workshop(recipe):
    """
    Render a workshop from its recipe.

    Reads the recipe. Builds the input page. Writes session state.
    Does not know any structure.

    Parameters
    ----------
    recipe : dict
        See the module header for the full recipe shape.
    """
    _validate_recipe(recipe)

    st.markdown(WORKSHOP_CSS, unsafe_allow_html=True)
    _init_defaults(recipe)

    prefix = recipe["prefix"]
    gen = int(st.session_state.get(prefix + "_found_widget_generation", 0))
    gen_suffix = _gen_suffix(recipe, gen)

    project_info = st.session_state.get("project_info", {})
    project_name = project_info.get("name", "") or "Untitled Project"
    client_name = project_info.get("client", "") or "Unknown Client"

    bc = recipe["breadcrumb"]
    render_breadcrumb(bc[0], bc[1])
    render_project_header(project_name, client_name, recipe["structure_label"])

    for group in recipe["groups"]:
        gen = _draw_group(recipe, group, gen, gen_suffix)
        gen_suffix = _gen_suffix(recipe, gen)

    viewer_fn = recipe.get("viewer_strings", None)
    if viewer_fn is not None:
        viewer_fn(st.session_state, prefix)

    _draw_action_buttons(recipe)







# =============================================================================
# END OF ui/workshops/_renderer.py
# =============================================================================
#
# This file is Step 1 of UI_ARCHITECTURE.md Part 9.
#
# It is NOT yet wired into the app. No workshop imports it yet.
# The four workshops (saddle_standard.py, saddle_frame.py,
# saddle_leaf.py, saddle_hypar.py) still run as they did before.
#
# To use it, a recipe must be written per structure and the
# workshop file must be reduced to:
#
#   from ui.workshops._renderer import render_workshop
#   from data.recipes.<structure> import WORKSHOP_RECIPE
#
#   def render_<variant>():
#       render_workshop(WORKSHOP_RECIPE)
#
# That migration is Step 2. It has not been done.
#
# Files untouched by this addition:
#   ui/workshop.py
#   core/navigation.py
#   core/state.py
#   ui/landing.py
#   ui/workshops/_shared.py
#   ui/workshops/saddle_standard.py
#   ui/workshops/saddle_frame.py
#   ui/workshops/saddle_leaf.py
#   ui/workshops/saddle_hypar.py
#   viewers/*
#
# The renderer lives in isolation until the Chief says migrate.
# =============================================================================




