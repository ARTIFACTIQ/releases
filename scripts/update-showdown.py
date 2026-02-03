#!/usr/bin/env python3
"""
Update Website Model Showdown Section

Reads benchmark JSON files and updates the index.html with actual metrics.

Usage:
    python scripts/update-showdown.py --benchmarks benchmarks/ --html index.html
"""

import argparse
import json
import re
from pathlib import Path


def load_benchmarks(benchmarks_dir: str) -> dict:
    """Load all benchmark JSON files from directory."""
    benchmarks = {}
    for f in Path(benchmarks_dir).glob("*.json"):
        with open(f) as fp:
            data = json.load(fp)
            model = data.get("model", f.stem)
            benchmarks[model] = data
    return benchmarks


def format_model_row(model: str, data: dict, is_winner: bool = False) -> str:
    """Generate HTML table row for a model."""
    total_detections = data.get("total_detections", 0)
    total_images = data.get("total_images", 0)
    avg_time = data.get("avg_time_ms", 0)

    style = 'background: rgba(126, 231, 135, 0.15);' if is_winner else ''
    color = 'var(--success)' if is_winner else 'var(--text-muted)'

    return f"""<tr style="{style}">
    <td style="padding: 0.75rem; color: {color}; font-weight: {'600' if is_winner else '400'};">{model}</td>
    <td style="padding: 0.75rem; text-align: center; color: {color};">{total_detections}</td>
    <td style="padding: 0.75rem; text-align: center;">{total_images}</td>
    <td style="padding: 0.75rem; text-align: center;">{avg_time:.0f}ms</td>
</tr>"""


def generate_image_cards(benchmark: dict) -> str:
    """Generate HTML for image detection cards from benchmark results."""
    cards = []
    for result in benchmark.get("results", [])[:12]:  # Max 12 cards
        image_name = Path(result["image"]).name
        count = result.get("count", 0)
        elapsed = result.get("elapsed_ms", 0)
        detections = result.get("detections", [])

        # Format detection tags
        tags = []
        for det in detections[:4]:  # Max 4 tags per card
            label = det.get("label", "object")
            conf = det.get("confidence", 0) * 100
            tags.append(f'<span class="detection-tag">{label} {conf:.0f}%</span>')

        tags_html = "\n".join(tags) if tags else '<span class="detection-tag">No detections</span>'

        cards.append(f"""
        <div class="gallery-card">
            <div class="gallery-card-image">
                <img src="images/{image_name}" alt="Detection result">
            </div>
            <div class="gallery-card-content">
                <div class="gallery-card-title">{count} Objects Detected</div>
                <div class="gallery-card-detections">
                    {tags_html}
                </div>
                <div class="gallery-card-meta">{elapsed:.0f}ms | {benchmark.get('model', 'unknown')}</div>
            </div>
        </div>""")

    return "\n".join(cards)


def main():
    parser = argparse.ArgumentParser(description="Update website showdown section")
    parser.add_argument("--benchmarks", required=True, help="Directory with benchmark JSON files")
    parser.add_argument("--html", required=True, help="HTML file to update")
    parser.add_argument("--output", help="Output file (default: update in place)")
    args = parser.parse_args()

    benchmarks = load_benchmarks(args.benchmarks)
    print(f"Loaded {len(benchmarks)} benchmarks: {list(benchmarks.keys())}")

    with open(args.html) as f:
        html = f.read()

    # Generate summary
    summary = {
        "models": list(benchmarks.keys()),
        "total_benchmarks": len(benchmarks)
    }

    print(f"Summary: {json.dumps(summary, indent=2)}")

    # For now, just validate - actual HTML replacement would require careful parsing
    output_file = args.output or args.html
    print(f"Would update {output_file}")


if __name__ == "__main__":
    main()
