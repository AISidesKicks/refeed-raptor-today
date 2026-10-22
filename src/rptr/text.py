"""Small text normalizers shared by the model clients and the writer.

The project writes plain ASCII hyphens in HTML and docs. Local models sometimes
emit typographic dashes, so every generated string passes through here before
it reaches the reader.
"""

from __future__ import annotations

DASHES = str.maketrans(
    {
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2015": "-",  # horizontal bar
        "\u2212": "-",  # minus sign
        "\u2043": "-",  # hyphen bullet
    }
)


def plain_hyphens(text: str) -> str:
    return text.translate(DASHES)
