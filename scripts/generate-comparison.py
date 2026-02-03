#!/usr/bin/env python3
"""Generate model comparison JSON for website transparency.

Runs inference on showcase images with multiple models and outputs
structured JSON for dynamic website rendering.

Usage:
    python generate-comparison.py [--models stock,e7] [--images-dir ../images]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Model configurations
MODELS = {
    "stock_yolov8n": {
        "path": "yolov8n.pt",  # Downloaded automatically by ultralytics
        "name": "Stock YOLOv8n",
        "version": "8.0.0",
        "type": "baseline",
        "classes": 80,
        "dataset": "COCO",
        "color": "#888888"
    },
    "artifactiq_e7": {
        "path": "/Users/shaileshpant/src/orgs/artifactiq/ml-models/training/runs/production/e7_best.pt",
        "name": "Artifactiq E7",
        "version": "v5.0.0",
        "type": "custom",
        "classes": 39,
        "dataset": "Open Images V7",
        "mAP50": 0.001454,
        "color": "#10b981",
        "is_current": True
    },
    "artifactiq_e8": {
        "path": "/Users/shaileshpant/src/orgs/artifactiq/ml-models/training/runs/e8_calibrated/shard_45/weights/best.pt",
        "name": "Artifactiq E8",
        "version": "v6.0.0",
        "type": "custom",
        "classes": 39,
        "dataset": "Open Images V7",
        "color": "#3b82f6"
    }
}

# Class categories for analysis
CLASS_CATEGORIES = {
    "apparel": ["Clothing", "Dress", "Suit", "Jacket", "Coat", "Jeans", "Shorts", "Skirt", "Swimwear", "Miniskirt", "clothing", "dress", "suit", "jacket", "coat", "jeans", "shorts", "skirt"],
    "footwear": ["Footwear", "Boot", "High heels", "Sandal", "footwear", "boot", "sandal"],
    "accessories": ["Watch", "Sunglasses", "Hat", "Tie", "Belt", "Scarf", "Glasses", "watch", "sunglasses", "hat", "tie", "belt", "scarf", "glasses", "umbrella"],
    "bags": ["Backpack", "Handbag", "Suitcase", "Briefcase", "backpack", "handbag", "suitcase", "briefcase"],
    "people": ["Person", "Man", "Woman", "Boy", "Girl", "person", "man", "woman"],
    "vehicles": ["Car", "Bus", "Motorcycle", "Bicycle", "car", "bus", "motorcycle", "bicycle", "truck"],
}


def categorize_detection(label):
    """Categorize a detection label."""
    label_lower = label.lower()
    for category, labels in CLASS_CATEGORIES.items():
        if label in labels or label_lower in [l.lower() for l in labels]:
            return category
    return "other"


def run_inference(model_path, image_path, confidence=0.1):
    """Run inference on a single image."""
    from ultralytics import YOLO
    import time

    model = YOLO(model_path)

    start = time.time()
    results = model(image_path, conf=confidence, verbose=False)
    elapsed_ms = int((time.time() - start) * 1000)

    detections = []
    for r in results:
        if r.boxes is not None:
            for box in r.boxes:
                label = model.names[int(box.cls)]
                conf = float(box.conf)
                detections.append({
                    "label": label,
                    "confidence": round(conf, 4),
                    "category": categorize_detection(label)
                })

    # Sort by confidence
    detections.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "count": len(detections),
        "processing_time_ms": elapsed_ms,
        "detections": detections
    }


def generate_comparison(models_to_run, images_dir, output_path, confidence=0.1):
    """Generate comparison JSON for all models and images."""

    images_dir = Path(images_dir)
    image_files = sorted([
        f for f in images_dir.glob("*.webp")
    ] + [
        f for f in images_dir.glob("*.jpg")
        if not f.name.startswith("detected_")
    ])

    print(f"Found {len(image_files)} images")
    print(f"Running models: {', '.join(models_to_run)}")

    # Build output structure
    output = {
        "schema_version": "2.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "benchmark_config": {
            "confidence_threshold": confidence,
            "iou_threshold": 0.45,
            "image_count": len(image_files)
        },
        "models": {},
        "images": [],
        "summary": {}
    }

    # Add model metadata
    for model_id in models_to_run:
        if model_id in MODELS:
            config = MODELS[model_id].copy()
            config.pop("path", None)  # Don't expose local paths
            output["models"][model_id] = config

    # Initialize summary counters
    for model_id in models_to_run:
        output["summary"][model_id] = {
            "total_detections": 0,
            "by_category": {cat: 0 for cat in CLASS_CATEGORIES.keys()}
        }
        output["summary"][model_id]["by_category"]["other"] = 0

    # Run inference on each image
    for img_path in image_files:
        print(f"\nProcessing: {img_path.name}")

        image_result = {
            "filename": img_path.name,
            "results": {}
        }

        for model_id in models_to_run:
            if model_id not in MODELS:
                print(f"  Skipping unknown model: {model_id}")
                continue

            model_path = MODELS[model_id]["path"]

            # Check if model exists
            if not model_path.startswith("yolo") and not Path(model_path).exists():
                print(f"  Model not found: {model_path}")
                image_result["results"][model_id] = {
                    "count": 0,
                    "processing_time_ms": 0,
                    "detections": [],
                    "error": "Model not found"
                }
                continue

            print(f"  Running {MODELS[model_id]['name']}...", end=" ")
            try:
                result = run_inference(model_path, str(img_path), confidence)
                image_result["results"][model_id] = result
                print(f"{result['count']} detections ({result['processing_time_ms']}ms)")

                # Update summary
                output["summary"][model_id]["total_detections"] += result["count"]
                for det in result["detections"]:
                    cat = det["category"]
                    output["summary"][model_id]["by_category"][cat] += 1

            except Exception as e:
                print(f"ERROR: {e}")
                image_result["results"][model_id] = {
                    "count": 0,
                    "processing_time_ms": 0,
                    "detections": [],
                    "error": str(e)
                }

        output["images"].append(image_result)

    # Write output
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Comparison saved to: {output_path}")

    # Print summary
    print("\n📊 Summary:")
    for model_id, summary in output["summary"].items():
        model_name = output["models"].get(model_id, {}).get("name", model_id)
        print(f"\n  {model_name}:")
        print(f"    Total: {summary['total_detections']} detections")
        for cat, count in summary["by_category"].items():
            if count > 0:
                print(f"    {cat}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Generate model comparison JSON")
    parser.add_argument("--models", default="stock_yolov8n,artifactiq_e7",
                       help="Comma-separated model IDs to compare")
    parser.add_argument("--images-dir", default="../images",
                       help="Directory containing test images")
    parser.add_argument("--output", default="../src/data/model-comparison-results.json",
                       help="Output JSON path")
    parser.add_argument("--confidence", type=float, default=0.1,
                       help="Confidence threshold")

    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]

    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    images_dir = (script_dir / args.images_dir).resolve()
    output_path = (script_dir / args.output).resolve()

    generate_comparison(models, images_dir, output_path, args.confidence)


if __name__ == "__main__":
    main()
