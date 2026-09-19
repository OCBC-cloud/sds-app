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
# The prompt describes the structure in words. Each variant gets a
# per-structure description block assembled from the workshop's
# current parameter values. The scene and time of day are then
# appended.
#
# This engine is stateless. It receives structure parameters and
# returns a formatted prompt string.
#
# Legal: SDSe is not affiliated with any external renderer. See
# MARKETING_RENDER_WORKFLOW.md for the disclaimer text and design
# rationale.
# =============================================================================


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
# A structure description is prepended by format_prompt().

SCENES = {
    "garden": {
        "name": "Public Garden (golden hour)",
        "scene_text": (
            "Placed in a lush public garden at golden hour. Green trees, "
            "flowerbeds, stone pathways, small water feature reflecting the "
            "canopy. People walking underneath the structure. Warm late "
            "afternoon sunlight, soft shadows, wide-angle architectural "
            "photography, extremely detailed, shot on Canon EOS R5, 24mm "
            "lens, f/8, ISO 100."
        ),
    },
    "plaza": {
        "name": "Monumental Square (dusk)",
        "scene_text": (
            "As the centerpiece of a modern urban plaza. Surrounding plaza "
            "with stone paving, modern glass buildings in background, dusk "
            "lighting with the canopy illuminated from below, pedestrians "
            "walking, city skyline visible. Dramatic architectural "
            "photography, blue hour, wide angle."
        ),
    },
    "event": {
        "name": "Event Venue (evening)",
        "scene_text": (
            "Over an elegant outdoor event space. Underneath: round tables "
            "with white linens, string lights, guests at a wedding "
            "reception. Evening setting, warm golden lighting from the "
            "canopy, romantic atmosphere. Shot on Canon EOS R5, 35mm lens, "
            "f/4."
        ),
    },
    "cafe": {
        "name": "Retail / Cafe (daytime)",
        "scene_text": (
            "Shading an outdoor cafe. Beneath: wooden tables, coffee cups, "
            "customers seated. Sunny afternoon, dappled light through "
            "fabric, modern hospitality setting, shallow depth of field, "
            "shot on Canon EOS R5, 50mm lens, f/2.8."
        ),
    },
    "motorsport": {
        "name": "Motorsports Paddock (daytime)",
        "scene_text": (
            "Shading the pit lane canopy area of a motorsport circuit. "
            "Racing motorcycles parked beneath the structure, team crew "
            "in racing suits working on bikes, tool carts, tyre stacks, "
            "grandstands and timing tower in the background, bright "
            "daytime sunlight, dramatic motorsport photography, "
            "high detail, shot on Canon EOS R5, 35mm lens, f/4."
        ),
    },
    "parade": {
        "name": "National Day Parade (morning)",
        "scene_text": (
            "Standing on Dataran Merdeka in Kuala Lumpur during a "
            "National Day parade. Malaysian flags flying, marching "
            "contingents in formation, spectators along the streets, "
            "the Sultan Abdul Samad building and colonial architecture "
            "in the background, clear morning light, patriotic and "
            "ceremonial atmosphere, wide architectural photography, "
            "shot on Canon EOS R5, 24mm lens, f/8."
        ),
    },
    "hubei": {
        "name": "Chinese Mountain Landscape (misty morning)",
        "scene_text": (
            "Set on a scenic overlook in the mountains of Hubei "
            "province, China. Mist rolling through pine trees, "
            "traditional Chinese pavilions and tiled roofs in the "
            "distance, layered mountain peaks fading into the "
            "clouds, soft diffused morning light, ink-wash painting "
            "atmosphere, serene and timeless, shot on Canon EOS R5, "
            "50mm lens, f/5.6."
        ),
    },
    "airbase": {
        "name": "Air Force Base (sunset)",
        "scene_text": (
            "On the apron of a modern air force base at sunset. "
            "Next-generation stealth fighter jets parked beneath "
            "the structure, ground crew in flight suits, service "
            "vehicles, a control tower silhouette in the background, "
            "dramatic orange and red sky, military precision and "
            "scale, cinematic photography, shot on Canon EOS R5, "
            "24mm lens, f/8."
        ),
    },
}


# =============================================================================
# TIME OF DAY PRESETS
# =============================================================================
# Independent of scene. Controls lighting, shadow direction, and mood.
# The user picks a scene (where) and a time (when). The prompt engine
# combines them.

TIMES = {
    "morning": {
        "name": "Morning (soft light)",
        "lighting_text": (
            "Soft morning light, low warm sun in the east, long shadows "
            "stretching westward, cool clean air, slight haze in the "
            "distance, early morning atmosphere."
        ),
    },
    "midday": {
        "name": "Midday (bright overhead)",
        "lighting_text": (
            "Bright overhead midday sun, short sharp shadows directly "
            "beneath objects, high contrast, clear visibility, saturated "
            "colours, strong direct light."
        ),
    },
    "golden_hour": {
        "name": "Golden Hour (warm glow)",
        "lighting_text": (
            "Golden hour light, low warm sun, long soft shadows, orange "
            "and pink sky, gentle warm glow on all surfaces, ideal "
            "architectural photography light."
        ),
    },
    "evening": {
        "name": "Evening / Dusk (blue hour)",
        "lighting_text": (
            "Blue hour twilight, deep blue sky, artificial lights "
            "beginning to glow, soft ambient illumination, reflections "
            "on water and glass, cinematic atmosphere."
        ),
    },
}

# ============ END OF CHUNK 1 ============





# =============================================================================
# PUBLIC FUNCTION
# =============================================================================

def format_prompt(scene_key, structure_key, variant_key, params, time_key="golden_hour"):
    """
    Return a personalised prompt for the given scene, structure, and time.

    Parameters
    ----------
    scene_key : str
        One of the keys of SCENES. Falls back to "garden" if unknown.
    structure_key : str
        e.g. "cantilever", "saddle_span". Used only as a fallback name.
    variant_key : str
        e.g. "cantilever_leaf", "standard_saddle", "frame_supported_saddle".
    params : dict
        Variant-specific parameter values read from session state.
        Keys vary by variant. Missing keys are skipped.
    time_key : str
        One of the keys of TIMES. Falls back to "golden_hour" if unknown.

    Returns
    -------
    prompt : str
        A single string ready to paste into an external renderer.
    """
    scene = SCENES.get(scene_key, SCENES["garden"])
    time_preset = TIMES.get(time_key, TIMES["golden_hour"])

    # ---- Build the structure description block (variant-specific)
    structure_block = _describe_structure(variant_key, structure_key, params)

    # ---- Combine
    lighting = " " + time_preset["lighting_text"]
    body = " " + scene["scene_text"]

    return structure_block + lighting + body


# =============================================================================
# PER-VARIANT STRUCTURE DESCRIPTIONS
# =============================================================================

def _describe_structure(variant_key, structure_key, params):
    """Return the leading sentence(s) describing the structure."""

    if variant_key == "cantilever_leaf":
        return _describe_cantilever_leaf(params)
    if variant_key == "standard_saddle":
        return _describe_standard_saddle(params)
    if variant_key == "frame_supported_saddle":
        return _describe_beam_supported_saddle(params)

    # Fallback: unknown variant. Use the generic structure_key.
    name = _humanise(structure_key) if structure_key else "tensile membrane"
    return (
        "Photorealistic architectural photograph of a " + name
        + " tensile membrane structure. "
    )


def _describe_cantilever_leaf(params):
    """Cantilever Leaf: column-mounted tiered membrane leaves."""
    intro = "Photorealistic architectural photograph of a Cantilever Leaf tensile membrane structure. "
    intro += (
        "A single vertical steel column supports a set of curved cantilever "
        "leaves reaching outward, each leaf formed by a fabric membrane "
        "stretched over radial ribs, tapering to a pointed tip. "
    )

    detail_lines = []

    n_leaves = params.get("num_leaves")
    arrangement = params.get("arrangement")
    column_height = params.get("column_height")
    outreach = params.get("outreach")

    if arrangement:
        arrangement_text = _humanise(arrangement)
        if n_leaves:
            detail_lines.append(
                str(int(n_leaves)) + " leaves arranged in a "
                + arrangement_text + " configuration"
            )
        else:
            detail_lines.append(arrangement_text + " arrangement")

    if column_height:
        detail_lines.append("column height " + _fmt_m(column_height))

    if outreach:
        detail_lines.append("leaf outreach " + _fmt_m(outreach))

    if detail_lines:
        intro += "Structure details: " + ", ".join(detail_lines) + ". "

    intro += (
        "The base of the column is a visible steel baseplate with anchor "
        "bolts and a stiffened column-to-baseplate joint resting on a "
        "concrete foundation at ground level. "
    )
    return intro


def _describe_standard_saddle(params):
    """Standard Saddle: two curved edge beams with hypar membrane."""
    intro = (
        "Photorealistic architectural photograph of a Standard Saddle Span "
        "tensile membrane structure. "
    )
    intro += (
        "Two curved steel edge beams rise from opposite ground supports, "
        "converging towards a low point between them, with a fabric "
        "membrane stretched between the beams to form a classic hyperbolic "
        "paraboloid (hypar) saddle shape. Tie-down cables run from points "
        "along each beam down to ground anchors. "
    )

    detail_lines = []

    span = params.get("span")
    apex = params.get("apex")
    rise = params.get("rise")
    curve_type = params.get("curve_type")
    tie_count = params.get("tiedown_count")

    if span:
        detail_lines.append("span " + _fmt_m(span))
    if apex:
        detail_lines.append("apex-to-apex distance " + _fmt_m(apex))
    if rise:
        detail_lines.append("rise " + _fmt_m(rise))
    if curve_type:
        detail_lines.append(_humanise(curve_type) + " beam curve")
    if tie_count:
        detail_lines.append(str(int(tie_count)) + " tie-down cables")

    if detail_lines:
        intro += "Structure details: " + ", ".join(detail_lines) + ". "

    intro += (
        "Each beam end terminates at a ground support with a visible steel "
        "baseplate, anchor bolt group, and stiffened beam-to-baseplate "
        "connection resting on a concrete foundation at ground level. "
    )
    return intro


def _describe_beam_supported_saddle(params):
    """Beam Supported Saddle: two curved beams, purlins, secondary beams."""
    intro = (
        "Photorealistic architectural photograph of a Beam Supported Saddle "
        "Span tensile membrane structure. "
    )
    intro += (
        "Two curved steel edge beams rise from opposite ground supports, "
        "converging towards a low point between them, with a fabric "
        "membrane stretched between the beams to form a hyperbolic "
        "paraboloid (hypar) saddle shape. Cross purlins run across the "
        "membrane, and secondary beams tie the main beams down to ground "
        "anchor points. "
    )

    detail_lines = []

    span = params.get("span")
    apex = params.get("apex")
    rise = params.get("rise")
    curve_type = params.get("curve_type")
    secondary_count = params.get("secondary_count")

    if span:
        detail_lines.append("span " + _fmt_m(span))
    if apex:
        detail_lines.append("apex-to-apex distance " + _fmt_m(apex))
    if rise:
        detail_lines.append("rise " + _fmt_m(rise))
    if curve_type:
        detail_lines.append(_humanise(curve_type) + " beam curve")
    if secondary_count:
        detail_lines.append(
            str(int(secondary_count)) + " secondary beams per main beam"
        )

    if detail_lines:
        intro += "Structure details: " + ", ".join(detail_lines) + ". "

    intro += (
        "Each main beam end and each secondary beam terminates at a ground "
        "support with a visible steel baseplate, anchor bolt group, and "
        "stiffened connection to the baseplate resting on a concrete "
        "foundation at ground level. "
    )
    return intro


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


# =============================================================================
# SELF-TEST
# =============================================================================

def _verify_render_prompts():
    """Sanity checks on the prompt formatter."""
    results = {}

    # Test 1: Cantilever Leaf, tiered helix, with dimensions
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
        "golden_hour",
    )
    results["leaf_has_name"] = "Cantilever Leaf" in p1
    results["leaf_has_leaves"] = "6 leaves" in p1
    results["leaf_has_arrangement"] = "Tiered Helix" in p1
    results["leaf_has_column"] = "column height 10.0 m" in p1
    results["leaf_has_outreach"] = "leaf outreach 5.0 m" in p1
    results["leaf_has_baseplate"] = "baseplate" in p1.lower()
    results["leaf_has_lighting"] = "Golden hour light" in p1
    results["leaf_has_scene"] = "public garden" in p1.lower()

    # Test 2: Standard Saddle
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
        "midday",
    )
    results["saddle_has_name"] = "Standard Saddle Span" in p2
    results["saddle_has_span"] = "span 10.0 m" in p2
    results["saddle_has_apex"] = "apex-to-apex distance 15.0 m" in p2
    results["saddle_has_rise"] = "rise 6.2 m" in p2
    results["saddle_has_curve"] = "Parabolic" in p2
    results["saddle_has_ties"] = "4 tie-down cables" in p2
    results["saddle_has_hypar"] = "hypar" in p2.lower()
    results["saddle_has_baseplate"] = "baseplate" in p2.lower()
    results["saddle_has_midday"] = "overhead midday sun" in p2.lower()
    # The bug: no Cantilever-specific language should leak in.
    results["saddle_no_leaf_words"] = (
        "leaves" not in p2.lower()
        and "arrangement" not in p2.lower()
        and "cantilever" not in p2.lower()
    )

    # Test 3: Beam Supported Saddle
    p3 = format_prompt(
        "event",
        "saddle_span",
        "frame_supported_saddle",
        {
            "span": 12.0,
            "apex": 18.0,
            "rise": 7.0,
            "curve_type": "circular",
            "secondary_count": 4,
        },
        "evening",
    )
    results["beam_has_name"] = "Beam Supported Saddle Span" in p3
    results["beam_has_secondary"] = "4 secondary beams per main beam" in p3
    results["beam_has_purlins"] = "purlins" in p3.lower()
    results["beam_has_hypar"] = "hypar" in p3.lower()
    results["beam_has_baseplate"] = "baseplate" in p3.lower()
    results["beam_has_evening"] = "blue hour" in p3.lower()
    results["beam_no_leaf_words"] = (
        "leaves" not in p3.lower() and "cantilever" not in p3.lower()
    )

    # Test 4: unknown scene falls back to garden
    p4 = format_prompt(
        "unknown_scene",
        "saddle_span",
        "standard_saddle",
        {},
        "morning",
    )
    results["unknown_scene_fallback"] = "public garden" in p4.lower()

    # Test 5: unknown time falls back to golden hour
    p5 = format_prompt(
        "plaza",
        "saddle_span",
        "standard_saddle",
        {},
        "unknown_time",
    )
    results["unknown_time_fallback"] = "Golden hour light" in p5

    # Overall
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
        print("{:24s}: {}".format(k, v))
    print("-" * 70)
    print("GATE:", "PASS" if res["pass"] else "FAIL")
