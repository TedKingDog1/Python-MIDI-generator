
import re
import spacy

nlp = spacy.load("en_core_web_sm")


# ============================================================
# MUSICAL RULE BANKS
# ============================================================

MOOD_RULES = {
    "lonely": ["lonely", "isolated", "alone"],
    "dark": ["dark", "ominous", "sinister", "grim"],
    "sad": ["sad", "sorrowful", "heartbreaking", "melancholic"],
    "happy": ["happy", "joyful", "cheerful", "uplifting"],
    "hopeful": ["hopeful", "optimistic", "inspiring"],
    "angry": ["angry", "furious", "aggressive", "vengeful"],
    "peaceful": ["peaceful", "calm", "serene", "relaxing"],
    "mysterious": ["mysterious", "enigmatic", "suspenseful"],
    "triumphant": ["triumphant", "victorious", "heroic"],
    "epic": ["epic", "grand", "monumental", "massive"],
}

STYLE_RULES = {
    "orchestral": ["orchestral", "symphonic", "full orchestra"],
    "cinematic": ["cinematic", "film score", "movie soundtrack"],
    "electronic": ["electronic", "synth", "synthwave"],
    "rock": ["rock", "rock music", "guitar-driven"],
    "ambient": ["ambient", "atmospheric", "soundscape"],
    "classical": ["classical", "baroque", "chamber music"],
}

BUILD_RULES = {
    "explosive": [
        r"\bexplod(?:e|es|ed|ing)\s+into\b",
        r"\bexplosive\s+(?:climax|ending|finale)\b",
        r"\bsudden(?:ly)?\s+explod\w*\b",
        r"\bmassive\s+drop\b",
        r"\b(?:huge|massive|explosive)\s+climax\b",
        r"\b(?:burst|bursts|bursting)\s+into\b",
    ],
    "gradual": [
        r"\bgradually\s+(?:build\w*|becom\w*|grow\w*|increase\w*)\b",
        r"\bslowly\s+(?:build\w*|becom\w*|grow\w*|increase\w*)\b",
        r"\bbuild\w*\s+gradually\b",
        r"\bslowly\s+grow\w*\b",
        r"\bgradually\s+grow\w*\b",
        r"\bbuild\w*\s+(?:toward|towards|into)\b",
    ],
    "fade": [
        r"\bfade\w*\s+away\b",
        r"\bfade\w*\s+out\b",
        r"\bslowly\s+fade\w*\b",
    ],
    "steady": [
        r"\bsteady\b",
        r"\bconsistent\b",
        r"\bconstant\s+energy\b",
    ],
}

ENERGY_CURVES = {
    "gradual": [0.15, 0.30, 0.50, 0.75, 1.0],
    "explosive": [0.15, 0.25, 0.45, 0.70, 1.0],
    "steady": [0.50, 0.50, 0.50, 0.50, 0.50],
    "fade": [0.90, 0.70, 0.50, 0.30, 0.15],
}


# ============================================================
# TEXT MATCHING
# ============================================================

def find_matches(text, rule_bank):
    """Find matching categories in the text."""
    matches = []

    for category, keywords in rule_bank.items():
        for keyword in keywords:
            pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"

            if re.search(pattern, text):
                matches.append(category)
                break

    return matches


def find_mood_events(text):
    """Find mood words in their original order."""
    events = []

    for category, keywords in MOOD_RULES.items():
        for keyword in keywords:
            pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"

            for match in re.finditer(pattern, text):
                events.append({
                    "position": match.start(),
                    "mood": category,
                    "word": keyword,
                })

    events.sort(key=lambda event: event["position"])
    return events


def unique_in_order(items):
    """Remove duplicates while preserving order."""
    return list(dict.fromkeys(items))


# ============================================================
# BUILD AND ENERGY INTERPRETATION
# ============================================================

def detect_build_type(text):
    """Detect the last explicit musical-development instruction."""
    found = []

    for build_type, patterns in BUILD_RULES.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                found.append({
                    "position": match.start(),
                    "type": build_type,
                })

    if not found:
        return "steady"

    found.sort(key=lambda event: event["position"])
    return found[-1]["type"]


def find_phase_boundaries(text):
    """
    Return the start positions of the transition and ending.

    Ending phrases are detected from their beginnings, not just
    from words such as 'climax' that may appear after the mood.
    """

    transition_patterns = [
        r"\bgradually\b",
        r"\bslowly\b",
        r"\bstarts?\s+to\b",
        r"\bbegins?\s+to\b",
        r"\bbecomes?\s+more\b",
        r"\bturns?\s+into\b",
        r"\bshifts?\s+to\b",
        r"\btransitions?\s+to\b",
        r"\bgrows?\s+more\b",
    ]

    ending_patterns = [
        # "then explode into a triumphant climax"
        r"\bthen\s+(?:suddenly\s+)?(?:explod\w*|burst\w*)\s+into\b",

        # "explode into a triumphant climax"
        r"\b(?:explod\w*|burst\w*)\s+into\b",

        # "fade away into a sad conclusion"
        r"\bfade\w*\s+(?:away|out)\s+into\b",

        # "build into an epic ending"
        r"\binto\s+(?:a\s+|an\s+|the\s+)?"
        r"(?:\w+\s+){0,2}(?:climax|ending|conclusion|finale)\b",

        # "finally triumphant", "ends with a hopeful feeling"
        r"\bfinally\b",
        r"\bultimately\b",
        r"\bends?\s+with\b",
        r"\bend\s+with\b",
        r"\bfinishes?\s+with\b",
        r"\bresolves?\s+into\b",
    ]

    transition_positions = [
        match.start()
        for pattern in transition_patterns
        for match in re.finditer(pattern, text)
    ]

    ending_positions = [
        match.start()
        for pattern in ending_patterns
        for match in re.finditer(pattern, text)
    ]

    # Prefer the first transition cue and first ending cue.
    transition_start = (
        min(transition_positions)
        if transition_positions else None
    )

    ending_start = (
        min(ending_positions)
        if ending_positions else None
    )

    return transition_start, ending_start


def split_moods_into_phases(text, mood_events):
    """Classify mood events as opening, transition, or ending."""

    if not mood_events:
        return {
            "opening_moods": ["neutral"],
            "transition_moods": [],
            "ending_moods": [],
        }

    transition_start, ending_start = find_phase_boundaries(text)

    opening = []
    transition = []
    ending = []

    for event in mood_events:
        position = event["position"]
        mood = event["mood"]

        # An ending boundary takes precedence over a transition.
        if ending_start is not None and position >= ending_start:
            ending.append(mood)

        elif (
            transition_start is not None
            and position >= transition_start
        ):
            transition.append(mood)

        else:
            opening.append(mood)

    # If no explicit transition exists, don't invent one.
    # If no ending exists, the last mood remains the latest mood
    # without being automatically labelled an ending.
    return {
        "opening_moods": unique_in_order(opening),
        "transition_moods": unique_in_order(transition),
        "ending_moods": unique_in_order(ending),
    }


# ============================================================
# PROMPT ANALYZER
# ============================================================

def analyze_prompt(prompt):
    """Convert a natural-language prompt into a structured plan."""

    normalized = " ".join(prompt.lower().split())

    doc = nlp(prompt)
    words = [
        token.lemma_.lower()
        for token in doc
        if not token.is_space and not token.is_punct
    ]

    mood_events = find_mood_events(normalized)
    moods = unique_in_order([
        event["mood"] for event in mood_events
    ])

    phases = split_moods_into_phases(normalized, mood_events)

    opening_moods = phases["opening_moods"]
    transition_moods = phases["transition_moods"]
    ending_moods = phases["ending_moods"]

    build_type = detect_build_type(normalized)
    styles = find_matches(normalized, STYLE_RULES)

    primary_mood = (
        opening_moods[0] if opening_moods else "neutral"
    )

    # If no ending phrase was detected, report the last detected
    # mood as the latest mood, but keep ending_moods empty.
    ending_mood = (
        ending_moods[-1]
        if ending_moods
        else (moods[-1] if moods else "neutral")
    )

    suggested_mode = (
        "minor"
        if any(mood in {
            "lonely", "dark", "sad", "angry", "mysterious"
        } for mood in opening_moods)
        else "major"
    )

    suggested_instruments = (
        ["piano", "cello", "strings", "bass", "percussion"]
        if any(style in styles for style in [
            "cinematic", "orchestral", "classical"
        ])
        else ["piano", "cello", "bass"]
    )

    return {
        "original_prompt": prompt,
        "words_detected": words,
        "moods": moods,
        "primary_mood": primary_mood,
        "opening_mood": (
            opening_moods[0] if opening_moods else "neutral"
        ),
        "opening_moods": opening_moods,
        "transition_mood": (
            transition_moods[-1]
            if transition_moods else "none"
        ),
        "transition_moods": transition_moods,
        "ending_mood": ending_mood,
        "ending_moods": ending_moods,
        "build_type": build_type,
        "energy_curve": ENERGY_CURVES[build_type],
        "styles": styles,
        "suggested_mode": suggested_mode,
        "suggested_instruments": suggested_instruments,
    }


# ============================================================
# TEST THE ANALYZER
# ============================================================

if __name__ == "__main__":
    test_prompts = [
        (
            "Start lonely and mysterious, gradually become more "
            "hopeful, then explode into a triumphant orchestral climax."
        ),
        "A peaceful piano piece that slowly builds into an epic ending.",
        "A dark cinematic intro that fades away into a sad conclusion.",
        "A joyful, uplifting orchestral theme with steady energy.",
    ]

    for test_prompt in test_prompts:
        result = analyze_prompt(test_prompt)

        print("\n" + "=" * 60)
        print("PROMPT:", test_prompt)
        print("-" * 60)

        for key, value in result.items():
            print(f"{key}: {value}")
