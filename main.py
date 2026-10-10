from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Tried-and-tested chord shapes relative to their base root string (Root-6 is based on E, Root-5 on A)
CHORD_TEMPLATES = {
    "maj": [
        {"name": "Root-6 Barre (E-Shape)", "base_root": "E", "frets": [0, 2, 2, 1, 0, 0], "span": 3},
        {"name": "Root-5 Barre (A-Shape)", "base_root": "A", "frets": ["x", 0, 2, 2, 2, 0], "span": 3},
        {"name": "Interior Triad (D-G-B strings)", "base_root": "D", "frets": ["x", "x", 0, 2, 3, 2], "span": 3},
    ],
    "min": [
        {"name": "Root-6 Minor (Em-Shape)", "base_root": "E", "frets": [0, 2, 2, 0, 0, 0], "span": 2},
        {"name": "Root-5 Minor (Am-Shape)", "base_root": "A", "frets": ["x", 0, 2, 2, 1, 0], "span": 2},
    ],
    "7": [
        {"name": "Root-6 Dominant 7", "base_root": "E", "frets": [0, 2, 0, 1, 0, 0], "span": 2},
        {"name": "Root-5 Dominant 7", "base_root": "A", "frets": ["x", 0, 2, 0, 2, 0], "span": 2},
    ],
    "m7": [
        {"name": "Root-6 Minor 7", "base_root": "E", "frets": [0, 2, 0, 0, 0, 0], "span": 2},
        {"name": "Root-5 Minor 7", "base_root": "A", "frets": ["x", 0, 2, 0, 1, 0], "span": 2},
    ],
    "maj7": [
        {"name": "Root-6 Major 7", "base_root": "E", "frets": [0, "x", 1, 1, 0, "x"], "span": 2},
        {"name": "Root-5 Major 7", "base_root": "A", "frets": ["x", 0, 2, 1, 2, 0], "span": 2},
    ]
}

NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
}

@app.route('/')
def home():
    return "FretFlow Backend is active and running!"

@app.route('/generate', methods=['POST'])
def generate_arrangement():
    data = request.get_json() or {}
    raw_progression = data.get("chords", data.get("progression", "D - G - Em - A"))
    
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
            base_root = t["base_root"]
            # Calculate the exact semitone shift from the template base root to the target chord root
            shift = (NOTE_TO_SEMITONE.get(root, 0) - NOTE_TO_SEMITONE.get(base_root, 0)) % 12
            
            shifted_frets = []
            for f in t["frets"]:
                if f == "x":
                    shifted_frets.append("x")
                else:
                    # Shift the base shape cleanly without wrapping individual notes
                    shifted_frets.append(f + shift)
                    
            chord_variations.append({
                "name": t["name"],
                "frets": shifted_frets,
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
