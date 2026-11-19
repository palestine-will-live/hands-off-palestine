#!/usr/bin/env python3
"""Fail if index.html's title or paragraphs differ from the original markdown."""

import difflib
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKDOWN = ROOT / "original" / "hands-off-palestine.md"
PAGE = ROOT / "index.html"


def normalize(text):
    return " ".join(text.split())


def from_markdown(path):
    blocks = [b for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    title, *paragraphs = blocks
    if not title.startswith("# "):
        sys.exit(f"{path}: expected a '# ' title on the first line")
    return [normalize(title[2:])] + [normalize(p) for p in paragraphs]


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.current = None
        self.texts = []

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.depth += 1
        elif self.depth and (tag == "h1" or (tag == "p" and ("class", "author") not in attrs)):
            self.current = []

    def handle_endtag(self, tag):
        if tag == "article":
            self.depth -= 1
        elif self.current is not None and tag in ("h1", "p"):
            self.texts.append(normalize("".join(self.current)))
            self.current = None

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)


def from_page(path):
    parser = ArticleParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.texts


def main():
    expected = from_markdown(MARKDOWN)
    actual = from_page(PAGE)
    if expected == actual:
        print(f"index.html matches {MARKDOWN.relative_to(ROOT)} ({len(expected) - 1} paragraphs)")
        return 0
    diff = difflib.unified_diff(
        expected,
        actual,
        fromfile=str(MARKDOWN.relative_to(ROOT)),
        tofile=str(PAGE.relative_to(ROOT)),
        lineterm="",
    )
    print("\n".join(diff))
    return 1


if __name__ == "__main__":
    sys.exit(main())
