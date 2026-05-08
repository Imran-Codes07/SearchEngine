"""
indexer.py
-----------
Builds an inverted index from the crawled pages and computes TF-IDF scores.

Key concepts (you should know these for your viva):
- Tokenization: splitting text into words.
- Stemming: reducing words to their root (running -> run).
- Stop words: common words to ignore (the, is, at, ...).
- Inverted index: a dictionary mapping each word -> list of documents containing it.
- TF (Term Frequency): how often a word appears in a document.
- IDF (Inverse Document Frequency): how rare a word is across all documents.
- TF-IDF: TF * IDF. High score = important word in this document.
"""

import json
import math
import os
import pickle
import re
from collections import defaultdict, Counter

# A small built-in list of English stop words. No external NLTK download needed.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "while", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "should", "could", "may", "might", "must", "shall", "can", "of", "in", "on", "at",
    "to", "for", "with", "by", "from", "as", "into", "through", "during", "before",
    "after", "above", "below", "up", "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "just", "don", "now", "i", "me", "my", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "it", "its", "they", "them", "their", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "about"
}


def simple_stem(word):
    """
    A very small stemmer that strips common English suffixes.
    Not as good as the Porter stemmer, but it has zero dependencies.
    """
    if len(word) < 4:
        return word
    for suffix in ("ingly", "edly", "ing", "ed", "ly", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def tokenize(text):
    """
    Lowercase, split into words, remove stop words, and stem.
    Returns a list of clean tokens.
    """
    # Keep only letters and numbers, lowercase everything
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    tokens = []
    for w in words:
        if w in STOP_WORDS or len(w) < 2:
            continue
        tokens.append(simple_stem(w))
    return tokens


def build_index(pages_file="data/pages.json", index_file="data/index.pkl"):
    """
    Read crawled pages, tokenize them, build an inverted index,
    and compute IDF for every term. Save everything to disk.
    """
    with open(pages_file, "r", encoding="utf-8") as f:
        pages = json.load(f)

    num_docs = len(pages)
    print(f"[Indexer] Indexing {num_docs} documents...")

    # inverted_index[term] = {doc_id: term_frequency}
    inverted_index = defaultdict(dict)
    # doc_lengths[doc_id] = total tokens (for normalization)
    doc_lengths = {}
    # Also store the title text tokens separately so title matches rank higher
    title_tokens = {}

    for doc_id, page in enumerate(pages):
        tokens = tokenize(page["text"])
        title_toks = tokenize(page["title"])
        title_tokens[doc_id] = set(title_toks)

        token_counts = Counter(tokens)
        doc_lengths[doc_id] = max(sum(token_counts.values()), 1)

        for term, freq in token_counts.items():
            inverted_index[term][doc_id] = freq

    # Compute IDF: idf(term) = log(N / df(term))
    # where df(term) = number of documents containing the term
    idf = {}
    for term, postings in inverted_index.items():
        df = len(postings)
        idf[term] = math.log((num_docs + 1) / (df + 1)) + 1  # smoothed IDF

    index = {
        "pages": pages,            # the original documents (url, title, text)
        "inverted_index": dict(inverted_index),
        "doc_lengths": doc_lengths,
        "idf": idf,
        "num_docs": num_docs,
        "title_tokens": title_tokens,
    }

    os.makedirs(os.path.dirname(index_file), exist_ok=True)
    with open(index_file, "wb") as f:
        pickle.dump(index, f)

    print(f"[Indexer] Done. Index has {len(inverted_index)} unique terms.")
    print(f"[Indexer] Saved to {index_file}")
    return index


if __name__ == "__main__":
    build_index()
