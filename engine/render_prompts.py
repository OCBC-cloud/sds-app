# =============================================================================
# SDSe Engine - Render Prompt Templates
# =============================================================================
# Prompt templates for the external image renderer (Google Gemini).
#
# SDSe does not generate images. It prepares a snapshot and a prompt.
# The user takes them to Gemini. The result comes back to SDSe.
#
# Prompt layout (five parts, fixed order):
#   1. Camera phrase. Same every time. Tells the AI to render
#      architecturally, not stylised.
#   2. Structure sentence. With explicit scale in metres.
#   3. Lighting sentence (from TIMES, unless the scene overrides).
#   4. Scene sentence (from SCENES).
#   5. Human-figure-for-scale tail. Same every time (except technical).
#
# No materials. No product names. No steel sections. Confirmed by
# test: the AI renders better without them.
#
# The prompt is capped at MAX_PROMPT_CHARS. Kept short and focused.
#
# Updated 2026-09-27 (second pass):
#   - Short camera-anchored prompt confirmed to render well.
#   - Materials removed entirely from the prompt.
#   - Scene texts shortened to a single sentence each.
#   - Human-figure tail appended to every non-technical prompt.
# =============================================================================


# =============================================================================
# CHARACTER LIMIT
# =============================================================================
# Short prompts render better. We keep generous headroom but the
# prompts themselves come in at roughly 400-500 characters.

MAX_PROMPT_CHARS = 600


# =============================================================================
# RENDERER
# =============================================================================
# Single renderer. Google Gemini. Plain text name and URL.

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
# FIXED PHRASES
# =============================================================================
# The camera phrase opens every prompt. The scale tail closes every
# prompt that has people in it.

CAMERA_PHRASE = (
    "Photorealistic architectural photograph, shot on a full-frame "
    "camera with a 24mm wide-angle lens at f/8."
)

SCALE_TAIL = (
    "Adults 1.8 metres tall walking beneath provide scale."
)

SCALE_TAIL_TECHNICAL = (
    "Clean product-shot rendering, no people."
)


# =============================================================================
# SCENE TEMPLATES
# =============================================================================
# Each scene is a single short sentence. The technical scene overrides
# the time-of-day lighting, producing a plain product-shot.

SCENES = {
    "technical": {
        "name": "Technical (neutral background)",
        "overrides_lighting": True,
        "scene_text": (
            "Isolated on a plain light grey studio background, even "
            "diffused lighting, no scene."
        ),
        "no_people": True,
    },
    "garden": {
        "name": "Public Garden",
        "overrides_lighting": False,
        "scene_text": (
            "Set in a lush public garden with flowerbeds, stone "
            "pathways, and a reflective water feature."
        ),
        "no_people": False,
    },
    "plaza": {
        "name": "Monumental Square",
        "overrides_lighting": False,
        "scene_text": (
            "At the centre of a modern urban plaza with stone paving "
            "and glass buildings behind."
        ),
        "no_people": False,
    },
    "event": {
        "name": "Event Venue",
        "overrides_lighting": False,
        "scene_text": (
            "Over an outdoor event space with round tables, white "
            "linens, and string lights."
        ),
        "no_people": False,
    },
    "cafe": {
        "name": "Retail / Cafe",
        "overrides_lighting": False,
        "scene_text": (
            "Shading an outdoor cafe with wooden tables and coffee "
            "cups."
        ),
        "no_people": False,
    },
    "motorsport": {
        "name": "Motorsports Paddock",
        "overrides_lighting": False,
        "scene_text": (
            "At the pit lane of a motorsport circuit with racing "
            "motorcycles parked beneath."
        ),
        "no_people": False,
    },
    "parade": {
        "name": "National Day Parade",
        "overrides_lighting": False,
        "scene_text": (
            "On Dataran Merdeka in Kuala Lumpur during a National "
            "Day parade, with Malaysian flags and the Sultan Abdul "
            "Samad building behind."
        ),
        "no_people": False,
    },
    "hubei": {
        "name": "Chinese Mountain Landscape",
        "overrides_lighting": False,
        "scene_text": (
            "On a scenic overlook in the mountains of Hubei province, "
            "China, with pine trees, mist, and traditional pavilions "
            "in the distance."
        ),
        "no_people": False,
    },
    "airbase": {
        "name": "Air Force Base",
        "overrides_lighting": False,
        "scene_text": (
            "On the apron of a modern air force base with stealth "
            "fighter jets parked beneath."
        ),
        "no_people": False,
    },
}


# =============================================================================
# TIME OF DAY PRESETS
# =============================================================================

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


# ============ END OF RP CHUNK 1 ============





# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def format_prompt(scene_key, structure_key, variant_key, params, time_key="evening"):
    """
    Return a personalised prompt for the given scene, structure, and time.

    Prompt layout (fixed order):
      1. Camera phrase.
      2. Structure sentence with explicit scale.
      3. Lighting sentence (skipped when the scene overrides it).
      4. Scene sentence.
      5. Scale tail (human figures or product-shot).

    Capped at MAX_PROMPT_CHARS.
    """
    scene = SCENES.get(scene_key, SCENES["technical"])
    time_preset = TIMES.get(time_key, TIMES["evening"])

    # ---- 1. Camera phrase
    camera = CAMERA_PHRASE

    # ---- 2. Structure sentence
    name, shape = _describe_structure(variant_key, structure_key, params)
    structure = shape

    # ---- 3. Lighting (skipped when the scene overrides it)
    if scene.get("overrides_lighting", False):
        lighting = ""
    else:
        lighting = " " + time_preset["lighting_text"]

    # ---- 4. Scene
    body = " " + scene["scene_text"]

    # ---- 5. Scale tail
    if scene.get("no_people", False):
        tail = " " + SCALE_TAIL_TECHNICAL
    else:
        tail = " " + SCALE_TAIL

    prompt = camera + " " + structure + lighting + body + tail

    prompt = _enforce_char_limit(prompt)

    return prompt


# =============================================================================
# PER-VARIANT STRUCTURE SENTENCES
# =============================================================================
# Short. Explicit scale in metres. No materials.

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

    if arr == "single":
        shape = (
            "A leaf-shaped fabric canopy on a " + h_text + ", "
            "radiating outward and upward over curved steel ribs and "
            "tapering to a pointed tip, membrane fabric white and taut."
        )
    elif arr == "double":
        shape = (
            "Two mirrored leaf-shaped fabric canopies on a " + h_text
            + ", radiating outward and upward over curved steel ribs, "
            "membrane fabric white and taut."
        )
    elif arr == "multiple":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " " if n else "Multiple "
        shape = (
            n_text + "leaf-shaped fabric canopies arranged radially "
            "around a " + h_text + ", each stretched over curved "
            "steel ribs, membrane fabric white and taut."
        )
    elif arr == "tree_stack":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " tiers" if n else "stacked tiers"
        shape = (
            "Leaf-shaped fabric canopies arranged in " + n_text
            + " up a " + h_text + ", each canopy stretched over "
            "curved steel ribs, membrane fabric white and taut."
        )
    elif arr == "tiered_helix":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " " if n else "Several "
        shape = (
            n_text + "leaf-shaped fabric canopies arranged in a "
            "helix spiralling up a " + h_text + ", each stretched "
            "over curved steel ribs, membrane fabric white and taut."
        )
    else:
        shape = (
            "A leaf-shaped fabric canopy on a " + h_text
            + ", radiating outward and upward over curved steel ribs, "
            "membrane fabric white and taut."
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
            " spanning " + _fmt_m(span) + ", rising " + _fmt_m(rise) + ","
        )
    elif span:
        dim_phrase = " spanning " + _fmt_m(span) + ","
    elif rise:
        dim_phrase = " rising " + _fmt_m(rise) + ","

    shape = (
        "A hyperbolic paraboloid saddle membrane canopy" + dim_phrase
        + " held taut by two curved steel edge beams and steel "
        "tie-down cables, membrane fabric white and taut."
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
            " spanning " + _fmt_m(span) + ", rising " + _fmt_m(rise) + ","
        )
    elif span:
        dim_phrase = " spanning " + _fmt_m(span) + ","
    elif rise:
        dim_phrase = " rising " + _fmt_m(rise) + ","

    shape = (
        "A hyperbolic paraboloid saddle membrane canopy" + dim_phrase
        + " held taut by two curved steel edge beams with cross "
        "purlins and rigid secondary beams, membrane fabric white "
        "and taut."
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
    """Format a length in metres with 1 decimal, without the unit."""
    try:
        v = float(value)
        # Use whole numbers if the value is effectively integer.
        if abs(v - round(v)) < 0.05:
            return str(int(round(v)))
        return ("%.1f" % v)
    except (TypeError, ValueError):
        return str(value)


def _enforce_char_limit(text):
    """
    Trim the prompt if it exceeds MAX_PROMPT_CHARS.
    Splits into sentences and drops trailing ones until under the limit.
    Never truncates mid-sentence.
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


# ============ END OF RP CHUNK 2 ============





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
    results["leaf_has_camera"] = "shot on a full-frame camera" in p1
    results["leaf_has_name_word"] = "leaf-shaped" in p1.lower()
    results["leaf_has_helix"] = "helix" in p1.lower()
    results["leaf_has_column"] = "10" in p1
    results["leaf_has_lighting"] = "Soft morning light" in p1
    results["leaf_has_scene"] = "public garden" in p1.lower()
    results["leaf_has_scale_tail"] = "1.8 metres" in p1
    results["leaf_no_materials"] = "Precontraint" not in p1
    results["leaf_no_steel_section"] = "circular hollow" not in p1.lower()

    # ---- Test 2: Standard Saddle
    p2 = format_prompt(
        "plaza",
        "saddle_span",
        "standard_saddle",
        {"span": 10.0, "rise": 6.2},
        "noon",
    )
    results["saddle_has_camera"] = "24mm wide-angle" in p2
    results["saddle_has_hypar"] = "hyperbolic paraboloid" in p2.lower()
    results["saddle_has_span"] = "10" in p2
    results["saddle_has_rise"] = "6.2" in p2
    results["saddle_has_ties"] = "tie-down" in p2.lower()
    results["saddle_has_scene"] = "urban plaza" in p2.lower()
    results["saddle_has_scale_tail"] = "1.8 metres" in p2
    results["saddle_no_materials"] = "Precontraint" not in p2
    results["saddle_no_steel_section"] = "circular hollow" not in p2.lower()

    # ---- Test 3: Beam Supported Saddle
    p3 = format_prompt(
        "event",
        "saddle_span",
        "frame_supported_saddle",
        {"span": 12.0, "rise": 7.0},
        "evening",
    )
    results["beam_has_purlins"] = "purlins" in p3.lower()
    results["beam_has_secondary"] = "secondary beams" in p3.lower()
    results["beam_has_evening"] = "Warm evening light" in p3

    # ---- Test 4: Technical scene overrides lighting AND has no people
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
    results["tech_uses_technical_tail"] = "Clean product-shot" in p4

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

    # ---- Test 9: MAX_PROMPT_CHARS is 600
    results["char_limit_ok"] = MAX_PROMPT_CHARS == 600

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
        print("{:30s}: {}".format(k, v))
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")





