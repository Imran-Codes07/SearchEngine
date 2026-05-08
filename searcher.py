"""
searcher.py
------------
Loads the index built by indexer.py and answers queries.

Supports:
- Plain keyword search (ranked by TF-IDF cosine similarity).
- Boolean operators: AND, OR, NOT (uppercase).
  Examples:
      python AND tutorial
      cat OR dog
      java NOT script
- A short snippet around the matched terms in the result.
"""

import difflib
import math
import pickle
import re
from collections import defaultdict

from indexer import tokenize, simple_stem


class SearchEngine:
    def __init__(self, index_file="data/index.pkl"):
        with open(index_file, "rb") as f:
            data = pickle.load(f)
        self.pages = data["pages"]
        self.inverted_index = data["inverted_index"]
        self.doc_lengths = data["doc_lengths"]
        self.idf = data["idf"]
        self.num_docs = data["num_docs"]
        self.title_tokens = data["title_tokens"]

    # ---------- Boolean parsing ----------

    def _docs_for_term(self, term):
        """Return the set of doc_ids that contain a given (already-stemmed) term."""
        return set(self.inverted_index.get(term, {}).keys())

    def _is_boolean_query(self, query):
        return any(op in query.split() for op in ("AND", "OR", "NOT"))

    def _boolean_search(self, query):
        """
        Very small boolean parser. Walks left to right.
        Supports a chain like: A AND B OR C NOT D
        """
        tokens = query.split()
        all_docs = set(range(self.num_docs))

        # Start with the first term
        first = simple_stem(tokens[0].lower())
        result = self._docs_for_term(first)
        i = 1
        while i < len(tokens) - 1:
            op = tokens[i].upper()
            term = simple_stem(tokens[i + 1].lower())
            term_docs = self._docs_for_term(term)
            if op == "AND":
                result = result & term_docs
            elif op == "OR":
                result = result | term_docs
            elif op == "NOT":
                result = result - term_docs
            else:
                # Unknown operator - ignore and treat as OR
                result = result | term_docs
            i += 2
        return result

    # ---------- Fuzzy expansion ----------

    def _fuzzy_expand_terms(self, query_terms):
        """
        For any query term not present in the index, look for similar
        indexed terms via substring overlap and edit-distance closeness.
        Returns the original terms plus up to 5 expansion terms.
        """
        index_terms = list(self.inverted_index.keys())
        expansions = []
        seen = set(query_terms)

        for term in query_terms:
            if term in self.inverted_index:
                continue

            candidates = []
            if len(term) >= 4:
                for idx_term in index_terms:
                    if len(idx_term) >= 4 and (term in idx_term or idx_term in term):
                        candidates.append(idx_term)

            close = difflib.get_close_matches(term, index_terms, n=5, cutoff=0.75)
            candidates.extend(close)

            for cand in candidates:
                if cand not in seen:
                    expansions.append(cand)
                    seen.add(cand)

        return query_terms + expansions[:5]

    # ---------- Ranking ----------

    def _rank(self, doc_ids, query_terms):
        """
        Score each doc_id using TF-IDF cosine-style scoring.
        Title matches get a small boost.
        """
        scores = defaultdict(float)
        query_term_set = set(query_terms)

        for term in query_terms:
            if term not in self.inverted_index:
                continue
            term_idf = self.idf.get(term, 0.0)
            for doc_id, tf in self.inverted_index[term].items():
                if doc_id not in doc_ids:
                    continue
                # Normalized TF * IDF
                normalized_tf = tf / self.doc_lengths[doc_id]
                scores[doc_id] += normalized_tf * term_idf

        # Title boost: if any query term appears in the title, multiply score
        for doc_id in list(scores.keys()):
            overlap = query_term_set & self.title_tokens.get(doc_id, set())
            if overlap:
                scores[doc_id] *= (1.0 + 0.5 * len(overlap))

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

    # ---------- Snippet ----------

    def _make_snippet(self, text, query_terms, length=200):
        """
        Find the first occurrence of any query term in the text,
        and return a window of characters around it. Highlights matches.
        """
        text_lower = text.lower()
        best_pos = -1
        for term in query_terms:
            # Try to find the un-stemmed form first by looking for the prefix
            pos = text_lower.find(term)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos
        if best_pos == -1:
            return text[:length] + ("..." if len(text) > length else "")

        start = max(0, best_pos - length // 3)
        end = min(len(text), start + length)
        snippet = text[start:end]
        if start > 0:
            snippet = "... " + snippet
        if end < len(text):
            snippet = snippet + " ..."

        # Highlight matches with <mark> tags (used by the web UI)
        for term in query_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            snippet = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", snippet)
        return snippet

    # ---------- Public API ----------

    def search(self, query, top_k=10):
        """
        Run a search. Returns a list of result dicts:
        [{url, title, snippet, score}, ...]
        """
        if not query.strip():
            return []

        if self._is_boolean_query(query):
            doc_ids = self._boolean_search(query)
            # For ranking, use only the non-operator terms
            query_terms = [
                simple_stem(t.lower())
                for t in query.split()
                if t.upper() not in ("AND", "OR", "NOT")
            ]
        else:
            query_terms = tokenize(query)
            query_terms = self._fuzzy_expand_terms(query_terms)
            # Candidate docs = any doc containing at least one term (OR semantics)
            doc_ids = set()
            for term in query_terms:
                doc_ids |= self._docs_for_term(term)

        if not doc_ids or not query_terms:
            return []

        ranked = self._rank(doc_ids, query_terms)[:top_k]

        # Build display results. Use the original (un-stemmed) words
        # from the query for snippet highlighting so it looks natural.
        display_terms = [
            t.lower() for t in re.findall(r"[a-zA-Z0-9]+", query)
            if t.upper() not in ("AND", "OR", "NOT")
        ]

        results = []
        for doc_id, score in ranked:
            page = self.pages[doc_id]
            results.append({
                "url": page["url"],
                "title": page["title"],
                "snippet": self._make_snippet(page["text"], display_terms),
                "score": round(score, 4),
            })
        return results


if __name__ == "__main__":
    engine = SearchEngine()
    print("Mini Search Engine - type a query (or 'quit'):")
    while True:
        q = input("> ").strip()
        if q.lower() in ("quit", "exit"):
            break
        results = engine.search(q)
        if not results:
            print("No results.\n")
            continue
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['title']}  (score={r['score']})")
            print(f"   {r['url']}")
            # Strip HTML tags for the CLI view
            clean = re.sub(r"</?mark>", "", r["snippet"])
            print(f"   {clean}\n")
