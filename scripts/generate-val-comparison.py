#!/usr/bin/env python3
"""Generate model comparison using validation dataset for transparency.

Uses actual validation set with ground truth labels to show:
- Where models succeed and fail
- Honest comparison against known annotations
- Per-class performance breakdown

Usage:
    python generate-val-comparison.py [--sample-size 700] [--confidence 0.1]
"""

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path

# Paths
VAL_IMAGES_DIR = "/Users/shaileshpant/src/orgs/artifactiq-models/runs/merged_all_datasets/images/val"
VAL_LABELS_DIR = "/Users/shaileshpant/src/orgs/artifactiq-models/runs/merged_all_datasets/labels/val"
DATASET_YAML = "/Users/shaileshpant/src/orgs/artifactiq-models/runs/merged_all_datasets/dataset.yaml"
PRODUCTION_DIR = "/Users/shaileshpant/src/orgs/artifactiq/ml-models/training/runs/production"
MANIFEST_FILE = f"{PRODUCTION_DIR}/release_manifest.json"


def load_models_config():
    """Load models configuration dynamically from manifest."""
    models = {
        "stock_yolov8n": {
            "path": "yolov8n.pt",
            "name": "Stock YOLOv8n",
            "version": "8.0.0",
            "type": "baseline",
            "classes": 80,
            "dataset": "COCO",
            "color": "#888888"
        }
    }

    # Load current production model from manifest
    manifest_path = Path(MANIFEST_FILE)
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

        if manifest.get("current") and manifest.get("releases"):
            # Find current release
            current_id = manifest["current"]
            current_release = next(
                (r for r in manifest["releases"] if r["model_id"] == current_id),
                None
            )
            if current_release:
                models[current_id] = {
                    "path": current_release.get("file", f"{PRODUCTION_DIR}/current_best.pt"),
                    "name": f"Artifactiq {current_release['name']}",
                    "version": current_release["version"],
                    "type": "custom",
                    "classes": 39,
                    "dataset": "Open Images V7",
                    "mAP50": current_release.get("mAP50", 0),
                    "color": "#3b82f6",
                    "is_current": True,
                    "note": current_release.get("note", "")
                }
                return models

    # Fallback: use hardcoded current model if no manifest
    current_best = Path(PRODUCTION_DIR) / "current_best.pt"
    if current_best.exists():
        models["artifactiq_current"] = {
            "path": str(current_best),
            "name": "Artifactiq (Current)",
            "version": "latest",
            "type": "custom",
            "classes": 39,
            "dataset": "Open Images V7",
            "color": "#3b82f6",
            "is_current": True
        }
    else:
        # Final fallback to E8
        models["artifactiq_e8"] = {
            "path": f"{PRODUCTION_DIR}/e8_best.pt",
            "name": "Artifactiq E8",
            "version": "v6.0.0",
            "type": "custom",
            "classes": 39,
            "dataset": "Open Images V7",
            "mAP50": 0.1035,
            "color": "#3b82f6",
            "is_current": True,
            "note": "Calibrated training with val=True"
        }

    return models


# Load models dynamically
MODELS = load_models_config()

def load_class_names():
    """Load class names from dataset.yaml"""
    import yaml
    with open(DATASET_YAML) as f:
        config = yaml.safe_load(f)
    names = config.get('names', [])
    # Convert list to dict if needed
    if isinstance(names, list):
        return {i: name for i, name in enumerate(names)}
    return names

def parse_yolo_label(label_path, class_names):
    """Parse YOLO format label file."""
    annotations = []
    if not Path(label_path).exists():
        return annotations

    with open(label_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                # YOLO format: class_id, x_center, y_center, width, height (normalized)
                annotations.append({
                    "class_id": class_id,
                    "class_name": class_names.get(class_id, f"class_{class_id}"),
                    "bbox": [float(x) for x in parts[1:5]]
                })
    return annotations

def run_inference(model, image_path, confidence=0.1):
    """Run inference and return detections."""
    import time

    start = time.time()
    results = model(image_path, conf=confidence, verbose=False)
    elapsed_ms = int((time.time() - start) * 1000)

    detections = []
    for r in results:
        if r.boxes is not None:
            for box in r.boxes:
                label = model.names[int(box.cls)]
                conf = float(box.conf)
                bbox = box.xywhn[0].tolist()  # normalized xywh
                detections.append({
                    "label": label,
                    "confidence": round(conf, 4),
                    "bbox": bbox
                })

    detections.sort(key=lambda x: x["confidence"], reverse=True)
    return {
        "count": len(detections),
        "processing_time_ms": elapsed_ms,
        "detections": detections
    }

def calculate_iou(box1, box2):
    """Calculate IoU between two boxes in xywh format."""
    # Convert xywh to xyxy
    def xywh_to_xyxy(box):
        x, y, w, h = box
        return [x - w/2, y - h/2, x + w/2, y + h/2]

    b1 = xywh_to_xyxy(box1)
    b2 = xywh_to_xyxy(box2)

    # Intersection
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)

    # Union
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0

def evaluate_detections(detections, ground_truth, iou_threshold=0.5):
    """Compare detections against ground truth."""
    matched_gt = set()
    true_positives = []
    false_positives = []

    for det in detections:
        best_iou = 0
        best_gt_idx = -1

        for i, gt in enumerate(ground_truth):
            if i in matched_gt:
                continue
            iou = calculate_iou(det["bbox"], gt["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = i

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            matched_gt.add(best_gt_idx)
            true_positives.append({
                **det,
                "matched_gt": ground_truth[best_gt_idx]["class_name"],
                "iou": round(best_iou, 3)
            })
        else:
            false_positives.append(det)

    # Missed ground truth (false negatives)
    false_negatives = [
        ground_truth[i] for i in range(len(ground_truth)) if i not in matched_gt
    ]

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": len(true_positives) / len(detections) if detections else 0,
        "recall": len(true_positives) / len(ground_truth) if ground_truth else 0
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=700, help="Number of images to sample")
    parser.add_argument("--confidence", type=float, default=0.1, help="Confidence threshold")
    parser.add_argument("--output", default="../src/data/val-comparison-results.json")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    print(f"Loading models...")
    from ultralytics import YOLO

    models = {}
    for model_id, config in MODELS.items():
        model_path = config["path"]
        if not model_path.startswith("yolo") and not Path(model_path).exists():
            print(f"  ⚠️  {config['name']}: Model not found at {model_path}")
            continue
        print(f"  Loading {config['name']}...")
        models[model_id] = YOLO(model_path)

    if not models:
        print("No models loaded!")
        return

    # Load class names
    class_names = load_class_names()
    print(f"Loaded {len(class_names)} class names")

    # Sample images
    all_images = sorted(Path(VAL_IMAGES_DIR).glob("*"))
    sample_size = min(args.sample_size, len(all_images))
    sampled_images = random.sample(all_images, sample_size)
    print(f"Sampled {sample_size} images from {len(all_images)} validation images")

    # Initialize output
    output = {
        "schema_version": "3.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_source": "validation_set",
        "benchmark_config": {
            "validation_set": VAL_IMAGES_DIR,
            "total_val_images": len(all_images),
            "sample_size": sample_size,
            "sample_percentage": round(sample_size / len(all_images) * 100, 1),
            "confidence_threshold": args.confidence,
            "iou_threshold": 0.5,
            "random_seed": args.seed
        },
        "models": {mid: {k: v for k, v in cfg.items() if k != "path"} for mid, cfg in MODELS.items() if mid in models},
        "ground_truth_classes": class_names,
        "summary": {mid: {
            "total_detections": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "precision": 0,
            "recall": 0,
            "by_class": {}
        } for mid in models},
        "images": []
    }

    # Process images
    start_time = time.time()
    for idx, img_path in enumerate(sampled_images):
        if idx % 50 == 0:
            elapsed = time.time() - start_time
            eta = (elapsed / (idx + 1)) * (sample_size - idx - 1) if idx > 0 else 0
            print(f"[{idx+1}/{sample_size}] Processing... (ETA: {eta/60:.1f} min)")

        # Load ground truth
        label_path = Path(VAL_LABELS_DIR) / (img_path.stem + ".txt")
        ground_truth = parse_yolo_label(label_path, class_names)

        image_result = {
            "filename": img_path.name,
            "ground_truth": {
                "count": len(ground_truth),
                "classes": list(set(gt["class_name"] for gt in ground_truth))
            },
            "results": {}
        }

        # Run each model
        for model_id, model in models.items():
            try:
                inference = run_inference(model, str(img_path), args.confidence)
                evaluation = evaluate_detections(inference["detections"], ground_truth)

                image_result["results"][model_id] = {
                    "count": inference["count"],
                    "processing_time_ms": inference["processing_time_ms"],
                    "detections": inference["detections"][:10],  # Top 10 only for JSON size
                    "evaluation": {
                        "true_positives": len(evaluation["true_positives"]),
                        "false_positives": len(evaluation["false_positives"]),
                        "false_negatives": len(evaluation["false_negatives"]),
                        "precision": round(evaluation["precision"], 3),
                        "recall": round(evaluation["recall"], 3)
                    }
                }

                # Update summary
                output["summary"][model_id]["total_detections"] += inference["count"]
                output["summary"][model_id]["true_positives"] += len(evaluation["true_positives"])
                output["summary"][model_id]["false_positives"] += len(evaluation["false_positives"])
                output["summary"][model_id]["false_negatives"] += len(evaluation["false_negatives"])

            except Exception as e:
                print(f"  Error on {img_path.name} with {model_id}: {e}")
                image_result["results"][model_id] = {"error": str(e)}

        output["images"].append(image_result)

    # Calculate final summary metrics
    for model_id in models:
        s = output["summary"][model_id]
        total_gt = s["true_positives"] + s["false_negatives"]
        total_det = s["true_positives"] + s["false_positives"]
        s["precision"] = round(s["true_positives"] / total_det, 4) if total_det > 0 else 0
        s["recall"] = round(s["true_positives"] / total_gt, 4) if total_gt > 0 else 0
        s["f1"] = round(2 * s["precision"] * s["recall"] / (s["precision"] + s["recall"]), 4) if (s["precision"] + s["recall"]) > 0 else 0

    # Save output
    output_path = Path(__file__).parent / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    elapsed_total = time.time() - start_time
    print(f"\n✅ Done in {elapsed_total/60:.1f} minutes")
    print(f"📄 Saved to: {output_path}")

    # Print summary
    print("\n📊 Summary:")
    for model_id, s in output["summary"].items():
        model_name = output["models"][model_id]["name"]
        print(f"\n  {model_name}:")
        print(f"    Detections: {s['total_detections']}")
        print(f"    True Positives: {s['true_positives']}")
        print(f"    False Positives: {s['false_positives']}")
        print(f"    False Negatives: {s['false_negatives']}")
        print(f"    Precision: {s['precision']*100:.2f}%")
        print(f"    Recall: {s['recall']*100:.2f}%")
        print(f"    F1: {s['f1']*100:.2f}%")

if __name__ == "__main__":
    main()
