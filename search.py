"""Plain text of an issue page, for the archive's search index.

The archive page filters issues in the browser, with no server and no search
library. The build gives it a small JSON index that includes the readable text
of each issue, so a word that appears anywhere in an issue, such as
"Hot Corner" or "rubric", finds it.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

# Skipped: scripts and styles aren't words on the page, SVG holds only icon
# paths, and the only buttons in an issue are "Pause animations" controls,
# which would otherwise make every issue match a search for "pause".
SKIPPED_TAGS = {"script", "style", "svg", "button"}


class _MainText(HTMLParser):
    """Collects the visible text inside <main>, skipping scripts and styles.

    Screen-reader-only text (like "Command" inside a ⌘ keycap) is kept on
    purpose, so searching "command q" finds the issue that teaches ⌃⌘Q.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._in_main = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main":
            self._in_main = True
        elif tag in SKIPPED_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "main":
            self._in_main = False
        elif tag in SKIPPED_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_main and not self._skip_depth:
            self.parts.append(data)


def page_text(html: str) -> str:
    """The words a reader sees in the page's <main>, as one line of text."""
    parser = _MainText()
    parser.feed(html)
    parser.close()
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
