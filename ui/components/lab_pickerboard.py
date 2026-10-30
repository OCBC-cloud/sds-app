import os
import streamlit as st
import streamlit.components.v1 as components

_RELEASE = True
_COMPONENT_NAME = "lab_pickerboard"

if not _RELEASE:
    _component_func = components.declare_component(
        _COMPONENT_NAME,
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "lab_pickerboard")
    _component_func = components.declare_component(_COMPONENT_NAME, path=build_dir)

def lab_pickerboard(reach=10.0, width=10.0, active_dots=None, key=None):
    """
    Renders the new rectangular 2D pickerboard.
    """
    if active_dots is None:
        active_dots = []
        
    component_value = _component_func(
        reach=reach,
        width=width,
        active_dots=active_dots,
        key=key,
        default={"active_dots": active_dots}
    )
    return component_value
