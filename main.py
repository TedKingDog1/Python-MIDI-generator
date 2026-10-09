import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

# ============================================================
# DARK CINEMATIC — "THE AWAKENING"
# Piano → Cello → Mystery → HUGE ORCHESTRAL CLIMAX
# ============================================================

TPB = 480
BPM = 88

mid = MidiFile(ticks_per_beat=TPB)

# ------------------------------------------------------------
# MIDI helpers
# ------------------------------------------------------------

def add_note(track, note, duration, velocity=80, channel=0):
    track.append(Message(
        'note_on',
        note=note,
        velocity=velocity,
        channel=channel,
        time=0
    ))

    track.append(Message(
        'note_off',
        note=note,
        velocity=0,
        channel=channel,
        time=int(duration * TPB)
    ))


def add_chord(track, notes, duration, velocity=70, channel=0):
    for note in notes:
        track.append(Message(
            'note_on',
            note=note,
            velocity=velocity,
            channel=channel,
            time=0
        ))

    track.append(Message(
        'note_off',
        note=notes[0],
        velocity=0,
        channel=channel,
        time=int(duration * TPB)
    ))

    for note in notes[1:]:
        track.append(Message(
            'note_off',
            note=note,
            velocity=0,
            channel=channel,
            time=0
        ))


def add_program(track, program, channel=0):
    track.append(Message(
        'program_change',
        program=program,
        channel=channel,
        time=0
    ))


# ------------------------------------------------------------
# Tempo
# ------------------------------------------------------------

tempo_track = MidiTrack()
mid.tracks.append(tempo_track)

tempo_track.append(
    MetaMessage(
        'set_tempo',
        tempo=bpm2tempo(BPM),
        time=0
    )
)


# ============================================================
# TRACK 1 — PIANO
# ============================================================

piano = MidiTrack()
mid.tracks.append(piano)

add_program(piano, 0)

# Dark opening progression
CHORDS = [
    [48, 51, 55],  # Cm
    [46, 50, 53],  # Bb
    [43, 46, 51],  # Ab
    [41, 44, 48],  # Fm
]

# ------------------------------------------------------------
# INTRO — sparse piano
# ------------------------------------------------------------

for chord in CHORDS:
    add_chord(piano, chord, 4, 48)

# ------------------------------------------------------------
# MYSTERY — broken piano pattern
# ------------------------------------------------------------

for repeat in range(2):

    for chord in CHORDS:
        root, third, fifth = chord

        pattern = [
            root + 12,
            fifth + 12,
            third + 12,
            fifth + 12,
        ]

        for note in pattern:
            add_note(
                piano,
                note,
                0.5,
                55 + repeat * 5
            )


# ------------------------------------------------------------
# BUILD — stronger piano
# ------------------------------------------------------------

BUILD_CHORDS = [
    [48, 51, 55],
    [46, 50, 53],
    [43, 46, 51],
    [41, 44, 48],
]

for repeat in range(2):

    for chord in BUILD_CHORDS:

        root, third, fifth = chord

        pattern = [
            root + 12,
            third + 12,
            fifth + 12,
            third + 12,
            root + 12,
            fifth + 12,
            third + 12,
            fifth + 12,
        ]

        for note in pattern:
            add_note(
                piano,
                note,
                0.5,
                65 + repeat * 8
            )


# ============================================================
# TRACK 2 — CELLO
# ============================================================

cello = MidiTrack()
mid.tracks.append(cello)

# Cello
add_program(cello, 42)

# ------------------------------------------------------------
# FIRST CELLO ENTRANCE
# ------------------------------------------------------------

CELLO_INTRO = [
    (48, 2),
    (51, 2),
    (55, 4),

    (46, 2),
    (50, 2),
    (53, 4),

    (43, 2),
    (46, 2),
    (51, 4),

    (41, 2),
    (44, 2),
    (48, 4),
]

for note, duration in CELLO_INTRO:
    add_note(
        cello,
        note,
        duration,
        68
    )


# ------------------------------------------------------------
# MYSTERIOUS CELLO MOTIF
# ------------------------------------------------------------

CELLO_MYSTERY = [
    (55, 1),
    (58, 1),
    (60, 2),

    (58, 1),
    (55, 1),
    (53, 2),

    (51, 1),
    (55, 1),
    (58, 2),

    (55, 1),
    (53, 1),
    (48, 2),
]

for repeat in range(2):

    for note, duration in CELLO_MYSTERY:
        add_note(
            cello,
            note,
            duration,
            72 + repeat * 5
        )


# ------------------------------------------------------------
# BUILDING CELLO
# ------------------------------------------------------------

CELLO_BUILD = [
    (48, 1),
    (51, 1),
    (55, 2),

    (58, 1),
    (55, 1),
    (51, 2),

    (46, 1),
    (50, 1),
    (53, 2),

    (58, 1),
    (55, 1),
    (53, 2),
]

for repeat in range(2):

    for note, duration in CELLO_BUILD:
        add_note(
            cello,
            note,
            duration,
            82 + repeat * 8
        )


# ------------------------------------------------------------
# HUGE CELLO CLIMAX
# ------------------------------------------------------------

CELLO_CLIMAX = [
    (48, 1),
    (51, 1),
    (55, 1),
    (60, 1),

    (58, 1),
    (55, 1),
    (60, 1),
    (63, 1),

    (62, 2),
    (60, 2),

    (58, 1),
    (55, 1),
    (51, 1),
    (55, 1),

    (58, 1),
    (60, 1),
    (63, 1),
    (67, 1),

    (65, 2),
    (63, 2),
]

for note, duration in CELLO_CLIMAX:
    add_note(
        cello,
        note,
        duration,
        108
    )


# ============================================================
# TRACK 3 — HIGH STRINGS
# ============================================================

strings = MidiTrack()
mid.tracks.append(strings)

add_program(strings, 48)

# Silence during intro.
# Strings gradually enter during mystery.

for chord in CHORDS:

    notes = [
        chord[0] + 24,
        chord[1] + 24,
        chord[2] + 24
    ]

    add_chord(
        strings,
        notes,
        4,
        42
    )


# Stronger strings
for repeat in range(2):

    for chord in CHORDS:

        notes = [
            chord[0] + 24,
            chord[1] + 24,
            chord[2] + 24
        ]

        add_chord(
            strings,
            notes,
            4,
            65 + repeat * 12
        )


# ============================================================
# TRACK 4 — LOW STRINGS
# ============================================================

low_strings = MidiTrack()
mid.tracks.append(low_strings)

add_program(low_strings, 48)

# Deep sustained notes

LOW_PATTERN = [
    36,
    34,
    31,
    29,
]

for repeat in range(4):

    for note in LOW_PATTERN:

        add_note(
            low_strings,
            note,
            4,
            55 + repeat * 10
        )


# ============================================================
# TRACK 5 — BASS
# ============================================================

bass = MidiTrack()
mid.tracks.append(bass)

add_program(bass, 43)

BASS_PATTERN = [
    36,
    34,
    31,
    29,
]

# Quiet early bass
for note in BASS_PATTERN:
    add_note(
        bass,
        note,
        4,
        48
    )

# Stronger bass
for repeat in range(3):

    for note in BASS_PATTERN:

        add_note(
            bass,
            note,
            2,
            70 + repeat * 10
        )

        add_note(
            bass,
            note + 12,
            2,
            65 + repeat * 10
        )


# ============================================================
# TRACK 6 — ORCHESTRAL PERCUSSION
# ============================================================

drums = MidiTrack()
mid.tracks.append(drums)

DRUM_CHANNEL = 9

# ------------------------------------------------------------
# Very sparse opening
# ------------------------------------------------------------

# Low orchestral boom
drums.append(
    Message(
        'note_on',
        note=35,
        velocity=55,
        channel=DRUM_CHANNEL,
        time=0
    )
)

drums.append(
    Message(
        'note_off',
        note=35,
        velocity=0,
        channel=DRUM_CHANNEL,
        time=int(4 * TPB)
    )
)


# ------------------------------------------------------------
# BUILDING PERCUSSION
# ------------------------------------------------------------

for i in range(8):

    # Deep boom
    drums.append(
        Message(
            'note_on',
            note=35,
            velocity=65 + i * 4,
            channel=DRUM_CHANNEL,
            time=0
        )
    )

    drums.append(
        Message(
            'note_off',
            note=35,
            velocity=0,
            channel=DRUM_CHANNEL,
            time=int(2 * TPB)
        )
    )


# ------------------------------------------------------------
# CLIMAX — HUGE LOW HITS
# ------------------------------------------------------------

for i in range(8):

    drums.append(
        Message(
            'note_on',
            note=35,
            velocity=115,
            channel=DRUM_CHANNEL,
            time=0
        )
    )

    drums.append(
        Message(
            'note_off',
            note=35,
            velocity=0,
            channel=DRUM_CHANNEL,
            time=int(TPB)
        ))

    # Second impact
    drums.append(
        Message(
            'note_on',
            note=36,
            velocity=95,
            channel=DRUM_CHANNEL,
            time=0
        )
    )

    drums.append(
        Message(
            'note_off',
            note=36,
            velocity=0,
            channel=DRUM_CHANNEL,
            time=int(TPB)
        )
    )


# ============================================================
# TRACK 7 — CLIMAX PIANO OCTAVES
# ============================================================

climax_piano = MidiTrack()
mid.tracks.append(climax_piano)

add_program(climax_piano, 0)

CLIMAX_CHORDS = [
    [60, 63, 67],
    [58, 62, 65],
    [55, 58, 63],
    [53, 56, 60],
]

for repeat in range(2):

    for chord in CLIMAX_CHORDS:

        for beat in range(4):

            for note in chord:
                add_note(
                    climax_piano,
                    note,
                    0.25,
                    88 + repeat * 8
                )


# ============================================================
# TRACK 8 — FINAL HIGH STRING MELODY
# ============================================================

final_strings = MidiTrack()
mid.tracks.append(final_strings)

add_program(final_strings, 48)

FINAL_MELODY = [
    (72, 1),
    (75, 1),
    (79, 2),

    (77, 1),
    (75, 1),
    (72, 2),

    (74, 1),
    (77, 1),
    (80, 2),

    (79, 1),
    (77, 1),
    (75, 2),

    (79, 1),
    (82, 1),
    (84, 2),

    (82, 1),
    (79, 1),
    (75, 2),

    (79, 1),
    (82, 1),
    (87, 4),
]

for note, duration in FINAL_MELODY:

    add_note(
        final_strings,
        note,
        duration,
        100
    )


# ============================================================
# SAVE
# ============================================================

mid.save("dark_cinematic_awaken.mid")

print("DONE!")
print("Created: dark_cinematic_awaken.mid")
print("Import the MIDI into BandLab.")