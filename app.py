from flask import Flask, render_template, send_file, request
from music_engine import generate_song

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate")
def generate():

    prompt = request.args.get("prompt", "")
    bpm = int(request.args.get("bpm", 90))
    key = request.args.get("key", "C")
    mode = request.args.get("mode", "major")

    instruments = request.args.getlist("instruments")

    print("----- SONG REQUEST -----")
    print("Prompt:", prompt)
    print("BPM:", bpm)
    print("Key:", key)
    print("Mode:", mode)
    print("Instruments:", instruments)
    print("-----------------------")

    # Create a filename based on the song settings
    instrument_text = "-".join(instruments) if instruments else "None"

    filename = (
        f"output/{key}-{mode}-{bpm}BPM-{instrument_text}.mid"
    )

    generate_song(
        filename,
        bpm=bpm,
        key=key,
        mode=mode,
        instruments=instruments,
        prompt=prompt
    )

    return send_file(
        filename,
        as_attachment=True,
        download_name=filename.split("/")[-1]
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )