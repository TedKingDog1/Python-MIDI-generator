
import os
import mido
from mido import (
    MidiFile,
    MidiTrack,
    Message,
    MetaMessage,
    bpm2tempo,
)

from prompt_analyzer import analyze_prompt

TPB = 480
BEATS_PER_BAR = 4


# ============================================================
# MUSICAL EVENT HELPERS
# ============================================================

def add_note(track, note, duration, velocity=80, channel=0):
    """Schedule one note using absolute MIDI event positions."""
    note = max(0, min(127, int(note)))
    velocity = max(1, min(127, int(velocity)))

    start = track["cursor"]
    duration_ticks = max(1, int(duration * TPB))

    track["events"].append((
        start, 1,
        Message(
            "note_on",
            note=note,
            velocity=velocity,
            channel=channel,
            time=0,
        ),
    ))

    track["events"].append((
        start + duration_ticks, 0,
        Message(
            "note_off",
            note=note,
            velocity=0,
            channel=channel,
            time=0,
        ),
    ))

    track["cursor"] += duration_ticks


def add_chord(track, notes, duration, velocity=70, channel=0):
    """Schedule simultaneous notes that form a chord."""
    if not notes:
        return

    start = track["cursor"]
    duration_ticks = max(1, int(duration * TPB))
    velocity = max(1, min(127, int(velocity)))

    for note in notes:
        note = max(0, min(127, int(note)))

        track["events"].append((
            start, 1,
            Message(
                "note_on",
                note=note,
                velocity=velocity,
                channel=channel,
                time=0,
            ),
        ))

        track["events"].append((
            start + duration_ticks, 0,
            Message(
                "note_off",
                note=note,
                velocity=0,
                channel=channel,
                time=0,
            ),
        ))

    track["cursor"] += duration_ticks


def rest(track, duration):
    """Advance the track's position without playing a note."""
    track["cursor"] += max(0, int(duration * TPB))


def make_track(name, channel, program=None):
    """Create a track's event schedule."""
    return {
        "name": name,
        "channel": channel,
        "program": program,
        "cursor": 0,
        "events": [],
    }


def write_track(mid, scheduled_track):
    """Convert absolute event positions into MIDI delta-times."""
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage(
        "track_name",
        name=scheduled_track["name"],
        time=0,
    ))

    program = scheduled_track["program"]

    if program is not None:
        track.append(Message(
            "program_change",
            program=program,
            channel=scheduled_track["channel"],
            time=0,
        ))

    events = sorted(
        scheduled_track["events"],
        key=lambda event: (event[0], event[1]),
    )

    previous_tick = 0

    for absolute_tick, _, message in events:
        message.time = absolute_tick - previous_tick
        track.append(message)
        previous_tick = absolute_tick


# ============================================================
# MUSICAL INTERPRETATION
# ============================================================

DARK_MOODS = {
    "lonely", "dark", "sad", "mysterious"
}

BRIGHT_MOODS = {
    "happy", "hopeful", "peaceful"
}

POWERFUL_MOODS = {
    "triumphant", "epic", "angry"
}



def get_section_energy(plan, section_index):
    """Map prompt energy to the five song sections.

    The climax comes before the outro, so explosive and gradual
    curves should peak at the climax and then resolve.
    """

    build_type = plan.get("build_type", "steady")
    curve = plan.get("energy_curve", [0.15, 0.30, 0.50, 0.75, 1.0])

    if len(curve) != 5:
        curve = [0.15, 0.30, 0.50, 0.75, 1.0]

    if build_type == "fade":
        # A fade should continue into the ending.
        energy = curve[section_index]

    elif build_type == "steady":
        energy = curve[section_index]

    else:
        # The climax gets maximum energy; the outro resolves.
        energy = curve[min(section_index, 3)]

        if section_index == 4:
            energy = min(curve[1], 0.30)

    return max(0.0, min(1.0, float(energy)))



def get_section_mood(plan, section_name):
    """Choose the mood appropriate to each song section."""
    opening = plan.get("opening_mood", "neutral")
    transition = plan.get("transition_mood", "none")
    ending = plan.get("ending_mood", "neutral")

    if section_name in ("Intro", "Theme"):
        return opening

    if section_name == "Build":
        if transition != "none":
            return transition
        return opening

    if ending != "neutral":
        return ending

    if transition != "none":
        return transition

    return opening


def adjust_velocity(base_velocity, energy, mood):
    """Combine section dynamics with the interpreted mood."""
    velocity = base_velocity * (0.8 + 0.4 * energy)

    if mood in POWERFUL_MOODS:
        velocity += 7
    elif mood in BRIGHT_MOODS:
        velocity += 3
    elif mood in DARK_MOODS:
        velocity -= 6

    return max(1, min(127, round(velocity)))


def adjust_melody_register(note, mood, section_name):
    """Use register to reinforce the current musical mood."""
    if mood in DARK_MOODS and section_name in ("Intro", "Theme"):
        note -= 12

    elif (
        mood in POWERFUL_MOODS
        and section_name == "Climax"
    ):
        note += 12

    return max(0, min(127, note))


# ============================================================
# SONG GENERATOR
# ============================================================

def generate_song(
    filename,
    bpm=100,
    key="C",
    mode="major",
    instruments=None,
    prompt="",
):
    if instruments is None:
        instruments = [
            "piano",
            "cello",
            "strings",
            "bass",
            "percussion",
        ]

    # --------------------------------------------------------
    # VALIDATE SETTINGS
    # --------------------------------------------------------

    bpm = max(40, min(240, int(bpm)))
    mode = mode.lower()

    valid_keys = [
        "C", "C#", "D", "D#", "E", "F",
        "F#", "G", "G#", "A", "A#", "B",
    ]

    if key not in valid_keys:
        key = "C"

    valid_instruments = {
        "piano", "cello", "strings", "bass", "percussion"
    }

    instruments = list(dict.fromkeys(
        instrument
        for instrument in instruments
        if instrument in valid_instruments
    ))

    os.makedirs(
        os.path.dirname(filename) or ".",
        exist_ok=True,
    )

    # --------------------------------------------------------
    # INTERPRET THE PROMPT
    # --------------------------------------------------------

    plan = analyze_prompt(prompt)

    print("\n----- GENERATING SONG -----")
    print("Prompt:", prompt)
    print("Key:", key)
    print("Mode:", mode)
    print("BPM:", bpm)
    print("Instruments:", instruments)
    print("Opening mood:", plan["opening_mood"])
    print("Transition mood:", plan["transition_mood"])
    print("Ending mood:", plan["ending_mood"])
    print("Build type:", plan["build_type"])
    print("Energy curve:", plan["energy_curve"])
    print("Styles:", plan["styles"])
    print("---------------------------")

    # The UI's selected key and mode remain authoritative.
    # The analyzer guides composition rather than overriding them.

    # --------------------------------------------------------
    # KEY AND SCALE
    # --------------------------------------------------------

    key_offsets = {
        "C": 0,
        "C#": 1,
        "D": 2,
        "D#": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "G": 7,
        "G#": 8,
        "A": 9,
        "A#": 10,
        "B": 11,
    }

    root = key_offsets[key]

    if mode == "minor":
        scale = [0, 2, 3, 5, 7, 8, 10]

        chord_intervals = [
            [0, 3, 7],       # i
            [10, 14, 17],    # VII
            [8, 12, 15],     # VI
            [5, 8, 12],      # iv
        ]

    else:
        scale = [0, 2, 4, 5, 7, 9, 11]

        chord_intervals = [
            [0, 4, 7],       # I
            [7, 11, 14],     # V
            [9, 12, 16],     # vi
            [5, 9, 12],      # IV
        ]

    chords = [
        [60 + root + interval for interval in chord]
        for chord in chord_intervals
    ]

    # --------------------------------------------------------
    # TEMPO AND SONG STRUCTURE
    # --------------------------------------------------------

    mid = MidiFile(ticks_per_beat=TPB)

    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)

    tempo_track.append(MetaMessage(
        "track_name",
        name="Tempo",
        time=0,
    ))

    tempo_track.append(MetaMessage(
        "set_tempo",
        tempo=bpm2tempo(bpm),
        time=0,
    ))

    sections = [
        {"name": "Intro", "bars": 8, "energy_index": 0},
        {"name": "Theme", "bars": 16, "energy_index": 1},
        {"name": "Build", "bars": 16, "energy_index": 2},
        {"name": "Climax", "bars": 16, "energy_index": 3},
        {"name": "Outro", "bars": 8, "energy_index": 4},
    ]

    print("\nSong structure:")

    for section in sections:
        print(
            f"  {section['name']}: {section['bars']} bars"
        )

    # --------------------------------------------------------
    # RECURRING CELLO MOTIF
    # --------------------------------------------------------

    motif_degrees = [0, 2, 4, 2, 3, 2, 1, 0]

    motif = [
        60 + root + scale[degree]
        for degree in motif_degrees
    ]

    # --------------------------------------------------------
    # CREATE INSTRUMENT TRACKS
    # --------------------------------------------------------

    instrument_settings = {
        "piano": ("Piano", 0, 0),
        "cello": ("Cello", 42, 1),
        "strings": ("Strings", 48, 2),
        "bass": ("Bass", 32, 3),
    }

    tracks = {}

    for instrument, (name, program, channel) in (
        instrument_settings.items()
    ):
        if instrument in instruments:
            tracks[instrument] = make_track(
                name,
                channel,
                program,
            )

    if "percussion" in instruments:
        tracks["percussion"] = make_track(
            "Percussion",
            9,
            None,
        )

    # --------------------------------------------------------
    # COMPOSE THE SONG
    # --------------------------------------------------------

    global_bar = 0

    for section in sections:
        name = section["name"]
        energy = get_section_energy(
            plan,
            section["energy_index"],
        )
        mood = get_section_mood(plan, name)

        print(
            f"Composing {name}: "
            f"mood={mood}, energy={energy:.2f}"
        )

        for bar in range(section["bars"]):
            bar_start = global_bar * BEATS_PER_BAR * TPB

            # Every track begins this bar at the same absolute time.
            for track in tracks.values():
                track["cursor"] = bar_start

            chord = chords[global_bar % len(chords)]
            harmony_root = chord[0]

            # ------------------------------------------------
            # PIANO
            # ------------------------------------------------

            if "piano" in tracks:
                piano = tracks["piano"]

                if name == "Intro":
                    add_chord(
                        piano,
                        chord,
                        4,
                        velocity=adjust_velocity(
                            42, energy, mood
                        ),
                        channel=0,
                    )

                elif name == "Theme":
                    add_chord(
                        piano,
                        chord,
                        4,
                        velocity=adjust_velocity(
                            60, energy, mood
                        ),
                        channel=0,
                    )

                elif name == "Build":
                    add_chord(
                        piano,
                        chord,
                        2,
                        velocity=adjust_velocity(
                            68, energy, mood
                        ),
                        channel=0,
                    )
                    add_chord(
                        piano,
                        chord,
                        2,
                        velocity=adjust_velocity(
                            62, energy, mood
                        ),
                        channel=0,
                    )

                elif name == "Climax":
                    for beat in range(4):
                        base = 88 if beat % 2 == 0 else 76

                        add_chord(
                            piano,
                            chord,
                            1,
                            velocity=adjust_velocity(
                                base, energy, mood
                            ),
                            channel=0,
                        )

                elif name == "Outro":
                    add_chord(
                        piano,
                        chord,
                        4,
                        velocity=adjust_velocity(
                            38, energy, mood
                        ),
                        channel=0,
                    )

            # ------------------------------------------------
            # CELLO: MOTIF DEVELOPMENT
            # ------------------------------------------------

            if "cello" in tracks:
                cello = tracks["cello"]
                motif_start = (global_bar * 4) % len(motif)

                if name == "Intro":
                    if bar % 2 == 0:
                        for step in range(2):
                            note = motif[
                                (motif_start + step) % 8
                            ] - 12

                            note = adjust_melody_register(
                                note, mood, name
                            )

                            add_note(
                                cello,
                                note,
                                2,
                                velocity=adjust_velocity(
                                    42 - step * 4,
                                    energy,
                                    mood,
                                ),
                                channel=1,
                            )
                    else:
                        add_note(
                            cello,
                            harmony_root - 12,
                            4,
                            velocity=adjust_velocity(
                                32, energy, mood
                            ),
                            channel=1,
                        )

                elif name == "Theme":
                    for step in range(4):
                        note = motif[
                            (motif_start + step) % 8
                        ]

                        note = adjust_melody_register(
                            note, mood, name
                        )

                        add_note(
                            cello,
                            note,
                            1,
                            velocity=adjust_velocity(
                                68 + (step % 2) * 5,
                                energy,
                                mood,
                            ),
                            channel=1,
                        )

                elif name == "Build":
                    for step in range(4):
                        note = motif[
                            (motif_start + step) % 8
                        ]

                        if bar >= 8 and step >= 2:
                            note += 12

                        note = adjust_melody_register(
                            note, mood, name
                        )

                        add_note(
                            cello,
                            note,
                            1,
                            velocity=adjust_velocity(
                                78 + step * 3,
                                energy,
                                mood,
                            ),
                            channel=1,
                        )

                elif name == "Climax":
                    for step in range(8):
                        note = motif[
                            (motif_start + step) % 8
                        ]

                        if bar % 4 in (2, 3):
                            note += 12

                        note = adjust_melody_register(
                            note, mood, name
                        )

                        add_note(
                            cello,
                            note,
                            0.5,
                            velocity=adjust_velocity(
                                92 if step in (0, 4) else 82,
                                energy,
                                mood,
                            ),
                            channel=1,
                        )

                elif name == "Outro":
                    for step in range(2):
                        note = motif[
                            (motif_start + step) % 8
                        ]

                        add_note(
                            cello,
                            note,
                            2,
                            velocity=adjust_velocity(
                                46 - step * 6,
                                energy,
                                mood,
                            ),
                            channel=1,
                        )

            # ------------------------------------------------
            # STRINGS: HARMONIC DEPTH
            # ------------------------------------------------

            if "strings" in tracks:
                strings = tracks["strings"]
                high_chord = [note + 12 for note in chord]

                if name == "Intro":
                    # Cinematic openings introduce strings quietly.
                    if any(
                        style in plan["styles"]
                        for style in ("cinematic", "orchestral")
                    ):
                        add_chord(
                            strings,
                            high_chord,
                            4,
                            velocity=adjust_velocity(
                                25, energy, mood
                            ),
                            channel=2,
                        )

                elif name == "Theme":
                    add_chord(
                        strings,
                        high_chord,
                        4,
                        velocity=adjust_velocity(
                            38, energy, mood
                        ),
                        channel=2,
                    )

                elif name == "Build":
                    add_chord(
                        strings,
                        high_chord,
                        4,
                        velocity=adjust_velocity(
                            58 + (bar % 4) * 3,
                            energy,
                            mood,
                        ),
                        channel=2,
                    )

                elif name == "Climax":
                    add_chord(
                        strings,
                        high_chord,
                        4,
                        velocity=adjust_velocity(
                            88, energy, mood
                        ),
                        channel=2,
                    )

                elif name == "Outro":
                    add_chord(
                        strings,
                        high_chord,
                        4,
                        velocity=adjust_velocity(
                            35, energy, mood
                        ),
                        channel=2,
                    )

            # ------------------------------------------------
            # BASS: LOW-END FOUNDATION
            # ------------------------------------------------

            if "bass" in tracks:
                bass = tracks["bass"]
                bass_note = harmony_root - 12

                if name == "Intro":
                    if bar % 2 == 0:
                        add_note(
                            bass,
                            bass_note,
                            4,
                            velocity=adjust_velocity(
                                38, energy, mood
                            ),
                            channel=3,
                        )

                elif name == "Theme":
                    add_note(
                        bass,
                        bass_note,
                        4,
                        velocity=adjust_velocity(
                            54, energy, mood
                        ),
                        channel=3,
                    )

                elif name == "Build":
                    for beat in range(2):
                        add_note(
                            bass,
                            bass_note,
                            2,
                            velocity=adjust_velocity(
                                65 + beat * 5,
                                energy,
                                mood,
                            ),
                            channel=3,
                        )

                elif name == "Climax":
                    for beat in range(4):
                        add_note(
                            bass,
                            bass_note,
                            1,
                            velocity=adjust_velocity(
                                86 if beat % 2 == 0 else 76,
                                energy,
                                mood,
                            ),
                            channel=3,
                        )

                elif name == "Outro":
                    add_note(
                        bass,
                        bass_note,
                        4,
                        velocity=adjust_velocity(
                            38, energy, mood
                        ),
                        channel=3,
                    )

            # ------------------------------------------------
            # PERCUSSION: ENERGY-AWARE RHYTHM
            # ------------------------------------------------

            if "percussion" in tracks:
                percussion = tracks["percussion"]

                if name == "Intro":
                    # Let the other instruments establish the mood.
                    pass

                elif name == "Theme":
                    add_note(
                        percussion,
                        36,
                        1,
                        velocity=adjust_velocity(
                            48, energy, mood
                        ),
                        channel=9,
                    )
                    rest(percussion, 3)

                elif name == "Build":
                    for beat in range(4):
                        drum = 36 if beat % 2 == 0 else 38
                        base = 72 if beat % 2 == 0 else 58

                        add_note(
                            percussion,
                            drum,
                            0.5,
                            velocity=adjust_velocity(
                                base, energy, mood
                            ),
                            channel=9,
                        )
                        rest(percussion, 0.5)

                elif name == "Climax":
                    if bar == 0:
                        add_note(
                            percussion,
                            49,
                            0.5,
                            velocity=adjust_velocity(
                                105, energy, mood
                            ),
                            channel=9,
                        )
                        rest(percussion, 0.5)

                    for beat in range(4):
                        drum = 36 if beat % 2 == 0 else 38
                        base = 100 if beat % 2 == 0 else 78

                        add_note(
                            percussion,
                            drum,
                            0.5,
                            velocity=adjust_velocity(
                                base, energy, mood
                            ),
                            channel=9,
                        )
                        rest(percussion, 0.5)

                elif name == "Outro":
                    pass

            global_bar += 1

    # --------------------------------------------------------
    # WRITE AND SAVE MIDI
    # --------------------------------------------------------

    for scheduled_track in tracks.values():
        write_track(mid, scheduled_track)

    mid.save(filename)

    print("\nSong saved to:", filename)
    print("Generation complete.")
