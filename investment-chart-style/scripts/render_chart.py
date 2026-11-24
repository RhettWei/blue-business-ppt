"""Render a supported investment chart from a JSON specification."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from chart_style import (
    export_figure, plot_heatmap, plot_lines, plot_ranked,
    plot_tail_distribution, plot_ternary, plot_violin, style_context,
)
from extended_patterns import DRAWERS, render_extended


CHART_TYPES = ("line", "ranked", "violin", "permutation", "ternary", "heatmap", *DRAWERS)


def render(specification, output):
    """Render a JSON chart specification and return its export manifest."""
    kind = specification["type"]
    data = specification["data"]
    if kind in DRAWERS or (kind == "ternary" and data.get("marginals", False)):
        return render_extended(specification, output)
    reference = specification.get("reference", 0)
    with style_context():
        fig, ax = plt.subplots(figsize=specification.get("figsize", [9, 5.5]))
        fig.subplots_adjust(left=0.15, right=0.92, bottom=0.26, top=0.83)
        statistics = {}
        if kind == "line":
            plot_lines(ax, data["x"], data["series"], specification.get("reference"))
        elif kind == "ranked":
            statistics = plot_ranked(ax, data["labels"], data["values"], data.get("lower"),
                                     data.get("upper"), reference, specification.get("unit", ""))
        elif kind == "violin":
            statistics = plot_violin(ax, data["groups"], data["labels"], reference, data.get("sort", True))
        elif kind == "permutation":
            statistics = plot_tail_distribution(ax, data["null_values"], data["observed"],
                                                data.get("side", "right"), data.get("bins", 30))
        elif kind == "ternary":
            statistics = plot_ternary(ax, data["probabilities"], data.get("labels"), data.get("normalize", False))
        elif kind == "heatmap":
            image = plot_heatmap(ax, data["matrix"], data["row_labels"], data["column_labels"],
                                 data.get("center", 0), data.get("vmin", -1), data.get("vmax", 1))
            fig.colorbar(image, ax=ax, fraction=0.04, pad=0.04)
        else:
            raise ValueError(f"Unsupported chart type: {kind}")
        ax.set_xlabel(specification.get("xlabel", ""))
        ax.set_ylabel(specification.get("ylabel", ax.get_ylabel()))
        fig.suptitle(specification["title"], x=0.065, y=0.95, ha="left", fontsize=17)
        result = export_figure(fig, output, specification.get("source", "用户提供的 JSON 图表规格"),
                               specification.get("note", ""), statistics)
        plt.close(fig)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specification", nargs="?", type=Path)
    parser.add_argument("--output", type=Path, help="Output filename stem")
    parser.add_argument("--list-types", action="store_true", help="List the 30 supported chart tasks")
    arguments = parser.parse_args()
    if arguments.list_types:
        print("\n".join(CHART_TYPES))
        return
    if arguments.specification is None or arguments.output is None:
        parser.error("A specification and --output are required when rendering")
    specification = json.loads(arguments.specification.read_text(encoding="utf-8-sig"))
    print(json.dumps(render(specification, arguments.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
