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
# PUBLIC FUNCTION
# =============================================================================

def format_prompt(scene_key, structure_key, variant_key, params):
    """
    Return a personalised prompt for the given scene and structure.

    Parameters
    ----------
    scene_key : str
        One of: "garden", "plaza", "event", "cafe".
    structure_key : str
        e.g. "cantilever", "saddle_span".
    variant_key : str
        e.g. "cantilever_leaf", "standard_saddle".
    params : dict
        Must contain whichever of the following are available:
        column_height, outreach, num_leaves, arrangement.

    Returns
    -------
    prompt : str
        A single string ready to paste into an external renderer.
    """
    scene = SCENES.get(scene_key)
    if scene is None:
        scene = SCENES["garden"]

    # ---- Build the structure description
    structure_name = _humanise(structure_key)
    variant_name = _humanise(variant_key)

    # ---- Core structure line
    intro = (
        "Photorealistic architectural photograph of a {variant} "
        "structure ({structure})."
    ).format(variant=variant_name, structure=structure_name)

    # ---- Optional dimensions line
    dim_lines = []
    if params:
        if "num_leaves" in params and params["num_leaves"]:
            dim_lines.append(str(int(params["num_leaves"])) + " leaves")
        if "arrangement" in params and params["arrangement"]:
            dim_lines.append(_humanise(params["arrangement"]) + " arrangement")
        if "column_height" in params and params["column_height"]:
            dim_lines.append(
                "column height " + _fmt_m(params["column_height"])
            )
        if "outreach" in params and params["outreach"]:
            dim_lines.append(
                "outreach " + _fmt_m(params["outreach"])
            )

    if dim_lines:
        intro += " Structure details: " + ", ".join(dim_lines) + "."

    # ---- Scene text
    body = " " + scene["scene_text"]

    return intro + body


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

    # Test 1: garden scene, cantilever leaf, with dimensions
    p = format_prompt(
        "garden",
        "cantilever",
        "cantilever_leaf",
        {
            "num_leaves": 6,
            "arrangement": "tiered_helix",
            "column_height": 4.0,
            "outreach": 5.0,
        },
    )
    results["has_variant"] = "Cantilever Leaf" in p
    results["has_leaves"] = "6 leaves" in p
    results["has_arrangement"] = "Tiered Helix arrangement" in p
    results["has_column"] = "column height 4.0 m" in p
    results["has_outreach"] = "outreach 5.0 m" in p
    results["has_scene"] = "public garden" in p.lower()

    # Test 2: unknown scene falls back to garden
    p2 = format_prompt(
        "unknown_scene",
        "saddle_span",
        "standard_saddle",
        {},
    )
    results["unknown_fallback"] = "public garden" in p2.lower()
    results["saddle_ok"] = "Saddle Span" in p2

    # Test 3: no params - no dimensions line
    p3 = format_prompt("plaza", "cantilever", "cantilever_leaf", {})
    results["no_params"] = "Structure details:" not in p3

    # Test 4: partial params
    p4 = format_prompt(
        "event",
        "cantilever",
        "cantilever_leaf",
        {"num_leaves": 4},
    )
    results["partial"] = "4 leaves" in p4

    # Overall
    results["pass"] = all([
        results["has_variant"],
        results["has_leaves"],
        results["has_arrangement"],
        results["has_column"],
        results["has_outreach"],
        results["has_scene"],
        results["unknown_fallback"],
        results["saddle_ok"],
        results["no_params"],
        results["partial"],
    ])
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
