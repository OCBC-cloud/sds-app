# =============================================================================
# SDSe Engine - Render Prompt Templates
# =============================================================================
# Prompt templates for external image renderers.
#
# SDSe does not generate images. It prepares a snapshot and a prompt.
# The user takes them to an external renderer (Bing Image Creator,
# Midjourney, Adobe Firefly, etc.). The result is brought back by the
# user.
#
# The prompt is short. One live shape sentence, one lighting sentence,
# one scene paragraph. The shape sentence is assembled at prompt time
# from the current workshop values, so it always matches what the user
# is looking at on screen.
#
# A word-count guard trims the prompt if it ever approaches the
# external renderer's input limit (Bing: 480 words).
#
# Legal: SDSe is not affiliated with any external renderer. See
# MARKETING_RENDER_WORKFLOW.md for the disclaimer text and design
# rationale.
# =============================================================================


# =============================================================================
# WORD LIMIT
# =============================================================================
# External renderers cap the prompt length. Bing is 480 words.
# We keep a safe margin below that.

MAX_PROMPT_WORDS = 420


# =============================================================================
# RENDERER LINKS
# =============================================================================
# Plain text names and URLs. No logos. No endorsement implied.

RENDERERS = [
    {
        "key": "bing",
        "name": "Bing Image Creator",
        "url": "https://www.bing.com/create",
        "note": "Free. No account required.",
    },
    {
        "key": "midjourney",
        "name": "Midjourney",
        "url": "https://www.midjourney.com",
        "note": "Paid subscription. Highest quality.",
    },
    {
        "key": "firefly",
        "name": "Adobe Firefly",
        "url": "https://firefly.adobe.com",
        "note": "Free tier available. Adobe account required.",
    },
]


# =============================================================================
# DISCLAIMER TEXT
# =============================================================================
# Shown in the SDSe interface below the renderer links.

DISCLAIMER = (
    "SDSe is not affiliated with any of the renderers listed above. "
    "These are third-party tools offered for your consideration. "
    "Each opens in a new browser tab. Use of any renderer is subject "
    "to that renderer's own terms of service.\n\n"
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
# Each template is a paragraph that describes the desired scene.
# A live shape sentence is prepended by format_prompt().
#
# The special "technical" scene overrides the time-of-day lighting,
# producing a plain product-shot with no location and no mood.

SCENES = {
    "technical": {
        "name": "Technical (neutral background)",
        "overrides_lighting": True,
        "scene_text": (
            "Isolated on a plain light grey studio background. No scene, "
            "no people, no landscaping. Even diffused studio lighting, "
            "no dramatic shadows. Clean product-shot rendering, sharp "
            "focus, technical catalogue style."
        ),
    },
    "garden": {
        "name": "Public Garden",
        "overrides_lighting": False,
        "scene_text": (
            "Placed in a lush public garden. Green trees, flowerbeds, "
            "stone pathways, small water feature reflecting the canopy. "
            "People walking underneath the structure. Wide-angle "
            "architectural photography, extremely detailed, shot on "
            "Canon EOS R5, 24mm lens, f/8, ISO 100."
        ),
    },
    "plaza": {
        "name": "Monumental Square",
        "overrides_lighting": False,
        "scene_text": (
            "As the centerpiece of a modern urban plaza. Surrounding "
            "plaza with stone paving, modern glass buildings in the "
            "background, pedestrians walking, city skyline visible. "
            "Wide-angle architectural photography."
        ),
    },
    "event": {
        "name": "Event Venue",
        "overrides_lighting": False,
        "scene_text": (
            "Over an elegant outdoor event space. Underneath: round "
            "tables with white linens, string lights, guests at a "
            "wedding reception. Romantic atmosphere. Shot on Canon "
            "EOS R5, 35mm lens, f/4."
        ),
    },
    "cafe": {
        "name": "Retail / Cafe",
        "overrides_lighting": False,
        "scene_text": (
            "Shading an outdoor cafe. Beneath: wooden tables, coffee "
            "cups, customers seated. Modern hospitality setting, "
            "shallow depth of field, shot on Canon EOS R5, 50mm lens, "
            "f/2.8."
        ),
    },
    "motorsport": {
        "name": "Motorsports Paddock",
        "overrides_lighting": False,
        "scene_text": (
            "Shading the pit lane canopy area of a motorsport circuit. "
            "Racing motorcycles parked beneath the structure, team crew "
            "in racing suits working on bikes, tool carts, tyre stacks, "
            "grandstands and timing tower in the background. Dramatic "
            "motorsport photography, shot on Canon EOS R5, 35mm lens, "
            "f/4."
        ),
    },
    "parade": {
        "name": "National Day Parade",
        "overrides_lighting": False,
        "scene_text": (
            "Standing on Dataran Merdeka in Kuala Lumpur during a "
            "National Day parade. Malaysian flags flying, marching "
            "contingents in formation, spectators along the streets, "
            "the Sultan Abdul Samad building in the background. "
            "Patriotic and ceremonial atmosphere, wide architectural "
            "photography, shot on Canon EOS R5, 24mm lens, f/8."
        ),
    },
    "hubei": {
        "name": "Chinese Mountain Landscape",
        "overrides_lighting": False,
        "scene_text": (
            "Set on a scenic overlook in the mountains of Hubei "
            "province, China. Mist rolling through pine trees, "
            "traditional Chinese pavilions and tiled roofs in the "
            "distance, layered mountain peaks fading into the clouds. "
            "Ink-wash painting atmosphere, serene and timeless, shot "
            "on Canon EOS R5, 50mm lens, f/5.6."
        ),
    },
    "airbase": {
        "name": "Air Force Base",
        "overrides_lighting": False,
        "scene_text": (
            "On the apron of a modern air force base. Next-generation "
            "stealth fighter jets parked beneath the structure, ground "
            "crew in flight suits, service vehicles, a control tower "
            "silhouette in the background. Military precision and "
            "scale, cinematic photography, shot on Canon EOS R5, 24mm "
            "lens, f/8."
        ),
    },
}


# =============================================================================
# TIME OF DAY PRESETS
# =============================================================================
# Independent of scene. Controls lighting, shadow direction, and mood.
# Four plain slots: Morning, Noon, Evening, Night.
#
# The "technical" scene overrides this block entirely.

TIMES = {
    "morning": {
        "name": "Morning",
        "lighting_text": (
            "Soft morning light, low warm sun rising, long shadows "
            "stretching across the ground, cool clean air, slight haze "
            "in the distance."
        ),
    },
    "noon": {
        "name": "Noon",
        "lighting_text": (
            "Bright overhead midday sun, short sharp shadows directly "
            "beneath objects, high contrast, clear visibility, "
            "saturated colours."
        ),
    },
    "evening": {
        "name": "Evening",
        "lighting_text": (
            "Warm evening light, low sun, long soft shadows, orange "
            "and pink sky, gentle warm glow on all surfaces."
        ),
    },
    "night": {
        "name": "Night",
        "lighting_text": (
            "Dark night sky, artificial lights glowing on the "
            "structure and its surroundings, deep blue ambient "
            "illumination, cinematic atmosphere."
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

    Prompt layout (four parts):
      1. Photorealistic architectural photograph of a <name>. <shape>.
      2. Lighting sentence (skipped when the scene overrides lighting).
      3. Scene paragraph.
      4. Word-count guard trims the tail if it exceeds MAX_PROMPT_WORDS.

    The shape sentence is written live from the params dict so it always
    matches the workshop values the user is currently working with.

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
        "Photorealistic architectural photograph of a " + name + ". "
        + shape
    )

    # ---- 2. Lighting (skipped when the scene overrides it)
    if scene.get("overrides_lighting", False):
        lighting = ""
    else:
        lighting = " " + time_preset["lighting_text"]

    # ---- 3. Scene
    body = " " + scene["scene_text"]

    prompt = lead + lighting + body

    # ---- 4. Word-count guard
    prompt = _enforce_word_limit(prompt)

    return prompt


# =============================================================================
# PER-VARIANT LIVE SHAPE SENTENCES
# =============================================================================
# Every shape sentence is assembled from the params dict. No hardcoded
# dimensions. No technical spec sheet. Just what a viewer's eye would
# notice.

def _describe_structure(variant_key, structure_key, params):
    """Return (name, shape_sentence) for the active variant."""

    if variant_key == "cantilever_leaf":
        return _describe_cantilever_leaf(params)
    if variant_key == "standard_saddle":
        return _describe_standard_saddle(params)
    if variant_key == "frame_supported_saddle":
        return _describe_beam_supported_saddle(params)

    # Fallback for unknown variants
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
            "A single leaf-shaped fabric canopy on a " + h_text + ", "
            "radiating outward and upward over curved steel ribs and "
            "tapering to a pointed tip."
        )
    elif arr == "double":
        shape = (
            "Two mirrored leaf-shaped fabric canopies on a " + h_text + ", "
            "radiating outward and upward over curved steel ribs."
        )
    elif arr == "multiple":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " " if n else "Multiple "
        shape = (
            n_text + "leaf-shaped fabric canopies arranged radially "
            "around a " + h_text + ", each stretched over curved steel "
            "ribs."
        )
    elif arr == "tree_stack":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " tiers" if n else "stacked tiers"
        shape = (
            "Leaf-shaped fabric canopies arranged in " + n_text + " up a "
            + h_text + ", each canopy stretched over curved steel ribs."
        )
    elif arr == "tiered_helix":
        n = params.get("num_leaves")
        n_text = str(int(n)) + " " if n else "Several "
        shape = (
            n_text + "leaf-shaped fabric canopies arranged in a helix "
            "spiralling up a " + h_text + ", each stretched over curved "
            "steel ribs."
        )
    else:
        shape = (
            "A leaf-shaped fabric canopy on a " + h_text + ", radiating "
            "outward and upward over curved steel ribs."
        )
    return name, shape


def _describe_standard_saddle(params):
    """Standard Saddle: hypar membrane between two curved edge beams."""
    name = "Standard Saddle Span tensile membrane structure"

    span = params.get("span")
    rise = params.get("rise")

    dim_phrase = ""
    if span and rise:
        dim_phrase = " " + _fmt_m(span) + " long and rising " + _fmt_m(rise) + ","
    elif span:
        dim_phrase = " " + _fmt_m(span) + " long,"
    elif rise:
        dim_phrase = " rising " + _fmt_m(rise) + ","

    shape = (
        "A hyperbolic paraboloid saddle membrane canopy" + dim_phrase + " "
        "held by two curved steel edge beams rising from two ground "
        "supports and converging toward a low point between them, "
        "stabilised by tie-down cables."
    )
    return name, shape


def _describe_beam_supported_saddle(params):
    """Beam Supported Saddle: hypar with purlins and rigid secondary beams."""
    name = "Beam Supported Saddle Span tensile membrane structure"

    span = params.get("span")
    rise = params.get("rise")

    dim_phrase = ""
    if span and rise:
        dim_phrase = " " + _fmt_m(span) + " long and rising " + _fmt_m(rise) + ","
    elif span:
        dim_phrase = " " + _fmt_m(span) + " long,"
    elif rise:
        dim_phrase = " rising " + _fmt_m(rise) + ","

    shape = (
        "A hyperbolic paraboloid saddle membrane canopy" + dim_phrase + " "
        "held by two curved steel edge beams rising from two ground "
        "supports and converging toward a low point between them, with "
        "cross purlins spanning the membrane and rigid secondary beams "
        "tying the structure down."
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


def _enforce_word_limit(text):
    """
    Trim the prompt if it exceeds MAX_PROMPT_WORDS.
    Strategy: split on sentences, drop trailing scene sentences
    until under the limit. Never truncate mid-sentence.
    """
    words = text.split()
    if len(words) <= MAX_PROMPT_WORDS:
        return text

    # Split into sentences on '. ' boundaries and reassemble, dropping
    # from the tail until under the limit.
    parts = text.split(". ")
    while len(parts) > 1 and len(" ".join(parts).split()) > MAX_PROMPT_WORDS:
        parts.pop()

    trimmed = ". ".join(parts)
    if not trimmed.endswith("."):
        trimmed += "."
    return trimmed


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
    results["leaf_has_lighting"] = "Soft morning light" in p1
    results["leaf_has_scene"] = "public garden" in p1.lower()
    results["leaf_no_spec_sheet"] = "Structure details:" not in p1
    results["leaf_no_baseplate"] = "baseplate" not in p1.lower()

    # ---- Test 2: Standard Saddle
    p2 = format_prompt(
        "plaza",
        "saddle_span",
        "standard_saddle",
        {
            "span": 10.0,
            "apex": 15.0,
            "rise": 6.2,
            "curve_type": "parabolic",
            "tiedown_count": 4,
        },
        "noon",
    )
    results["saddle_has_name"] = "Standard Saddle Span" in p2
    results["saddle_has_span"] = "10.0 m" in p2
    results["saddle_has_rise"] = "6.2 m" in p2
    results["saddle_has_hypar"] = "hyperbolic paraboloid" in p2.lower()
    results["saddle_has_ties"] = "tie-down" in p2.lower()
    results["saddle_no_leaf_words"] = (
        "leaves" not in p2.lower() and "cantilever" not in p2.lower()
    )
    results["saddle_no_spec_sheet"] = "Structure details:" not in p2

    # ---- Test 3: Beam Supported Saddle
    p3 = format_prompt(
        "event",
        "saddle_span",
        "frame_supported_saddle",
        {
            "span": 12.0,
            "rise": 7.0,
            "curve_type": "circular",
            "secondary_count": 4,
        },
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
    results["tech_no_scene_people"] = "people" not in p4.lower()

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

    # ---- Test 7: word count under limit for all scenes and times
    results["all_prompts_under_limit"] = True
    for sk in SCENES.keys():
        for tk in TIMES.keys():
            pt = format_prompt(
                sk, "saddle_span", "standard_saddle",
                {"span": 10.0, "rise": 6.2}, tk,
            )
            if len(pt.split()) > MAX_PROMPT_WORDS:
                results["all_prompts_under_limit"] = False

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





