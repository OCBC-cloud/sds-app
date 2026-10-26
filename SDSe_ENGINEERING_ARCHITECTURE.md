SDSe ENGINEERING ARCHITECTURE
 
Version: 2.0 (BATS / GSA Standard)
Date: 2026-10-26
Status: LOCKED
 
1. PROJECT PHILOSOPHY
 
The SDSe App is a deterministic structural engineering tool. It must follow the proven workflows of professional membrane software (BATS, Tensys, Oasys GSA).
• No AI guesswork: We do not use while loops to brute-force pretension until a solver converges.
• Failure is a valid result: If a membrane geometry cannot carry a wind load without tearing, the software must stop and report the failure. It must never silently increase the pretension to force a fake solution. 
2. THE THREE-PHASE WORKFLOW
 
PHASE 1: Geometry & Input
• The User: Enters span, apex, cones, eave height, fabric type, and Target Pretension (e.g., 2.0 kN/m).
• The System: Generates the initial mesh and defines the eave perimeter cables.
• The Rule: The user's input is the absolute law. No background pretension searching. 
PHASE 2: Form-Finding (Dynamic Relaxation)
• The Solver: engine/dynamic_relaxation.py (Membrane + Cables ONLY).
• The Action: Runs Dynamic Relaxation (DR) to pull the slack membrane into a taut 3D shape using the Target Pretension.
• Loads: loads = None (No wind, no snow).
• The Output: The exact 3D geometry of the taut roof.
• The Gate: If the solver fails to find a taut shape, it reports an error. It does not increase pretension. 
PHASE 3: Integrated Load Analysis (Dynamic Relaxation)
• The Solver: engine/dynamic_relaxation.py (Membrane + Cables + Steel Beams).
• The Action: The solver takes the Phase 2 shape. It builds the 3D steel frame (arches, ribs, rings, drops) directly into the DR loop.
• Loads: Wind (via Cp Map), Snow, Payload. Applied on top of the pretension.
• The Physics: The steel frame and membrane bend and stretch together in the same iteration. (The BATS way).
• The Output:
	1. The stretched membrane shape.
	2. Membrane stresses (checked against fabric limit).
	3. The real bending moments and shear forces in every steel member.
• The Gate: If membrane stress > fabric limit (e.g., 4.0 kN/m), STOP and report DANGER. 
PHASE 4: Auto-Sizing (GSA Design Task)
• The Solver: engine/steel_frame_sizer.py.
• The Action: The sizer reads the member forces from Phase 3. It starts with the smallest steel pipe and iterates upward until the member passes the 70% Utilization Cap.
• The Output: Final steel section sizes for Primary, Rib, Ring, Drop, and Spoke.
• The Gate: If the largest pipe in the catalogue fails, report "Oversize Required." 
PHASE 5: The Final Report
• The Data: Baseplate reactions (from Phase 3), Corner plate forces (from Phase 3 cables), Steel sizes (from Phase 4).
• The Output: The SDSe Analysis Report (PDF/Markdown). 
 
3. THE SOLVER RULES (For AI Agents)
 
If you are an AI agent working on this codebase, you are bound to these rules:
1. Never use a while loop to force convergence. If the solver fails, it fails. Report the error.
2. Never mutate user inputs to fix a solver error.
3. Dynamic Relaxation is the solver. Do not revert to Newton-Raphson for the load analysis.
4. Integrated means integrated. The steel beams must be included in the DR matrix during Phase 3. Do not use the old substructuring method.
5. No partial files. Every file provided must be complete and run with the currently committed set. 
 
Status: LOCKED. No changes to this architecture without explicit Chief approval.
