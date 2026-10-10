from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

CHORD_TEMPLATES = {
    "maj": [
        {"name": "Root-6 Barre (E-Shape)", "base_string": 0, "offsets": [0, 2, 2, 1, 0, 0], "span": 3},
        {"name": "Root-5 Barre (A-Shape)", "base_string": 1, "offsets": ["x", 0, 2, 2, 2, 0], "span": 3},
        {"name": "Interior Triad (D-G-B strings)", "base_string": 2, "offsets": ["x", "x", 0, 2, 3, 2], "span": 3},
    ],
    "min": [
        {"name": "Root-6 Minor (Em-Shape)", "base_string": 0, "offsets": [0, 2, 2, 0, 0, 0], "span": 2},
        {"name": "Root-5 Minor (Am-Shape)", "base_string": 1, "offsets": ["x", 0, 2, 2, 1, 0], "span": 2},
    ],
    "7": [
        {"name": "Root-6 Dominant 7", "base_string": 0, "offsets": [0, 2, 0, 1, 0, 0], "span": 2},
        {"name": "Root-5 Dominant 7", "base_string": 1, "offsets": ["x", 0, 2, 0, 2, 0], "span": 2},
    ],
    "m7": [
        {"name": "Root-6 Minor 7", "base_string": 0, "offsets": [0, 2, 0, 0, 0, 0], "span": 2},
        {"name": "Root-5 Minor 7", "base_string": 1, "offsets": ["x", 0, 2, 0, 1, 0], "span": 2},
    ],
    "maj7": [
        {"name": "Root-6 Major 7", "base_string": 0, "offsets": [0, "x", 1, 1, 0, "x"], "span": 2},
        {"name": "Root-5 Major 7", "base_string": 1, "offsets": ["x", 0, 2, 1, 2, 0], "span": 2},
    ]
}

NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
}

TUNINGS = {
    "standard": ["E", "A", "D", "G", "B", "E"],
    "drop d": ["D", "A", "D", "G", "B", "E"],
    "open g": ["D", "G", "D", "G", "B", "D"],
    "dadgad": ["D", "A", "D", "G", "A", "D"],
    "double drop d": ["D", "A", "D", "G", "B", "D"]
}

def get_fret(root: str, string_idx: int, offset, tuning_notes, base_string: int = 0) -> str:
    if offset == "x":
        return "x"
    
    root_semitone = NOTE_TO_SEMITONE.get(root.capitalize(), 0)
    base_open_note = TUNINGS["standard"][base_string]
    base_open_semitone = NOTE_TO_SEMITONE.get(base_open_note, 0)
    root_fret_on_base = (root_semitone - base_open_semitone) % 12
    
    target_open_note = tuning_notes[string_idx]
    target_open_semitone = NOTE_TO_SEMITONE.get(target_open_note, 0)
    
    absolute_semitone = NOTE_TO_SEMITONE.get(base_open_note, 0) + root_fret_on_base + offset
    fret = (absolute_semitone - target_open_semitone) % 12
    
    return str(fret)

def generate_picking_pattern(frets, style):
    # Generates a mini tab line based on the chosen picking style
    valid_frets = [f for f in frets if f != "x"]
    if not valid_frets:
        return "Rest / Mute"
    
    low_string = frets[0] if frets[0] != "x" else (frets[1] if frets[1] != "x" else "0")
    high_strings = [f for f in frets[2:] if f != "x"]
    mid = high_strings[0] if high_strings else low_string
    top = high_strings[-1] if len(high_strings) > 1 else low_string

    if "travis" in style.lower():
        return f"Thumb({low_string}) -> Index({mid}) -> Thumb({low_string}) -> Middle({top})"
    elif "6/8" in style.lower():
        return f"Bass({low_string}) . . Arpeggio({mid} - {top} - {mid})"
    elif "triads" in style.lower():
        return f"Compact Block Strum: [{', '.join(str(f) for f in frets)}]"
    else:
        return f"Acoustic Roll: Bass({low_string}) roll up through [{top}]"

@app.route('/')
def home():
    return "FretFlow Backend is active and running!"

@app.route('/generate', methods=['POST'])
def generate_arrangement():
    data = request.get_json() or {}
    raw_progression = data.get("chords", data.get("progression", "D - G - Em - A"))
    tuning_input = data.get("tuning", "Standard").lower()
    style = data.get("style", "Travis Fingerpicking")
    
    # Match tuning selection
    tuning_notes = TUNINGS["standard"]
    for key in TUNINGS:
        if key in tuning_input:
            tuning_notes = TUNINGS[key]
            break
            
    progression = []
    if isinstance(raw_progression, str):
        chords = [c.strip() for c in raw_progression.replace("-", " ").split() if c.strip()]
        for chord in chords:
            root = chord[0].upper()
            if len(chord) > 1 and chord[1] in ["#", "b"]:
                root = chord[:2]
                quality_str = chord[2:].lower()
            else:
                quality_str = chord[1:].lower()
            
            if quality_str in ["m", "min"]:
                quality = "min"
            elif quality_str in ["7"]:
                quality = "7"
            elif quality_str in ["m7", "min7"]:
                quality = "m7"
            elif quality_str in ["maj7"]:
                quality = "maj7"
            else:
                quality = "maj"
            progression.append({"root": root, "quality": quality})
    else:
        progression = raw_progression
        
    response_data = []
    for item in progression:
        root = item.get("root").capitalize()
        quality = item.get("quality", "maj").lower()
        templates = CHORD_TEMPLATES.get(quality, CHORD_TEMPLATES["maj"])
        
        chord_variations = []
        for t in templates:
            frets = [
                get_fret(root, i, off, tuning_notes, t["base_string"]) 
                for i, off in enumerate(t["offsets"])
            ]
            pattern_text = generate_picking_pattern(frets, style)
            
            chord_variations.append({
                "name": t["name"],
                "frets": frets,
                "pattern": pattern_text,
                "span": t["span"]
            })
            
        response_data.append({
            "chord": f"{root}{quality if quality != 'maj' else ''}",
            "root": root,
            "quality": quality,
            "variations": chord_variations
        })

    return jsonify({
        "progression": response_data
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
