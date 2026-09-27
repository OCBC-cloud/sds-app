# =============================================================================
# SDSe Engine - Render Prompt Templates
# =============================================================================
# Prompt templates for the external image renderer.
#
# SDSe does not generate images. It prepares a snapshot and a prompt.
# The user takes them to an external renderer (Google Gemini). The
# result is brought back by the user.
#
# Prompt layout (three parts):
#   1. Structure name + live shape sentence (assembled from params,
#      with explicit scale, materials, and a human figure for size).
#   2. Lighting sentence (from TIMES, unless the scene overrides it).
#   3. Scene paragraph (from SCENES, with human figures where the
#      scene is a real-world setting).
#
# The prompt is capped at MAX_PROMPT_CHARS characters. Gemini has no
# short input limit, so we allow a richer prompt than the old Bing
# version.
#
# Legal: SDSe is not affiliated with any external renderer. See
# MARKETING_RENDER_WORKFLOW.md for the disclaimer text and design
# rationale.
#
# Updated 2026-09-27:
#   - Switched renderer list from Bing/Midjourney/Firefly to Gemini.
#   - Raised MAX_PROMPT_CHARS from 440 to 1200.
#   - Prompt now includes explicit scale, materials, and a human
#     figure for scale.
# =============================================================================


# =============================================================================
# CHARACTER LIMIT
# =============================================================================
# Gemini has no short prompt cap. We allow a rich prompt but keep it
# focused so the AI concentrates on the structure.

MAX_PROMPT_CHARS = 1200


# =============================================================================
# RENDERER
# =============================================================================
# Single renderer. Gemini. Plain text name and URL. No logos.

RENDERERS = [
    {
        "key": "gemini",
        "name": "Google Gemini",
        "url": "https://gemini.google.com",
        "note": (
            "Tap to open Gemini in a new tab. Then: (1) upload your "
            "3D screenshot, (2) paste this prompt, (3) add the line "
            "\"Generate a photorealistic image based on this "
            "description and the attached image.\" and send."
        ),
    },
]


# =============================================================================
# DISCLAIMER TEXT
# =============================================================================
# Shown in the SDSe interface below the renderer button.

DISCLAIMER = (
    "SDSe is not affiliated with Google Gemini. It is a third-party "
    "tool offered for your consideration. It opens in a new browser "
    "tab. Use of Gemini is subject to Google's own terms of service.\n\n"
    "Before using any rendered image for commercial purposes, please "
    "check the terms of the renderer you used. Not all renderers "
    "permit commercial use of generated images.\n\n"
    "AI-generated images may have uncertain copyright status. "
    "Consult a legal professional before using them in commercial "
    "material."
)


# =============================================================================
# SCENE TEMPLATES
# =============================================================================
# Each scene is a short paragraph. The special "technical" scene
# overrides the time-of-day lighting, producing a plain product-shot.
# No camera/lens specs. No mood poetry. Only what the renderer can draw.
#
# Where the scene is a real-world setting, human figures are added for
# scale.

SCENES = {
    "technical": {
        "name": "Technical (neutral background)",
        "overrides_lighting": True,
        "scene_text": (
            "Isolated on a plain light grey studio background, no scene, "
            "no people. Even diffused lighting, clean product-shot "
            "rendering."
        ),
    },
    "garden": {
        "name": "Public Garden",
        "overrides_lighting": False,
        "scene_text": (
            "Placed in a lush public garden with flowerbeds, stone "
            "pathways, and a reflective water feature. Adults "
            "approximately 1.8 metres tall walk underneath the "
            "structure, providing human scale."
        ),
    },
    "plaza": {
        "name": "Monumental Square",
        "overrides_lighting": False,
        "scene_text": (
            "At the centerpiece of a modern urban plaza with stone "
            "paving and glass buildings in the background. Adults "
            "approximately 1.8 metres tall walk nearby, providing "
            "human scale."
        ),
    },
    "event": {
        "name": "Event Venue",
        "overrides_lighting": False,
        "scene_text": (
            "Over an outdoor event space with round tables, white "
            "linens, and string lights. Guests approximately 1.8 "
            "metres tall stand at a reception, providing human scale."
        ),
    },
    "cafe": {
        "name": "Retail / Cafe",
        "overrides_lighting": False,
        "scene_text": (
            "Shading an outdoor cafe with wooden tables and coffee "
            "cups. Adults approximately 1.8 metres tall sit beneath "
            "the structure, providing human scale."
        ),
    },
    "motorsport": {
        "name": "Motorsports Paddock",
        "overrides_lighting": False,
        "scene_text": (
            "Shading the pit lane of a motorsport circuit. Racing "
            "motorcycles parked beneath the structure. Team crew "
            "approximately 1.8 metres tall work on the bikes, "
            "providing human scale."
        ),
    },
    "parade": {
        "name": "National Day Parade",
        "overrides_lighting": False,
        "scene_text": (
            "Standing on Dataran Merdeka in Kuala Lumpur during a "
            "National Day parade. Malaysian flags, marching "
            "contingents of adults approximately 1.8 metres tall, "
            "and the Sultan Abdul Samad building behind. The human "
            "figures provide scale."
        ),
    },
    "hubei": {
        "name": "Chinese Mountain Landscape",
        "overrides_lighting": False,
        "scene_text": (
            "On a scenic overlook in the mountains of Hubei province, "
            "China. Pine trees, mist, and traditional pavilions in "
            "the distance. A few adults approximately 1.8 metres "
            "tall stand nearby, providing human scale."
        ),
    },
    "airbase": {
        "name": "Air Force Base",
        "overrides_lighting": False,
        "scene_text": (
            "On the apron of a modern air force base. Stealth fighter "
            "jets parked beneath the structure. Ground crew "
            "approximately 1.8 metres tall work nearby, providing "
            "human scale."
        ),
    },
}


# =============================================================================
# TIME OF DAY PRESETS
# =============================================================================
# Independent of scene. One short lighting sentence each.

TIMES = {
    "morning": {
        "name": "Morning",
        "lighting_text": (
            "Soft morning light, low warm sun, long shadows on the ground."
        ),
    },
    "noon": {
        "name": "Noon",
        "lighting_text": (
            "Bright overhead midday sun, short sharp shadows, high contrast."
        ),
    },
    "evening": {
        "name": "Evening",
        "lighting_text": (
            "Warm evening light, low sun, long soft shadows, orange sky."
        ),
    },
    "night": {
        "name": "Night",
        "lighting_text": (
            "Dark night sky, artificial lights glowing on the structure."
        ),
    },
}


# ============ END OF CHUNK 1 ============





# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def format_prompt(scene_key, structure_key, variant_key, params, time_key="evening"):
    """
    Return a personalised prompt for the given scene, structure, and time.

    Prompt layout:
      1. Photorealistic architectural photograph of a <name>. <shape>.
      2. Lighting sentence (skipped when the scene overrides lighting).
      3. Scene paragraph.

    Capped at MAX_PROMPT_CHARS characters.

    Parameters
    ----------
    scene_key : str
        One of the keys of SCENES. Falls back to "technical".
    structure_key : str
        Fallback name if variant_key is unknown.
    variant_key : str
        "cantilever_leaf", "standard_saddle", "frame_supported_saddle".
    params : dict
        Variant-specific workshop values.
    time_key : str
        One of the keys of TIMES. Falls back to "evening".

    Returns
    -------
    prompt : str
        A single string ready to paste into an external renderer.
    """
    scene = SCENES.get(scene_key, SCENES["technical"])
    time_preset = TIMES.get(time_key, TIMES["evening"])

    # ---- 1. Structure name + live shape sentence
    name, shape = _describe_structure(variant_key, structure_key, params)
    lead = (
        "Photorealistic architectural photograph of a "
        + name + ". " + shape
    )

    # ---- 2. Lighting (skipped when the scene overrides it)
    if scene.get("overrides_lighting", False):
        lighting = ""
    else:
        lighting = " " + time_preset["lighting_text"]

    # ---- 3. Scene
    body = " " + scene["scene_text"]

    prompt = lead + lighting + body

    # ---- 4. Character guard
    prompt = _enforce_char_limit(prompt)

    return prompt


# =============================================================================
# PER-VARIANT LIVE SHAPE SENTENCES
# =============================================================================
# Every shape sentence is assembled from the params dict. No hardcoded
# dimensions. Only what a viewer's eye would notice, plus explicit
# materials and a scale reference so an AI renderer knows the size.

# ---- Standard material specs (until the UI adds material selection).
_MEMBRANE_SPEC = (
    "white Ferrari Precontraint 702 PVC-polyester fabric, prestressed "
    "at 1.5 kN/m in each direction"
)
_STEEL_SPEC = (
    "200 mm diameter circular hollow steel section, galvanised"
)


def _describe_structure(variant_key, structure_key, params):
    """Return (name, shape_sentence) for the active variant."""

    if variant_key == "cantilever_leaf":
        return _describe_cantilever_leaf(params)
    if variant_key == "standard_saddle":
        return _describe_standard_saddle(params)
    if variant_key == "frame_supported_saddle":
        return _describe_beam_supported_saddle(params)

    name = (
        _humanise(structure_key) + " tensile membrane structure"
        if structure_key
        else "tensile membrane structure"
    )
    return name, "A tensile membrane canopy."


def _describe_cantilever_leaf(params):
    """Cantilever Leaf: column with one or more leaf-shaped canopies."""
    name = "Cantilever Leaf tensile membrane structure"

    arr = params.get("arrangement") or "single"
    h = params.get("column_height")
    h_text = _fmt_m(h) + " tall column" if h else "vertical column"

    material_phrase = (
        " The membrane is " + _MEMBRANE_SPEC
        + ", stretched over " + _STEEL_SPEC + " ribs."
    )

    if arr == "single":
        shape = (
            "A single leaf-shaped fabric canopy on a " + h_text
            + ", radiating outward and upward over curved steel ribs "
            "and tapering to a pointed tip." + material_phrase
        )
    elif arr == "double":
        shape = (
            "Two mirrored leaf-shaped fabric canopies on a " + h_text
            + ", radiating outward and upward over curved steel ribs."
            + material_phrase
        )
    elif arr == "multiple":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " " if n else "Multiple "
        shape = (
            n_text + "leaf-shaped fabric canopies arranged radially "
            "around a " + h_text + ", each stretched over curved "
            "steel ribs." + material_phrase
        )
    elif arr == "tree_stack":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " tiers" if n else "stacked tiers"
        shape = (
            "Leaf-shaped fabric canopies arranged in " + n_text
            + " up a " + h_text + ", each canopy stretched over "
            "curved steel ribs." + material_phrase
        )
    elif arr == "tiered_helix":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " " if n else "Several "
        shape = (
            n_text + "leaf-shaped fabric canopies arranged in a "
            "helix spiralling up a " + h_text + ", each stretched "
            "over curved steel ribs." + material_phrase
        )
    else:
        shape = (
            "A leaf-shaped fabric canopy on a " + h_text
            + ", radiating outward and upward over curved steel ribs."
            + material_phrase
        )
    return name, shape


def _describe_standard_saddle(params):
    """Standard Saddle: hypar membrane between two curved edge beams."""
    name = "Standard Saddle Span tensile membrane structure"

    span = params.get("span")
    rise = params.get("rise")

    dim_phrase = ""
    if span and rise:
        dim_phrase = (
            " spanning " + _fmt_m(span) + " and rising " + _fmt_m(rise)
            + " above ground,"
        )
    elif span:
        dim_phrase = " spanning " + _fmt_m(span) + ","
    elif rise:
        dim_phrase = " rising " + _fmt_m(rise) + " above ground,"

    shape = (
        "A hyperbolic paraboloid saddle membrane canopy" + dim_phrase
        + " held taut by two curved steel edge beams anchored at "
        "ground level, and stabilised by steel tie-down cables. "
        "The membrane is " + _MEMBRANE_SPEC + ". The steel is "
        + _STEEL_SPEC + "."
    )
    return name, shape


def _describe_beam_supported_saddle(params):
    """Beam Supported Saddle: hypar with purlins and rigid secondary beams."""
    name = "Beam Supported Saddle Span tensile membrane structure"

    span = params.get("span")
    rise = params.get("rise")

    dim_phrase = ""
    if span and rise:
        dim_phrase = (
            " spanning " + _fmt_m(span) + " and rising " + _fmt_m(rise)
            + " above ground,"
        )
    elif span:
        dim_phrase = " spanning " + _fmt_m(span) + ","
    elif rise:
        dim_phrase = " rising " + _fmt_m(rise) + " above ground,"

    shape = (
        "A hyperbolic paraboloid saddle membrane canopy" + dim_phrase
        + " held taut by two curved steel edge beams anchored at "
        "ground level, with cross purlins spanning the membrane and "
        "rigid secondary beams tying the structure down. "
        "The membrane is " + _MEMBRANE_SPEC + ". The steel is "
        + _STEEL_SPEC + "."
    )
    return name, shape


# =============================================================================
# HELPERS
# =============================================================================

def _humanise(s):
    """Convert a snake_case key to Title Case."""
    if not s:
        return ""
    return " ".join(w.capitalize() for w in str(s).split("_"))


def _fmt_m(value):
    """Format a length in metres with 1 decimal."""
    try:
        return ("%.1f m" % float(value))
    except (TypeError, ValueError):
        return str(value)


def _enforce_char_limit(text):
    """
    Trim the prompt if it exceeds MAX_PROMPT_CHARS.
    Splits into sentences and drops trailing ones until under the limit.
    Never truncates mid-sentence. Adds a period if the last one is lost.
    """
    if len(text) <= MAX_PROMPT_CHARS:
        return text

    parts = text.split(". ")
    while len(parts) > 1 and len(". ".join(parts)) > MAX_PROMPT_CHARS:
        parts.pop()

    trimmed = ". ".join(parts)
    if not trimmed.endswith("."):
        trimmed += "."
    return trimmed


# ============ END OF CHUNK 2 ============





# =============================================================================
# SELF-TEST
# =============================================================================

def _verify_render_prompts():
    """Sanity checks on the prompt formatter."""
    results = {}

    # ---- Test 1: Cantilever Leaf, tiered helix
    p1 = format_prompt(
        "garden",
        "cantilever",
        "cantilever_leaf",
        {
            "num_leaves": 6,
            "arrangement": "tiered_helix",
            "column_height": 10.0,
            "outreach": 5.0,
        },
        "morning",
    )
    results["leaf_has_name"] = "Cantilever Leaf" in p1
    results["leaf_has_column"] = "10.0 m" in p1
    results["leaf_has_arrangement"] = "helix" in p1.lower()
    results["leaf_has_membrane_spec"] = "Precontraint 702" in p1
    results["leaf_has_steel_spec"] = "circular hollow steel" in p1.lower()
    results["leaf_has_human_scale"] = "1.8 metres" in p1
    results["leaf_has_lighting"] = "Soft morning light" in p1
    results["leaf_has_scene"] = "public garden" in p1.lower()

    # ---- Test 2: Standard Saddle
    p2 = format_prompt(
        "plaza",
        "saddle_span",
        "standard_saddle",
        {"span": 10.0, "rise": 6.2},
        "noon",
    )
    results["saddle_has_name"] = "Standard Saddle Span" in p2
    results["saddle_has_span"] = "10.0 m" in p2
    results["saddle_has_rise"] = "6.2 m" in p2
    results["saddle_has_hypar"] = "hyperbolic paraboloid" in p2.lower()
    results["saddle_has_ties"] = "tie-down" in p2.lower()
    results["saddle_has_membrane_spec"] = "Precontraint 702" in p2
    results["saddle_has_steel_spec"] = "circular hollow steel" in p2.lower()
    results["saddle_has_human_scale"] = "1.8 metres" in p2
    results["saddle_no_leaf_words"] = (
        "leaves" not in p2.lower() and "cantilever" not in p2.lower()
    )

    # ---- Test 3: Beam Supported Saddle
    p3 = format_prompt(
        "event",
        "saddle_span",
        "frame_supported_saddle",
        {"span": 12.0, "rise": 7.0},
        "evening",
    )
    results["beam_has_name"] = "Beam Supported Saddle Span" in p3
    results["beam_has_span"] = "12.0 m" in p3
    results["beam_has_purlins"] = "purlins" in p3.lower()
    results["beam_has_secondary"] = "secondary beams" in p3.lower()
    results["beam_has_evening"] = "Warm evening light" in p3

    # ---- Test 4: Technical scene overrides lighting
    p4 = format_prompt(
        "technical",
        "saddle_span",
        "standard_saddle",
        {"span": 10.0, "rise": 6.2},
        "night",
    )
    results["tech_no_night_lighting"] = "Dark night sky" not in p4
    results["tech_has_studio"] = "studio background" in p4.lower()
    results["tech_no_people"] = "people" not in p4.lower()

    # ---- Test 5: unknown scene falls back to technical
    p5 = format_prompt(
        "unknown_scene",
        "saddle_span",
        "standard_saddle",
        {},
        "morning",
    )
    results["unknown_scene_fallback"] = "studio background" in p5.lower()

    # ---- Test 6: unknown time falls back to evening
    p6 = format_prompt(
        "plaza",
        "saddle_span",
        "standard_saddle",
        {},
        "unknown_time",
    )
    results["unknown_time_fallback"] = "Warm evening light" in p6

    # ---- Test 7: every scene/time combination stays under the character cap
    results["all_prompts_under_limit"] = True
    for sk in SCENES.keys():
        for tk in TIMES.keys():
            pt = format_prompt(
                sk, "saddle_span", "standard_saddle",
                {"span": 10.0, "rise": 6.2}, tk,
            )
            if len(pt) > MAX_PROMPT_CHARS:
                results["all_prompts_under_limit"] = False

    # ---- Test 8: RENDERERS has exactly one entry, and it is Gemini
    results["renderers_single"] = len(RENDERERS) == 1
    results["renderers_is_gemini"] = (
        RENDERERS[0]["key"] == "gemini"
        and "gemini.google.com" in RENDERERS[0]["url"]
    )

    # ---- Test 9: MAX_PROMPT_CHARS is 1200
    results["char_limit_ok"] = MAX_PROMPT_CHARS == 1200

    # ---- Overall
    results["pass"] = all(v for k, v in results.items() if k != "pass")
    return results


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("engine/render_prompts.py - render prompt templates")
    print("-" * 70)
    res = _verify_render_prompts()
    for k, v in res.items():
        print("{:28s}: {}".format(k, v))
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")





