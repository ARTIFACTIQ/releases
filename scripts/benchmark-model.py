#!/usr/bin/env python3
"""
Model Benchmarking Script for Artifactiq

Runs inference on test images and generates benchmark data for website.
Outputs JSON with detection results and timing metrics.

Usage:
    python scripts/benchmark-model.py --model artifactiq:v5.0.0 --images images/
    python scripts/benchmark-model.py --model ./path/to/model.onnx --images images/
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def run_artifactiq(model: str, image_path: str, confidence: float = 0.25) -> dict:
    """Run artifactiq analyze on a single image and parse results."""
    cmd = [
        "artifactiq", "analyze",
        "--input", image_path,
        "--model", model,
        "--confidence", str(confidence),
        "--output", "json"
    ]

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed_ms = (time.time() - start) * 1000

    if result.returncode != 0:
        return {
            "image": image_path,
            "error": result.stderr,
            "elapsed_ms": elapsed_ms,
            "detections": []
        }

    try:
        data = json.loads(result.stdout)
        return {
            "image": image_path,
            "elapsed_ms": elapsed_ms,
            "detections": data.get("detections", []),
            "count": len(data.get("detections", []))
        }
    except json.JSONDecodeError:
        return {
            "image": image_path,
            "error": "Failed to parse JSON output",
            "raw_output": result.stdout[:500],
            "elapsed_ms": elapsed_ms,
            "detections": []
        }


def benchmark_model(model: str, images_dir: str, confidence: float = 0.25) -> dict:
    """Run benchmark on all images in directory."""
    images_path = Path(images_dir)
    image_files = list(images_path.glob("*.jpg")) + list(images_path.glob("*.png"))

    results = []
    total_detections = 0
    total_time = 0

    for img in sorted(image_files):
        print(f"Processing {img.name}...", file=sys.stderr)
        result = run_artifactiq(model, str(img), confidence)
        results.append(result)
        total_detections += result.get("count", 0)
        total_time += result.get("elapsed_ms", 0)

    return {
        "model": model,
        "confidence_threshold": confidence,
        "total_images": len(image_files),
        "total_detections": total_detections,
        "total_time_ms": total_time,
        "avg_time_ms": total_time / len(image_files) if image_files else 0,
        "results": results
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Artifactiq model")
    parser.add_argument("--model", required=True, help="Model to benchmark (e.g., artifactiq:v5.0.0)")
    parser.add_argument("--images", required=True, help="Directory containing test images")
    parser.add_argument("--confidence", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--output", default="-", help="Output JSON file (- for stdout)")
    args = parser.parse_args()

    benchmark = benchmark_model(args.model, args.images, args.confidence)

    output_json = json.dumps(benchmark, indent=2)

    if args.output == "-":
        print(output_json)
    else:
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
