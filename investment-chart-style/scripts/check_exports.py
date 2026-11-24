"""Inspect exported chart files for presence, dimensions and readable structure."""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib.image as mpimg
import numpy as np


def check_directory(directory):
    records = []
    for png in sorted(directory.glob("*.png")):
        pixels = mpimg.imread(png)
        visible_rgb = pixels[..., :3]
        if pixels.ndim == 3 and pixels.shape[2] == 4:
            alpha = pixels[..., 3:4]
            visible_rgb = visible_rgb * alpha + (1 - alpha)
        record = {"stem": png.stem, "width": int(pixels.shape[1]), "height": int(pixels.shape[0]),
                  "nonwhite_fraction": float(np.mean(np.min(visible_rgb, axis=-1) < 0.97)), "errors": []}
        if record["width"] < 1200 or record["height"] < 700:
            record["errors"].append("PNG dimensions are smaller than the report preview target")
        if record["nonwhite_fraction"] < 0.005:
            record["errors"].append("PNG appears blank")
        for suffix in ("svg", "pdf"):
            path = png.with_suffix("." + suffix)
            if not path.exists():
                record["errors"].append(f"Missing {suffix} export")
                continue
            data = path.read_bytes()
            record[suffix + "_bytes"] = len(data)
            record[suffix + "_sha256"] = hashlib.sha256(data).hexdigest()
            if suffix == "svg":
                root = ET.fromstring(data)
                texts = list(root.iter("{http://www.w3.org/2000/svg}text"))
                record["svg_text_nodes"] = len(texts)
                if not texts:
                    record["errors"].append("SVG has no text nodes")
            elif not data.startswith(b"%PDF-"):
                record["errors"].append("Invalid PDF header")
        records.append(record)
    return {"figures": records, "passed": bool(records) and all(not item["errors"] for item in records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--report", type=Path)
    arguments = parser.parse_args()
    report = check_directory(arguments.directory)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.report:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(text, encoding="utf-8")
    print(text)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
