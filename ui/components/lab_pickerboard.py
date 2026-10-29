import os
import streamlit as st
import streamlit.components.v1 as components

# Locate the HTML file relative to this python file
_RELEASE = True
_COMPONENT_NAME = "pickerboard"

if not _RELEASE:
    _component_func = components.declare_component(
        _COMPONENT_NAME,
        url="http://localhost:3001", # for local dev if needed
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "pickerboard")
    _component_func = components.declare_component(_COMPONENT_NAME, path=build_dir)

def lab_pickerboard(shape="leaf", reach=10.0, width=10.0, rib_reach=5.0, rib_lengths=None, key=None):
    """
    Renders the 2D pickerboard and returns the component value (e.g., selected rib tips).
    """
    if rib_lengths is None:
        rib_lengths = []
        
    component_value = _component_func(
        shape=shape,
        reach=reach,
        width=width,
        rib_reach=rib_reach,
        rib_lengths=rib_lengths,
        key=key,
        default={"rib_lengths": rib_lengths}
    )
    return component_value
