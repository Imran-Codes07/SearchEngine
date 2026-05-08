"""
app.py
-------
A Flask web app that gives a Google-like UI for the search engine.

Run it:
    python app.py
Then open: http://127.0.0.1:5000
"""

import time
from flask import Flask, render_template, request

from searcher import SearchEngine

app = Flask(__name__)

# Load the index once at startup (fast searches afterwards)
try:
    print("Loading index...")
    engine = SearchEngine()
    print(f"Index loaded. {engine.num_docs} documents indexed.")
except FileNotFoundError:
    engine = None
    print("[Warning] Index file not found. Run crawler.py and indexer.py to build it.")


INDEX_MISSING_MESSAGE = (
    "Index not found. Run crawler.py and indexer.py locally, then redeploy."
)


@app.route("/")
def home():
    if engine is None:
        return INDEX_MISSING_MESSAGE
    return render_template("index.html")


@app.route("/search")
def search():
    if engine is None:
        return INDEX_MISSING_MESSAGE
    query = request.args.get("q", "").strip()
    if not query:
        return render_template("index.html")
    start = time.time()
    results = engine.search(query, top_k=15)
    elapsed = round(time.time() - start, 4)
    return render_template(
        "results.html",
        query=query,
        results=results,
        elapsed=elapsed,
        total=len(results),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
