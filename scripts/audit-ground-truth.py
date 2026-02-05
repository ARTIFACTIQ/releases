#!/usr/bin/env python3
"""Audit ground truth labels for quality issues.

This script identifies potentially mislabeled ground truth by:
1. Running a trusted model on validation images
2. Flagging cases where model confidently detects a different class than GT
3. Flagging images with suspicious label patterns
4. Generating a report for manual review

Usage:
    python audit-ground-truth.py --model models/e8_1_wavg_best.pt
    python audit-ground-truth.py --model models/e8_1_wavg_best.pt --output gt_audit.json
"""

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"


def calculate_iou(box1, box2):
    """Calculate IoU between two boxes in xywh format."""
    def xywh_to_xyxy(box):
        x, y, w, h = box
        return [x - w/2, y - h/2, x + w/2, y + h/2]

    b1, b2 = xywh_to_xyxy(box1), xywh_to_xyxy(box2)
    x1, y1 = max(b1[0], b2[0]), max(b1[1], b2[1])
    x2, y2 = min(b1[2], b2[2]), min(b1[3], b2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    area2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0


def load_class_names(yaml_path):
    """Load class names from dataset.yaml."""
    import yaml
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    names = config.get('names', [])
    if isinstance(names, list):
        return {i: name for i, name in enumerate(names)}
    return names


def parse_yolo_label(label_path, class_names):
    """Parse YOLO format label file."""
    annotations = []
    if not Path(label_path).exists():
        return annotations

    with open(label_path) as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split()
            if len(parts) >= 5:
                try:
                    class_id = int(parts[0])
                    bbox = [float(x) for x in parts[1:5]]

                    # Validate bbox values
                    issues = []
                    if not all(0 <= v <= 1 for v in bbox):
                        issues.append(f"bbox values out of [0,1] range: {bbox}")
                    if bbox[2] <= 0 or bbox[3] <= 0:
                        issues.append(f"invalid bbox dimensions: w={bbox[2]}, h={bbox[3]}")

                    annotations.append({
                        "class_id": class_id,
                        "class_name": class_names.get(class_id, f"unknown_{class_id}"),
                        "bbox": bbox,
                        "line_num": line_num,
                        "issues": issues
                    })
                except (ValueError, IndexError) as e:
                    annotations.append({
                        "class_id": -1,
                        "class_name": "PARSE_ERROR",
                        "bbox": [],
                        "line_num": line_num,
                        "issues": [f"Parse error: {e}"]
                    })

    return annotations


def audit_image(model, img_path, ground_truth, class_names, conf_threshold=0.5):
    """Audit a single image for GT quality issues."""
    issues = []

    # Run model inference
    results = model(str(img_path), conf=conf_threshold, verbose=False)

    detections = []
    for r in results:
        if r.boxes is not None:
            for box in r.boxes:
                detections.append({
                    "label": model.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xywhn[0].tolist()
                })

    # Check for label format issues
    for gt in ground_truth:
        if gt.get("issues"):
            for issue in gt["issues"]:
                issues.append({
                    "type": "format_error",
                    "severity": "high",
                    "description": issue,
                    "gt_class": gt["class_name"],
                    "line_num": gt["line_num"]
                })

    # Check for class mismatch: model confidently detects X, GT says Y
    for det in detections:
        if det["confidence"] < conf_threshold:
            continue

        # Find overlapping GT
        best_iou = 0
        best_gt = None
        for gt in ground_truth:
            if not gt["bbox"]:
                continue
            iou = calculate_iou(det["bbox"], gt["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_gt = gt

        if best_iou >= 0.3 and best_gt:  # Significant overlap
            det_class = det["label"].lower()
            gt_class = best_gt["class_name"].lower()

            # Check if classes are semantically different
            if det_class != gt_class:
                # Allow some reasonable mappings
                equivalent_classes = [
                    {"clothing", "dress", "suit", "jacket", "coat"},
                    {"footwear", "boot", "high heels", "sandal"},
                    {"bag", "handbag", "backpack", "briefcase", "luggage and bags"},
                ]

                is_equivalent = False
                for group in equivalent_classes:
                    if det_class in group and gt_class in group:
                        is_equivalent = True
                        break

                if not is_equivalent:
                    issues.append({
                        "type": "class_mismatch",
                        "severity": "high",
                        "description": f"Model detects '{det['label']}' ({det['confidence']*100:.1f}%), GT says '{best_gt['class_name']}'",
                        "model_class": det["label"],
                        "model_confidence": det["confidence"],
                        "gt_class": best_gt["class_name"],
                        "iou": best_iou
                    })

    # Check for missing GT: model confidently detects something with no GT overlap
    for det in detections:
        if det["confidence"] < conf_threshold:
            continue

        has_overlap = False
        for gt in ground_truth:
            if gt["bbox"] and calculate_iou(det["bbox"], gt["bbox"]) >= 0.3:
                has_overlap = True
                break

        if not has_overlap:
            issues.append({
                "type": "missing_gt",
                "severity": "medium",
                "description": f"Model detects '{det['label']}' ({det['confidence']*100:.1f}%) with no matching GT",
                "model_class": det["label"],
                "model_confidence": det["confidence"]
            })

    # Check for phantom GT: GT exists but model sees nothing there
    for gt in ground_truth:
        if not gt["bbox"]:
            continue

        has_detection = False
        for det in detections:
            if calculate_iou(det["bbox"], gt["bbox"]) >= 0.3:
                has_detection = True
                break

        if not has_detection and gt["class_name"] != "PARSE_ERROR":
            issues.append({
                "type": "phantom_gt",
                "severity": "low",
                "description": f"GT has '{gt['class_name']}' but model detects nothing there",
                "gt_class": gt["class_name"]
            })

    return {
        "detections": len(detections),
        "ground_truth_count": len(ground_truth),
        "issues": issues
    }


def main():
    parser = argparse.ArgumentParser(description="Audit ground truth labels")
    parser.add_argument("--model", required=True, help="Path to model file")
    parser.add_argument("--images", default="images/val", help="Validation images directory")
    parser.add_argument("--labels", default="data/val/labels", help="Labels directory")
    parser.add_argument("--dataset-yaml", default="data/dataset.yaml", help="Dataset YAML file")
    parser.add_argument("--output", default="gt_audit_report.json", help="Output report file")
    parser.add_argument("--confidence", type=float, default=0.5, help="Confidence threshold for flagging")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of images (0 = all)")
    args = parser.parse_args()

    from ultralytics import YOLO

    print("=" * 60)
    print("Ground Truth Audit")
    print("=" * 60)

    # Load model and class names
    print(f"\nLoading model: {args.model}")
    model = YOLO(args.model)

    print(f"Loading class names: {args.dataset_yaml}")
    class_names = load_class_names(args.dataset_yaml)
    print(f"  {len(class_names)} classes loaded")

    # Find images
    images_dir = Path(args.images)
    labels_dir = Path(args.labels)
    all_images = sorted(images_dir.glob("*"))

    if args.limit > 0:
        all_images = all_images[:args.limit]

    print(f"\nAuditing {len(all_images)} images (conf threshold: {args.confidence})")

    # Audit each image
    report = {
        "generated_at": datetime.now().isoformat(),
        "model": args.model,
        "confidence_threshold": args.confidence,
        "total_images": len(all_images),
        "summary": {
            "images_with_issues": 0,
            "total_issues": 0,
            "by_severity": {"high": 0, "medium": 0, "low": 0},
            "by_type": defaultdict(int)
        },
        "flagged_images": []
    }

    for idx, img_path in enumerate(all_images):
        if idx % 100 == 0:
            print(f"  [{idx+1}/{len(all_images)}] Processing...")

        # Load ground truth
        label_path = labels_dir / (img_path.stem + ".txt")
        ground_truth = parse_yolo_label(label_path, class_names)

        # Audit
        result = audit_image(model, img_path, ground_truth, class_names, args.confidence)

        if result["issues"]:
            report["summary"]["images_with_issues"] += 1
            report["summary"]["total_issues"] += len(result["issues"])

            for issue in result["issues"]:
                report["summary"]["by_severity"][issue["severity"]] += 1
                report["summary"]["by_type"][issue["type"]] += 1

            report["flagged_images"].append({
                "filename": img_path.name,
                "ground_truth_count": result["ground_truth_count"],
                "model_detections": result["detections"],
                "issues": result["issues"]
            })

    # Convert defaultdict for JSON
    report["summary"]["by_type"] = dict(report["summary"]["by_type"])

    # Sort flagged images by issue count (most issues first)
    report["flagged_images"].sort(key=lambda x: len(x["issues"]), reverse=True)

    # Save report
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total images: {report['total_images']}")
    print(f"Images with issues: {report['summary']['images_with_issues']}")
    print(f"Total issues: {report['summary']['total_issues']}")
    print(f"\nBy severity:")
    for severity, count in report["summary"]["by_severity"].items():
        print(f"  {severity}: {count}")
    print(f"\nBy type:")
    for issue_type, count in report["summary"]["by_type"].items():
        print(f"  {issue_type}: {count}")

    print(f"\nReport saved: {args.output}")

    # Show top flagged images
    if report["flagged_images"]:
        print(f"\nTop 10 most problematic images:")
        for img in report["flagged_images"][:10]:
            high_count = sum(1 for i in img["issues"] if i["severity"] == "high")
            print(f"  {img['filename']}: {len(img['issues'])} issues ({high_count} high)")


if __name__ == "__main__":
    main()
