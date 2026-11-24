"""Reusable plotting primitives for the reference-derived investment chart style."""

import json
from contextlib import contextmanager
from pathlib import Path
import textwrap

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Polygon
import numpy as np
from layout_audit import inspect_layout


COLORS = {
    "blue": "#5E86A6", "blue_light": "#D6E4EE",
    "gold": "#D4A14C", "gold_light": "#FAE7BE", "gold_text": "#997025",
    "green": "#91AF96", "green_light": "#DEEADD",
    "navy": "#183C55", "text": "#202830", "muted": "#59636C",
    "gray": "#B9BEC2", "grid": "#E4E8EB",
}
SERIES_COLORS = [COLORS[k] for k in ("blue", "gold", "green", "navy", "gray")]


@contextmanager
def style_context():
    """Apply scoped styles, choosing installed Latin and Chinese font families."""
    available = {font.name for font in font_manager.fontManager.ttflist}
    candidates = ["Arial", "Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "DejaVu Sans"]
    fonts = [name for name in candidates if name in available]
    with mpl.rc_context({
        "font.family": fonts, "font.sans-serif": fonts,
        "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "normal",
        "axes.labelsize": 11.5, "axes.labelcolor": COLORS["text"],
        "text.color": COLORS["text"], "xtick.color": COLORS["muted"],
        "ytick.color": COLORS["muted"], "xtick.labelsize": 10,
        "ytick.labelsize": 10, "legend.fontsize": 10, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.7, "axes.unicode_minus": False,
        "axes.axisbelow": True, "lines.linewidth": 1.7,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "savefig.dpi": 300,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "svg.hashsalt": "investment-chart-style", "mathtext.fontset": "dejavusans",
    }):
        yield


def format_axis(ax, grid="y"):
    """Set thin axes and a light grid along the quantitative comparison axis."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(COLORS["muted"])
    ax.tick_params(length=3, width=0.6, pad=5)
    ax.grid(False)
    if grid:
        ax.grid(axis=grid, color=COLORS["grid"], linestyle=(0, (3, 3)), linewidth=0.65)


def export_figure(fig, stem, source, note="", statistics=None, dpi=300):
    """Export PNG, text-preserving SVG, PDF and source/statistic metadata."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    footer = "\n".join(filter(None, [source, note]))
    footer = "\n".join(textwrap.fill(line, width=105) for line in footer.splitlines())
    fig.text(0.065, 0.025, footer, fontsize=8.5, color=COLORS["muted"], va="bottom")
    layout_report = inspect_layout(fig)
    files = []
    for suffix in ("png", "svg", "pdf"):
        path = stem.with_suffix("." + suffix)
        fig.savefig(path, dpi=dpi, bbox_inches=None)
        files.append(path.name)
    record = {
        "files": files, "source": source, "note": note,
        "width_inches": float(fig.get_figwidth()),
        "height_inches": float(fig.get_figheight()),
        "png_dpi": dpi, "statistics": statistics or {}, "layout": layout_report,
    }
    stem.with_suffix(".json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    return record


def _finite_vector(values, name):
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a nonempty finite one-dimensional array")
    return array


def plot_lines(ax, x, series, reference=None):
    """Plot supplied series, preserving NaN gaps and optional uncertainty bands."""
    if not len(x) or not series:
        raise ValueError("Line charts require x values and at least one series")
    format_axis(ax)
    markers = ["o", "s", "D", "^", "v"]
    for i, item in enumerate(series):
        y = np.asarray(item["y"], dtype=float)
        if y.ndim != 1 or len(y) != len(x) or np.isinf(y).any() or not np.isfinite(y).any():
            raise ValueError("Every y array must match x and contain finite values or NaN gaps")
        color = item.get("color", SERIES_COLORS[i % len(SERIES_COLORS)])
        ax.plot(x, y, color=color, label=item["name"], marker=markers[i % len(markers)],
                markersize=3.5, markevery=max(1, len(y) // 10), zorder=3)
        if "lower" in item or "upper" in item:
            lower = np.asarray(item["lower"], dtype=float)
            upper = np.asarray(item["upper"], dtype=float)
            if lower.shape != y.shape or upper.shape != y.shape:
                raise ValueError("Band endpoints must have the same shape as y")
            if np.isinf(lower).any() or np.isinf(upper).any() or np.any(lower > upper):
                raise ValueError("Band endpoints must be ordered and finite or NaN")
            ax.fill_between(x, lower, upper, color=color, alpha=0.16, linewidth=0)
    if reference is not None:
        ax.axhline(reference, color=COLORS["gray"], ls="--", lw=0.9)
    ax.legend(loc="best")


def plot_ranked(ax, labels, values, lower=None, upper=None, reference=0, unit=""):
    """Plot ranked point estimates with optional interval endpoints."""
    values = _finite_vector(values, "values")
    if len(labels) != len(values):
        raise ValueError("labels and values must have equal length")
    order = np.argsort(-values, kind="stable")
    centers = values[order]
    colors = [COLORS["blue"] if value >= reference else COLORS["gold"] for value in centers]
    positions = np.arange(len(values))
    format_axis(ax, "x")
    ax.axvline(reference, color=COLORS["gray"], ls="--", lw=0.8)
    if lower is not None or upper is not None:
        low = _finite_vector(lower, "lower")
        high = _finite_vector(upper, "upper")
        if low.shape != values.shape or high.shape != values.shape:
            raise ValueError("Interval endpoint lengths must match values")
        if np.any(low > values) or np.any(high < values):
            raise ValueError("Intervals must contain each point estimate")
        ax.errorbar(centers, positions, xerr=[centers - low[order], high[order] - centers],
                    fmt="none", ecolor=COLORS["gray"], elinewidth=1.3, capsize=3, zorder=2)
    ax.scatter(centers, positions, c=colors, s=48, edgecolor="white", lw=0.6, zorder=3)
    for y, value in zip(positions, centers):
        ax.annotate(f"{value:.2f}{unit}", (value, y), xytext=(0, -13),
                    textcoords="offset points", ha="center", fontsize=9, color=COLORS["text"])
    ax.set_yticks(positions, np.asarray(labels)[order])
    ax.set_ylim(len(values) - 0.4, -0.7)
    ax.margins(x=0.18)
    return {"labels": np.asarray(labels)[order].tolist(), "values": centers.tolist()}


def plot_violin(ax, groups, labels, reference=0, sort=True):
    """Plot raw distributions with boxplots, mean diamonds and a reference line."""
    if not groups or len(groups) != len(labels):
        raise ValueError("groups and labels must have equal nonzero length")
    clean = []
    for group in groups:
        values = np.asarray(group, dtype=float)
        if values.ndim != 1 or np.isinf(values).any():
            raise ValueError("Each group must be one-dimensional, without infinite values")
        values = values[np.isfinite(values)]
        if not len(values):
            raise ValueError("Every group must have at least one observed value")
        clean.append(values)
    means = np.array([group.mean() for group in clean])
    order = np.argsort(-means, kind="stable") if sort else np.arange(len(clean))
    clean = [clean[i] for i in order]
    ordered_labels = np.asarray(labels)[order]
    means = means[order]
    format_axis(ax)
    for position, values, mean in zip(range(1, len(clean) + 1), clean, means):
        color = COLORS["blue"] if mean >= reference else COLORS["gold"]
        if len(values) > 1 and np.ptp(values) > 0:
            violin = ax.violinplot([values], positions=[position], widths=0.72,
                                   showextrema=False, points=120)
            violin["bodies"][0].set(facecolor=color, edgecolor=color, alpha=0.32, linewidth=0.8)
        ax.boxplot([values], positions=[position], widths=0.22, patch_artist=True,
                   manage_ticks=False, boxprops={"facecolor": "white", "edgecolor": COLORS["muted"], "lw": 0.8},
                   medianprops={"color": COLORS["navy"], "lw": 1.6},
                   whiskerprops={"color": COLORS["muted"], "lw": 0.8},
                   capprops={"color": COLORS["muted"], "lw": 0.8},
                   flierprops={"marker": "o", "markersize": 2.6,
                               "markerfacecolor": COLORS["muted"], "markeredgewidth": 0, "alpha": 0.7})
        ax.scatter(position, mean, color=COLORS["navy"], marker="D", s=26, zorder=5)
    ax.axhline(reference, color=COLORS["muted"], lw=0.9, ls=(0, (5, 4)))
    ax.set_xticks(np.arange(1, len(clean) + 1), ordered_labels)
    ax.set_xlim(0.4, len(clean) + 0.6)
    return {"labels": ordered_labels.tolist(), "means": means.tolist(),
            "counts": [len(group) for group in clean]}


def density_curve(values, grid):
    """Estimate a Gaussian KDE with a Silverman bandwidth, using NumPy only."""
    values = _finite_vector(values, "density values")
    if len(values) < 2 or np.std(values, ddof=1) == 0:
        raise ValueError("Density estimation requires at least two varying observations")
    bandwidth = 1.06 * np.std(values, ddof=1) * len(values) ** (-0.2)
    result = np.zeros(len(grid))
    for start in range(0, len(values), 1000):
        differences = (grid[:, None] - values[None, start:start + 1000]) / bandwidth
        result += np.exp(-0.5 * differences ** 2).sum(axis=1)
    return result / (len(values) * bandwidth * np.sqrt(2 * np.pi))


def plot_tail_distribution(ax, null_values, observed, side="right", bins=30, color="blue"):
    """Plot an empirical null and compute a one-sided Monte Carlo p value."""
    values = _finite_vector(null_values, "null_values")
    if not np.isfinite(observed) or side not in {"right", "left"}:
        raise ValueError("observed must be finite and side must be right or left")
    format_axis(ax)
    counts, edges = np.histogram(values, bins=bins)
    tail = values >= observed if side == "right" else values <= observed
    tail_counts, _ = np.histogram(values[tail], bins=edges)
    ax.bar(edges[:-1], counts, width=np.diff(edges), align="edge", color=COLORS[color + "_light"],
           edgecolor=COLORS[color], linewidth=0.5, zorder=2)
    ax.bar(edges[:-1], tail_counts, width=np.diff(edges), align="edge", color=COLORS["gold_light"],
           edgecolor=COLORS["gold"], linewidth=0.5, zorder=3)
    if len(values) > 1 and np.ptp(values) > 0:
        grid = np.linspace(edges[0], edges[-1], 400)
        ax.plot(grid, density_curve(values, grid) * len(values) * np.diff(edges)[0],
                color=COLORS[color], lw=1.8, zorder=4)
    ax.axvline(observed, color=COLORS["navy"], lw=2, zorder=5)
    p_value = (int(tail.sum()) + 1) / (len(values) + 1)
    text_x, alignment = (0.03, "left") if side == "right" else (0.97, "right")
    ax.text(text_x, 0.96, f"Observed = {observed:.3f}\np = {p_value:.4f}\nB = {len(values):,}",
            transform=ax.transAxes, ha=alignment, va="top", color=COLORS["navy"], fontsize=10, zorder=6,
            bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none", "pad": 4})
    ax.set_ylabel("频数")
    ax.margins(x=0.04, y=0.12)
    return {"observed": float(observed), "p_value": p_value, "tail_count": int(tail.sum()),
            "permutations": len(values), "side": side, "correction": "plus-one"}


def ternary_coordinates(probabilities, normalize=False):
    """Return normalized components and Cartesian coordinates in vertex order."""
    probabilities = np.asarray(probabilities, dtype=float)
    if (probabilities.ndim != 2 or probabilities.shape[1] != 3 or not len(probabilities)
            or not np.isfinite(probabilities).all() or np.any(probabilities < 0)):
        raise ValueError("probabilities must be a nonempty finite, nonnegative n-by-3 array")
    totals = probabilities.sum(axis=1)
    if np.any(totals <= 0):
        raise ValueError("Probability rows must have positive totals")
    if normalize:
        probabilities = probabilities / totals[:, None]
    elif not np.allclose(totals, 1, rtol=0, atol=1e-8):
        raise ValueError("Rows must sum to 1; set normalize=True to explicitly renormalize")
    top, left, right = probabilities.T
    coordinates = np.column_stack([0.5 * top + right, np.sqrt(3) / 2 * top])
    return probabilities, coordinates


def plot_ternary(ax, probabilities, labels=None, normalize=False):
    """Plot a simplex with the exact q_top=0.5 boundary and semantic fills."""
    labels = labels or ["顶部情景", "左侧情景", "右侧情景"]
    if len(labels) != 3:
        raise ValueError("A ternary plot needs three vertex labels")
    probabilities, coordinates = ternary_coordinates(probabilities, normalize)
    height = np.sqrt(3) / 2
    ax.add_patch(Polygon([[0, 0], [1, 0], [0.75, height / 2], [0.25, height / 2]],
                         facecolor=COLORS["blue_light"], alpha=0.40, edgecolor="none"))
    ax.add_patch(Polygon([[0.25, height / 2], [0.75, height / 2], [0.5, height]],
                         facecolor=COLORS["gold_light"], alpha=0.55, edgecolor="none"))
    for tick in (0.2, 0.4, 0.6, 0.8):
        segments = [([tick / 2, 1 - tick / 2], [height * tick] * 2),
                    ([(1 - tick) / 2, 1 - tick], [height * (1 - tick), 0]),
                    ([tick, 0.5 + tick / 2], [0, height * (1 - tick)])]
        for x, y in segments:
            ax.plot(x, y, color=COLORS["grid"], lw=0.65, ls=(0, (4, 4)), zorder=1)
        ax.text(tick / 2 - 0.025, height * tick, f"{tick:.1f}", ha="right", va="center", fontsize=9)
        ax.text(1 - tick, -0.035, f"{tick:.1f}", ha="center", va="top", fontsize=9)
        ax.text(0.5 + tick / 2 + 0.025, height * (1 - tick), f"{tick:.1f}", va="center", fontsize=9)
    colors = np.where(probabilities[:, 0] >= 0.5, COLORS["gold"], COLORS["blue"])
    ax.scatter(coordinates[:, 0], coordinates[:, 1], c=colors, s=14, alpha=0.22, edgecolors="none", zorder=2)
    ax.plot([0, 0.5, 1, 0], [0, height, 0, 0], color=COLORS["text"], lw=0.9)
    ax.plot([0.25, 0.75], [height / 2] * 2, color=COLORS["muted"], lw=1.2, ls=(0, (5, 4)))
    ax.text(0.5, height + 0.055, labels[0], ha="center", fontsize=12)
    ax.text(-0.025, -0.02, labels[1], ha="right", va="top", fontsize=12)
    ax.text(1.025, -0.02, labels[2], ha="left", va="top", fontsize=12)
    ax.set(xlim=(-0.14, 1.16), ylim=(-0.11, height + 0.12), aspect="equal")
    ax.axis("off")
    return {"means": probabilities.mean(axis=0).tolist(), "normalization_applied": bool(normalize),
            "boundary_top_probability": 0.5, "sample_count": len(probabilities)}


def plot_heatmap(ax, matrix, row_labels, column_labels, center=0, vmin=-1, vmax=1):
    """Plot a centered matrix, showing missing cells explicitly in gray."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (len(row_labels), len(column_labels)) or np.isinf(matrix).any():
        raise ValueError("Matrix shape must match labels and contain no infinite values")
    if not vmin < center < vmax:
        raise ValueError("Heatmap limits must satisfy vmin < center < vmax")
    if np.any(matrix[np.isfinite(matrix)] < vmin) or np.any(matrix[np.isfinite(matrix)] > vmax):
        raise ValueError("Heatmap data exceed the requested color limits")
    cmap = LinearSegmentedColormap.from_list("investment", [COLORS["gold"], "#F7F8F8", COLORS["blue"]])
    cmap.set_bad("#C8CCCF")
    image = ax.imshow(matrix, cmap=cmap, norm=TwoSlopeNorm(vmin=vmin, vcenter=center, vmax=vmax), aspect="auto")
    ax.set_xticks(range(len(column_labels)), column_labels, rotation=30, ha="right")
    ax.set_yticks(range(len(row_labels)), row_labels)
    if matrix.size <= 100:
        for (row, col), value in np.ndenumerate(matrix):
            label = "NA" if np.isnan(value) else f"{value:.2f}"
            ax.text(col, row, label, ha="center", va="center", fontsize=9, color=COLORS["text"])
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    return image
