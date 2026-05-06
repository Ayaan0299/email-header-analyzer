"""
Flask web app entrypoint for the Email Header Analyzer.

Routes:
  /        GET   -> renders the index page with the raw-header form
  /analyse POST  -> receives the raw header text, calls `analyse()` from
                   `analyzer.py`, and renders the results page

This file is intentionally minimal: request handling and template rendering
are done here; all parsing and DNS logic lives in `analyzer.py`.
"""

from flask import Flask, render_template, request
from analyzer import analyse

try:
    from database import get_stats, get_recent
    _db_available = True
except ImportError:
    _db_available = False

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    """Render the input page where users paste raw email headers.

    The template `templates/index.html` has the form which submits to
    `/analyse` via POST.
    """
    return render_template("index.html")


@app.route("/analyse", methods=["POST"])
def analyse_route():
    """Handle form POST, validate input, and call the analyzer.

    - Read `raw_header` from the form
    - If empty, re-render the index with an error banner
    - Otherwise call `analyse(raw_header)` and pass the returned
      dictionary into `results.html` for rendering.
    """
    raw_header = request.form.get("raw_header", "").strip()
    if not raw_header:
        return render_template("index.html", error="Please paste a raw email header.")
    # `analyse` returns a dict with parsed fields, checks, score, verdict, colour
    result = analyse(raw_header)
    return render_template("results.html", result=result)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not _db_available:
        return render_template("dashboard.html", stats=None, recent=[])
    try:
        stats  = get_stats()
        recent = get_recent(20)
    except Exception:
        stats  = None
        recent = []
    return render_template("dashboard.html", stats=stats, recent=recent)


if __name__ == "__main__":
    app.run(debug=True)
