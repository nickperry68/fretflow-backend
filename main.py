from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Keeps the door open for your website to talk to Railway

# Master dictionary of physical, human-verified guitar voicings 
CHORD_TEMPLATES = {
    "maj": [
        {"name": "Root-6 Barre (E-Shape)", "base_string": 0, "offsets": [0, 2, 2, 1, 0, 0], "span": 3},
        {"name": "Root-5 Barre (A-Shape)", "base_string": 1, "offsets": ["x", 0, 2, 2, 2, 0], "span": 3},
        {"name": "Interior Triad (D-G-B strings)", "base_string": 2, "offsets": ["x", "x", 0, 2, 3, 2], "span": 3},
        {"name": "High Shell Voicing", "base_string": 3, "offsets": ["x", "x", "x", 9, 10, 8], "span": 3},
    ],
    "min": [
        {"name": "Root-6 Minor (Em-Shape)", "base_string": 0, "offsets": [0, 2, 2, 0, 0, 0], "span": 2},
        {"name": "Root-5 Minor (Am-Shape)", "base_string": 1, "offsets": ["x", 0, 2, 2, 1, 0], "span": 2},
        {"name": "Interior Minor Triad", "base_string": 2, "offsets": ["x", "x", 0, 2, 1, 3], "span": 3},
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

TUNING_OFFSETS = {
    "standard": ["E", "A", "D", "G", "B", "E"],
    "drop d (dadgbe)": ["D", "A", "D", "G", "B", "E"],
    "drop_d": ["D", "A", "D", "G", "B", "E"]
}

def get_fret(root: str, string_idx: int, offset, tuning: str) -> str:
    if offset == "x":
        return "x"
    tuning_key = tuning.lower().strip()
    open_note = TUNING_OFFSETS.get(tuning_key, TUNING_OFFSETS["standard"])[string_idx]
    root_semitone = NOTE_TO_SEMITONE.get(root.capitalize(), 0)
    open_semitone = NOTE_TO_SEMITONE.get(open_note, 0)
    
    fret = (root_semitone - open_semitone) % 12 + offset
    return str(fret)

@app.route('/')
def home():
    return "FretFlow Backend is active and running!"

@app.route('/generate', methods=['POST'])
def generate_arrangement():
    data = request.get_json() or {}
    raw_progression = data.get("chords", data.get("progression", "D - G - Em - A"))
    tuning = data.get("tuning", "standard")
    
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
        
    resolved_chords = {}
    output_text = "🎸 FretFlow Hybrid Voicings Report\n" + "="*35 + "\n\n"
    
    for item in progression:
        root = item.get("root")
        quality = item.get("quality", "maj").lower()
        key_name = f"{root}{quality}"
        
        templates = CHORD_TEMPLATES.get(quality, CHORD_TEMPLATES["maj"])
        chord_variations = []
        
        output_text += f"Chord: {root.upper()}{quality if quality != 'maj' else ''}\n"
        for t in templates:
            frets = [get_fret(root, i, off, tuning) for i, off in enumerate(t["offsets"])]
            output_text += f"  - {t['name']}: {frets}\n"
        output_text += "\n"

    return jsonify({"result": output_text})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
