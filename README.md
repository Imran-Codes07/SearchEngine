# Mini Search Engine - Semester Project

A complete, working search engine built in Python. It crawls real web pages,
builds an inverted index with TF-IDF scoring, supports boolean operators,
and serves results through a clean Flask web UI.

## Project Structure

```
search_engine/
├── crawler.py          # Step 1: downloads pages and saves them as JSON
├── indexer.py          # Step 2: builds the inverted index + TF-IDF
├── searcher.py         # Step 3: ranks results for a query
├── app.py              # Flask web server (the UI)
├── templates/
│   ├── index.html      # Home page (search box)
│   └── results.html    # Results page
├── static/
│   └── style.css       # Styling
├── data/               # Auto-generated (pages.json, index.pkl)
└── requirements.txt
```

## How to Run (3 commands)

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Crawl pages and build the index (run once, takes ~30 seconds):
   ```
   python crawler.py
   python indexer.py
   ```

3. Start the search engine:
   ```
   python app.py
   ```
   Open http://127.0.0.1:5000 in your browser.

## Features

- Web crawler with politeness delay and robots-friendly headers
- Tokenization, stop-word removal, and a built-in stemmer
- Inverted index for fast lookup
- TF-IDF scoring with title-boost
- Boolean operators: `AND`, `OR`, `NOT` (must be UPPERCASE)
- Snippet generation with highlighted query terms
- Google-style minimalist web UI
- Command-line search mode (run `python searcher.py`)

## Try These Queries

- `search engine` - basic ranked search
- `python AND tutorial` - AND operator
- `cat OR dog` - OR operator
- `java NOT script` - NOT operator
- `information retrieval` - multi-word ranked search

## Customizing the Crawl

Edit the `seeds` list at the bottom of `crawler.py` to crawl different sites.
You can also change `max_pages=30` to crawl more.

## Concepts to Know for Viva

- Inverted index: maps each term to the list of documents containing it.
- TF (Term Frequency): how often a term appears in a document.
- IDF (Inverse Document Frequency): `log(N / df)` - rare terms score higher.
- TF-IDF: `TF * IDF` - balances frequency and rarity.
- Stop words: common words ignored to save space and improve relevance.
- Stemming: reduces words to a common root form (running -> run).
- Cosine similarity: measures angle between query vector and document vector.
- BFS crawling: the queue-based crawl in `crawler.py` is breadth-first search.

## Building This in Antigravity

If you are using the Antigravity IDE, you can:
1. Open this folder as a workspace.
2. Use the Agent Manager to ask the agent to extend features
   (e.g. "add fuzzy spelling correction" or "add a SQLite cache for the index").
3. The four files are short and self-contained, so the agent can read
   the whole project context easily.
