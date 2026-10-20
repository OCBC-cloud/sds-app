# =============================================================================
# SDSe Fluid Design Studio - Universal Workshop Renderer
# =============================================================================
# History:
#   2026-10-20 - Added show_actions parameter to allow workshops to
#                draw their own action buttons at the bottom of the page.
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
        raise ValueError("recipe['breadcrumb'] must be (structure_name, variant_name)")
    for group in recipe["groups"]:
        for gk in ("key", "name", "inputs"):
            if gk not in group:
                raise ValueError("group missing required key: " + gk)
        for inp in group["inputs"]:
            for ik in ("key", "label", "type"):
                if ik not in inp:
                    raise ValueError("input missing required key: " + ik)
            if inp["type"] not in _VALID_INPUT_TYPES:
                raise ValueError("invalid input type %r for key %r" % (inp["type"], inp["key"]))
    actions = recipe["actions"]
    for ak in ("back_page", "primary_label", "primary_page"):
        if ak not in actions:
            raise ValueError("actions missing required key: " + ak)


def _state_key(prefix, key):
    return prefix + "_" + key

def _init_defaults(recipe):
    prefix = recipe["prefix"]
    defaults = recipe.get("defaults", {})
    for suffix, value in defaults.items():
        full = _state_key(prefix, suffix)
        if full not in st.session_state:
            st.session_state[full] = value

def _get(prefix, key, fallback=None):
    return st.session_state.get(_state_key(prefix, key), fallback)

def _set(prefix, key, value):
    st.session_state[_state_key(prefix, key)] = value

def _reset_group_defaults(recipe, group, gen):
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
    return "_g" + str(gen)

def _draw_number(recipe, inp, gen_suffix):
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
    show_if = inp.get("show_if", None)
    if show_if is None:
        return True
    try:
        return bool(show_if(st.session_state, recipe["prefix"]))
    except Exception:
        return True

def _draw_group(recipe, group, gen, gen_suffix):
    prefix = recipe["prefix"]
    gname = group["name"]
    ghelp = group.get("help", "")
    expand_this = group.get("expanded", False)

    with st.expander(gname, expanded=expand_this):
        section_header(gname, ghelp)
        if group.get("defaults", None):
            gen = _reset_group_defaults(recipe, group, gen)
            gen_suffix = _gen_suffix(recipe, gen)

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

        if numeric_buffer:
            col1, col2 = st.columns(2)
            with col1:
                _draw_input(recipe, numeric_buffer[0], gen_suffix)

        info_fn = group.get("info", None)
        if info_fn is not None:
            msg = info_fn(st.session_state, prefix)
            if msg:
                info_box(msg)

        prev_fn = group.get("preview", None)
        if prev_fn is not None:
            msg = prev_fn(st.session_state, prefix)
            if msg:
                preview_box(msg)

        warn_fn = group.get("warning", None)
        if warn_fn is not None:
            msg = warn_fn(st.session_state, prefix)
            if msg:
                warning_box(msg)

    return gen

def _draw_action_buttons(recipe):
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


def render_workshop(recipe, show_actions=True):
    """
    Render a workshop from its recipe.
    
    If show_actions is False, the Back and Primary buttons are NOT drawn.
    The calling workshop is then responsible for drawing them.
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

    # ---- The new conditional check ----
    if show_actions:
        _draw_action_buttons(recipe)


# =============================================================================
# END OF ui/workshops/_renderer.py
# =============================================================================
