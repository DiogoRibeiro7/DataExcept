"""Write a coverage badge SVG, without depending on coverage-badge.

``coverage-badge`` imports ``pkg_resources``, which setuptools 81 removed, so
using it meant pinning ``setuptools<81`` -- and that pin pulled in a
moderate-severity advisory flagged by dependency review. Its last release was
August 2024. The badge is a small SVG, so generating it here removes the
dependency, the pin and the advisory together.

Usage:
    python scripts/coverage_badge.py [-o coverage.svg]
"""

from __future__ import annotations

import argparse
import subprocess
import sys

# Thresholds and colours match what coverage-badge produced, so the badge does
# not visibly change.
COLOURS = [
    (95, "#4c1"),  # brightgreen
    (90, "#97CA00"),  # green
    (75, "#a4a61d"),  # yellowgreen
    (60, "#dfb317"),  # yellow
    (40, "#fe7d37"),  # orange
    (0, "#e05d44"),  # red
]

TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
    <linearGradient id="b" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <mask id="a">
        <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
    </mask>
    <g mask="url(#a)">
        <path fill="#555" d="M0 0h{label_width}v20H0z"/>
        <path fill="{colour}" d="M{label_width} 0h{value_width}v20H{label_width}z"/>
        <path fill="url(#b)" d="M0 0h{total_width}v20H0z"/>
    </g>
    <g fill="#fff" text-anchor="middle" \
font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="{label_x}" y="15" fill="#010101" fill-opacity=".3">coverage</text>
        <text x="{label_x}" y="14">coverage</text>
        <text x="{value_x}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
        <text x="{value_x}" y="14">{value}</text>
    </g>
</svg>
"""

LABEL_WIDTH = 63  # "coverage" at font-size 11, as coverage-badge rendered it


def colour_for(percentage: int) -> str:
    for threshold, colour in COLOURS:
        if percentage >= threshold:
            return colour
    return COLOURS[-1][1]


def total_coverage() -> int:
    """Read the combined coverage percentage from the coverage data file."""
    result = subprocess.run(
        [sys.executable, "-m", "coverage", "report", "--format=total"],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout.strip())


def render(percentage: int) -> str:
    value = f"{percentage}%"
    # coverage-badge allotted 12px per character for the right-hand box.
    # Matching it keeps the rendered badge identical to the published one.
    value_width = 12 * len(value)
    total_width = LABEL_WIDTH + value_width
    return TEMPLATE.format(
        total_width=total_width,
        label_width=LABEL_WIDTH,
        value_width=value_width,
        colour=colour_for(percentage),
        label_x=round(LABEL_WIDTH / 2, 1),
        value_x=LABEL_WIDTH + value_width // 2 - 1,
        value=value,
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="coverage_badge", description=__doc__)
    parser.add_argument("-o", "--output", default="coverage.svg")
    args = parser.parse_args()

    percentage = total_coverage()
    with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render(percentage))
    print(f"Wrote {args.output} at {percentage}% coverage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
