import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    chords = data.get("chords", "")
    tuning = data.get("tuning", "")
    capo = data.get("capo", "")
    style = data.get("style", "")

    prompt = f"""You are an expert guitar master and teacher specializing in fingerpicking, open tunings, and up-the-neck voice leading.

User Request:
- Chord Progression: {chords}
- Tuning: {tuning}
- Capo Position: {capo}
- Desired Style: {style}

Please provide:
1. **Up-the-Neck Voicings:** 2-3 logical, comfortable movable chord shapes higher up the fretboard that flow naturally into each other.
2. **Fret Diagrams:** Express these voicings clearly using tab/fret numbers relative to the capo/tuning.
3. **Custom Picking Tab:** Clean ASCII guitar tab for a 1-to-2 bar picking pattern.
4. **Playing Tip:** 1 specific tip on hand position or string transition."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"result": response.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
