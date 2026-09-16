# 🗺️ APP MAP: sds-app Architecture
**Branch:** `modular-v10` (Primary Development Branch)
**Last Updated:** Current Session

---

## 📂 ROOT DIRECTORY
The main entry point and shared files live here.
*   `app.py` — **Main Entry Point.** Run this with `streamlit run app.py`.
*   `physics_engine.py` — Legacy math engine (check if still used by `engine/`).
*   `viewer_app.py` — Legacy 3D viewer (check if still used by `viewers/`).
*   `dxf_export.py` — CAD/DXF file exporter.
*   `run_tests.py` — Test suite.
*   `requirements.txt` — Python dependencies.
*   `README.md` / `README_M...` — Documentation.

---

## 📂 /core/
*(Purpose not yet mapped. Likely core data models or session state.)*

---

## 📂 /data/
*(Structural Data & Definitions)*
*   `__init__.py`
*   `constants.py` — Global constants (gravity, units, etc.)
*   `materials.py` — Material properties (steel, concrete, etc.)
*   `sections.py` — Cross-section definitions (I-beams, tubes, etc.)
*   **`structures.py`** — ⭐ **CRITICAL FILE:** Structural definitions (Column, Baseplate, Main Beam, Curved Strut).

---

## 📂 /engine/
*(The Mathematical & Physics Engine)*
*   `__init__.py`
*   `SPEC_saddle_sp...` — Specification document (unknown full name).
*   **`membrane.py`** — ⭐ **CRITICAL FILE:** Geometry generation math.

---

## 📂 /ui/
*(Streamlit User Interface)*
*   `__init__.py`
*   `landing.py` — Landing page.
*   `registration.py` — User registration.
*   `studio.py` — ⭐ **LIKELY CRITICAL:** Main design studio/controls.
*   `results.py` — Results display page.
*   `workshop.py` — Workshop/collaboration page.
*   `workshops/` (folder)
*   `rooms/` (folder)

---

## 📂 /viewers/
*(3D Visualization)*
*   `__init__.py`
*   **`results_viewer.py`** — ⭐ **CRITICAL FILE:** Plotly 3D rendering logic.
*   `figures/` (folder) — Saved figure outputs.

---

## 🎯 NEXT SESSION PRIORITIES
1.  **Read `data/structures.py`** — Understand how nodes/beams are currently defined.
2.  **Read `engine/membrane.py`** — Understand how geometry is generated.
3.  **Inject "Spiral Rocket" logic** into these two files.
4.  **Verify `viewers/results_viewer.py`** pulls nodes from the updated `structures.py`.

**Signing off.** 💤🛠️
