# main.py

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Master dictionary of physical, human-verified guitar voicings 
# based on standard string offsets from a root position.
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
    "drop_d": ["D", "A", "D", "G", "B", "E"]
}

def get_fret(root: str, string_idx: int, offset, tuning: str) -> str:
    if offset == "x":
        return "x"
    open_note = TUNING_OFFSETS.get(tuning, TUNING_OFFSETS["standard"])[string_idx]
    root_semitone = NOTE_TO_SEMITONE[root.capitalize()]
    open_semitone = NOTE_TO_SEMITONE[open_note]
    
    # Calculate absolute fret position on that string
    fret = (root_semitone - open_semitone) % 12 + offset
    return str(fret)

@app.route('/api/voicings', methods=['POST'])
def fetch_voicings():
    data = request.get_json() or {}
    progression = data.get("progression", []) # e.g. [{"root": "F#", "quality": "m7"}, ...]
    tuning = data.get("tuning", "standard")
    
    resolved_chords = {}
    for item in progression:
        root = item.get("root")
        quality = item.get("quality", "maj").lower()
        key_name = f"{root}{quality}"
        
        templates = CHORD_TEMPLATES.get(quality, CHORD_TEMPLATES["maj"])
        chord_variations = []
        
        for t in templates:
            base_str = t["base_string"]
            frets = [get_fret(root, i, off, tuning) for i, off in enumerate(t["offsets"])]
            chord_variations.append({
                "name": t["name"],
                "frets": frets,
                "span": t["span"]
            })
            
        resolved_chords[key_name] = chord_variations
        
    return jsonify({"status": "success", "voicings": resolved_chords})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
