"""
crawler.py
-----------
A simple web crawler. Given a list of seed URLs, it visits pages,
extracts text and links, and saves everything to a JSON file.

How it works:
1. Start with seed URLs in a queue.
2. Pop a URL, download the HTML, extract title + visible text + links.
3. Add new links to the queue (up to a maximum page limit).
4. Save all pages to data/pages.json.
"""

import json
import os
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def is_valid_url(url):
    """Return True if the URL is a proper http/https URL."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc != ""


def extract_text(soup):
    """Get clean visible text from a BeautifulSoup object."""
    # Remove scripts, styles, navigation - they aren't real content
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    # Collapse whitespace
    return " ".join(text.split())


def crawl(seed_urls, max_pages=30, delay=0.5, output_file="data/pages.json"):
    """
    Crawl starting from seed_urls until max_pages is reached.
    Saves the result as a JSON list: [{url, title, text}, ...]
    """
    visited = set()
    queue = deque(seed_urls)
    pages = []

    headers = {
        "User-Agent": "SimpleSearchEngineBot/1.0 (Semester Project)"
    }

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited or not is_valid_url(url):
            continue
        visited.add(url)

        try:
            print(f"[Crawling] ({len(pages) + 1}/{max_pages}) {url}")
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code != 200:
                continue
            # Skip non-HTML content like PDFs and images
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            text = extract_text(soup)

            if len(text) < 100:
                # Skip pages with almost no content
                continue

            pages.append({
                "url": url,
                "title": title,
                "text": text
            })

            # Find links and add them to the queue
            for link in soup.find_all("a", href=True):
                full_url = urljoin(url, link["href"])
                # Strip the URL fragment (#section)
                full_url = full_url.split("#")[0]
                if full_url not in visited and is_valid_url(full_url):
                    queue.append(full_url)

            # Be polite - don't hammer servers
            time.sleep(delay)

        except Exception as e:
            print(f"  [Error] {e}")
            continue

    # Save to disk
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] Crawled {len(pages)} pages. Saved to {output_file}")
    return pages


if __name__ == "__main__":
    # Default seed URLs - small, well-known sites that are crawler-friendly
    seeds = [
        "https://en.wikipedia.org/wiki/Search_engine",
        "https://en.wikipedia.org/wiki/Information_retrieval",
        "https://en.wikipedia.org/wiki/Web_crawler",
        "https://en.wikipedia.org/wiki/Tf%E2%80%93idf",
        "https://en.wikipedia.org/wiki/PageRank",
        "https://en.wikipedia.org/wiki/Natural_language_processing",
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://en.wikipedia.org/wiki/Toothbrush",
        "https://en.wikipedia.org/wiki/Dental_hygiene",
        "https://en.wikipedia.org/wiki/Coffee",
        "https://en.wikipedia.org/wiki/Tea",
        "https://en.wikipedia.org/wiki/Dog",
        "https://en.wikipedia.org/wiki/Cat",
        "https://en.wikipedia.org/wiki/Football",
        "https://en.wikipedia.org/wiki/Cricket",
        "https://en.wikipedia.org/wiki/Pakistan",
        "https://en.wikipedia.org/wiki/Lahore",
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/JavaScript",
    ]
    crawl(seeds, max_pages=150)
