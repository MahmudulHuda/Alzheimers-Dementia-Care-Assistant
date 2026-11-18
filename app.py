from flask import Flask, jsonify, render_template, request

from careqa.assistant import Assistant
from careqa.lang import LANGS

app = Flask(__name__)
bot = Assistant()


@app.route("/")
def home():
    return render_template("index.html", available=bot.languages())


@app.post("/ask")
def ask():
    data = request.get_json(silent=True) or {}
    q = str(data.get("q", "")).strip()[:500]
    if not q:
        return jsonify(error="empty question"), 400
    lang = data.get("lang")
    return jsonify(bot.ask(q, lang if lang in LANGS else None))


@app.get("/examples")
def examples():
    lang = request.args.get("lang", "en")
    return jsonify(bot.examples(lang if lang in LANGS else "en"))


if __name__ == "__main__":
    if not bot.languages():
        print("No data found. Run: python scripts/fetch_data.py")
    app.run(host="127.0.0.1", port=5000, debug=False)
