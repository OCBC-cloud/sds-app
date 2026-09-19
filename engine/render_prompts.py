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
# This engine is stateless. It receives a scene and a time of day and
# returns a formatted prompt string. The structure itself is not
# described in the prompt: the workshop writes its own description and
# dimensions string, which the results page displays under the 3D
# viewer. The external renderer reads the structure from the snapshot.
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
# The structure itself is not described here: the renderer reads it
# from the attached snapshot.

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

def format_prompt(scene_key, structure_key, variant_key, time_key="golden_hour"):
    """
    Return a personalised prompt for the given scene and time of day.

    The structure itself is not described. The workshop writes its own
    description and dimensions string, and the results page displays
    them under the 3D viewer. The user screenshots the viewer and the
    two lines together. The external renderer reads the structure and
    its dimensions from the attached image.

    Parameters
    ----------
    scene_key : str
        One of the keys of SCENES. Falls back to "garden" if unknown.
    structure_key : str
        Kept for future logging. Not injected into the prompt.
    variant_key : str
        Kept for future logging. Not injected into the prompt.
    time_key : str
        One of the keys of TIMES. Falls back to "golden_hour" if unknown.

    Returns
    -------
    prompt : str
        A single string ready to paste into an external renderer.
    """
    scene = SCENES.get(scene_key, SCENES["garden"])
    time_preset = TIMES.get(time_key, TIMES["golden_hour"])

    intro = (
        "Photorealistic architectural photograph. "
        "The attached reference image shows the structure and its "
        "dimensions."
    )

    lighting = " " + time_preset["lighting_text"]
    body = " " + scene["scene_text"]

    return intro + lighting + body


# =============================================================================
# SELF-TEST
# =============================================================================

def _verify_render_prompts():
    """Sanity checks on the prompt formatter."""
    results = {}

    # Test 1: garden scene, golden hour, cantilever leaf
    p = format_prompt(
        "garden",
        "cantilever",
        "cantilever_leaf",
        "golden_hour",
    )
    results["has_reference_line"] = (
        "attached reference image shows the structure" in p
    )
    results["has_golden_hour"] = "Golden hour light" in p
    results["has_garden_scene"] = "public garden" in p.lower()
    results["no_structure_words"] = (
        "cantilever" not in p.lower()
        and "saddle" not in p.lower()
        and "leaf" not in p.lower()
    )
    results["no_dimension_words"] = (
        "leaves" not in p.lower()
        and "arrangement" not in p.lower()
    )

    # Test 2: unknown scene falls back to garden
    p2 = format_prompt(
        "unknown_scene",
        "saddle_span",
        "standard_saddle",
        "midday",
    )
    results["unknown_scene_fallback"] = "public garden" in p2.lower()
    results["has_midday"] = "overhead midday sun" in p2.lower()

    # Test 3: unknown time falls back to golden hour
    p3 = format_prompt(
        "plaza",
        "cantilever",
        "cantilever_leaf",
        "unknown_time",
    )
    results["unknown_time_fallback"] = "Golden hour light" in p3

    # Test 4: all scenes reachable
    results["all_scenes_ok"] = True
    for sk in SCENES.keys():
        pt = format_prompt(sk, "x", "y", "morning")
        if SCENES[sk]["scene_text"] not in pt:
            results["all_scenes_ok"] = False

    # Test 5: all times reachable
    results["all_times_ok"] = True
    for tk in TIMES.keys():
        pt = format_prompt("garden", "x", "y", tk)
        if TIMES[tk]["lighting_text"] not in pt:
            results["all_times_ok"] = False

    # Overall
    results["pass"] = all([
        results["has_reference_line"],
        results["has_golden_hour"],
        results["has_garden_scene"],
        results["no_structure_words"],
        results["no_dimension_words"],
        results["unknown_scene_fallback"],
        results["has_midday"],
        results["unknown_time_fallback"],
        results["all_scenes_ok"],
        results["all_times_ok"],
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
