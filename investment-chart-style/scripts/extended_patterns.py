"""Additional reference-derived chart templates using the shared design system."""

from statistics import NormalDist
import textwrap

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon
import numpy as np

from chart_style import (
    COLORS, SERIES_COLORS, _finite_vector, density_curve, export_figure,
    format_axis, plot_ternary, style_context, ternary_coordinates,
)


def vector(data, key):
    return _finite_vector(data[key], key)


def labeled_values(data):
    values = vector(data, "values")
    labels = list(data["labels"])
    if len(values) != len(labels):
        raise ValueError("labels and values must have equal length")
    return labels, values


def series_matrix(data):
    labels = list(data["labels"])
    series = data["series"]
    if not labels or not series:
        raise ValueError("At least one category and one series are required")
    matrix = np.array([_finite_vector(item["values"], "series values") for item in series])
    if matrix.ndim != 2 or matrix.shape[1] != len(labels):
        raise ValueError("Every series must match the category labels")
    return labels, series, matrix


def legend_above(ax, count):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.025), ncol=min(count, 5), borderaxespad=0)


def value_labels(ax, bars, unit="", horizontal=False):
    for bar in bars:
        value = bar.get_width() if horizontal else bar.get_height()
        position = (value, bar.get_y() + bar.get_height()/2) if horizontal else (bar.get_x()+bar.get_width()/2, value)
        offset = (5 if value >= 0 else -5, 0) if horizontal else (0, 5 if value >= 0 else -5)
        ax.annotate(f"{value:g}{unit}", position, xytext=offset, textcoords="offset points",
                    ha=("left" if value >= 0 else "right") if horizontal else "center",
                    va="center" if horizontal else ("bottom" if value >= 0 else "top"), fontsize=9)


def draw_bar(fig, ax, data, spec):
    labels, values = labeled_values(data)
    horizontal = data.get("orientation", "vertical") == "horizontal"
    colors = [COLORS["blue"]] * len(values)
    for index in data.get("highlight_indices", []):
        colors[index] = COLORS["gold"]
    format_axis(ax, "x" if horizontal else "y")
    positions = np.arange(len(values))
    if horizontal:
        bars = ax.barh(positions, values, color=colors, height=0.62)
        ax.set_yticks(positions, labels)
        ax.invert_yaxis()
        ax.axvline(0, color=COLORS["gray"], lw=0.7)
    else:
        bars = ax.bar(positions, values, color=colors, width=0.62)
        ax.set_xticks(positions, labels)
        ax.axhline(0, color=COLORS["gray"], lw=0.7)
    value_labels(ax, bars, spec.get("unit", ""), horizontal)
    ax.margins(x=0.12, y=0.18)
    return {"total": float(values.sum()), "count": len(values)}


def draw_grouped_bar(fig, ax, data, spec):
    labels, series, matrix = series_matrix(data)
    format_axis(ax)
    width = 0.78 / len(series)
    for index, item in enumerate(series):
        x = np.arange(len(labels)) + (index-(len(series)-1)/2)*width
        bars = ax.bar(x, matrix[index], width=width*0.93, label=item["name"], color=SERIES_COLORS[index % 5])
        if data.get("show_values", matrix.size <= 20):
            value_labels(ax, bars, spec.get("unit", ""))
    ax.set_xticks(range(len(labels)), labels)
    ax.axhline(0, color=COLORS["gray"], lw=0.7)
    ax.margins(y=0.20)
    legend_above(ax, len(series))
    return {"series_count": len(series), "category_count": len(labels)}


def draw_stacked_bar(fig, ax, data, spec):
    labels, series, matrix = series_matrix(data)
    if data.get("normalize", False):
        if np.any(matrix < 0) or np.any(matrix.sum(axis=0) <= 0):
            raise ValueError("Normalized stacks require nonnegative values and positive category totals")
        matrix = matrix / matrix.sum(axis=0) * 100
    format_axis(ax)
    positive = np.zeros(len(labels))
    negative = np.zeros(len(labels))
    for index, item in enumerate(series):
        values = matrix[index]
        bottom = np.where(values >= 0, positive, negative)
        ax.bar(range(len(labels)), values, bottom=bottom, width=0.64,
               label=item["name"], color=SERIES_COLORS[index % 5], edgecolor="white", lw=0.7)
        positive += np.maximum(values, 0)
        negative += np.minimum(values, 0)
    ax.set_xticks(range(len(labels)), labels)
    ax.axhline(0, color=COLORS["gray"], lw=0.7)
    ax.margins(y=0.12)
    legend_above(ax, len(series))
    return {"positive_totals": positive.tolist(), "negative_totals": negative.tolist(),
            "normalized_percent": bool(data.get("normalize", False))}


def draw_grouped_stacked_bar(fig, ax, data, spec):
    labels = data["labels"]
    groups = data["groups"]
    if not labels or not groups:
        raise ValueError("Grouped stacks need labels and groups")
    names = [item["name"] for item in groups[0]["series"]]
    width = 0.75 / len(groups)
    format_axis(ax)
    totals = []
    tick_positions, tick_labels = [], []
    hatches = ["", "//", "\\\\", "xx", "..", "++", "oo", "**"]
    for group_index, group in enumerate(groups):
        if [item["name"] for item in group["series"]] != names:
            raise ValueError("Groups must have the same stack names and ordering")
        _, _, matrix = series_matrix({"labels": labels, "series": group["series"]})
        if np.any(matrix < 0):
            raise ValueError("This grouped-stack template expects nonnegative contributions")
        bottom = np.zeros(len(labels))
        x = np.arange(len(labels)) + (group_index-(len(groups)-1)/2)*width
        tick_positions.extend(x.tolist())
        tick_labels.extend([group["name"]]*len(labels))
        for series_index, values in enumerate(matrix):
            ax.bar(x, values, bottom=bottom, width=width*0.9,
                   color=SERIES_COLORS[series_index % 5], edgecolor="white", lw=0.6,
                   label=names[series_index] if group_index == 0 else None,
                   hatch=hatches[group_index % len(hatches)] or None)
            bottom += values
        totals.append(bottom.tolist())
    ax.set_xticks(tick_positions, tick_labels, fontsize=8)
    for position, label in enumerate(labels):
        ax.text(position, -0.13, label, transform=ax.get_xaxis_transform(), ha="center", fontsize=10)
    ax.xaxis.labelpad = 30
    legend_above(ax, len(names))
    ax.margins(y=0.13)
    return {"group_totals": totals}


def draw_diverging_bar(fig, ax, data, spec):
    labels, values = labeled_values(data)
    order = np.argsort(values, kind="stable")
    values = values[order]
    labels = np.array(labels)[order]
    format_axis(ax, "x")
    bars = ax.barh(range(len(values)), values, height=0.62,
                   color=[COLORS["blue"] if value >= 0 else COLORS["gold"] for value in values])
    ax.set_yticks(range(len(labels)), labels)
    ax.axvline(0, color=COLORS["muted"], lw=0.9)
    bound = max(np.max(np.abs(values)), 1e-9) * 1.28
    ax.set_xlim(-bound, bound)
    value_labels(ax, bars, spec.get("unit", ""), horizontal=True)
    return {"positive_count": int(np.sum(values > 0)), "negative_count": int(np.sum(values < 0))}


def draw_lollipop(fig, ax, data, spec):
    labels, values = labeled_values(data)
    order = np.argsort(-values, kind="stable")
    values = values[order]
    format_axis(ax, "x")
    ax.hlines(range(len(values)), 0, values, color=COLORS["blue_light"], lw=3)
    ax.scatter(values, range(len(values)), color=COLORS["blue"], s=50, zorder=3)
    ax.set_yticks(range(len(values)), np.array(labels)[order])
    ax.invert_yaxis()
    ax.axvline(0, color=COLORS["gray"], lw=0.7)
    for index, value in enumerate(values):
        ax.annotate(f"{value:g}{spec.get('unit', '')}", (value, index), xytext=(7, 0),
                    textcoords="offset points", va="center", fontsize=9)
    ax.margins(x=0.25)
    return {"values": values.tolist()}


def paired_xy(data):
    x = np.asarray(data["x"], dtype=float)
    y = np.asarray(data["y"], dtype=float)
    if x.ndim != 1 or y.shape != x.shape or np.isinf(x).any() or np.isinf(y).any():
        raise ValueError("x and y must have equal one-dimensional shapes and contain no infinities")
    mask = np.isfinite(x) & np.isfinite(y)
    if not mask.any():
        raise ValueError("No complete x/y pairs")
    return x[mask], y[mask], mask


def draw_scatter_regression(fig, ax, data, spec):
    x, y, mask = paired_xy(data)
    if len(x) < 3 or np.ptp(x) == 0:
        raise ValueError("Regression requires at least three paired points and varying x")
    format_axis(ax)
    ax.scatter(x, y, color=COLORS["blue"], s=35, alpha=0.65, edgecolor="white", lw=0.5)
    slope, intercept = np.polyfit(x, y, 1)
    residuals = y - (intercept + slope*x)
    sigma = np.sqrt(np.dot(residuals, residuals)/(len(x)-2))
    grid = np.linspace(x.min(), x.max(), 150)
    fitted = intercept + slope*grid
    se = sigma*np.sqrt(1/len(x) + (grid-x.mean())**2/np.sum((x-x.mean())**2))
    quantile = NormalDist().inv_cdf(0.975)
    ax.fill_between(grid, fitted-quantile*se, fitted+quantile*se, color=COLORS["blue"], alpha=0.13)
    ax.plot(grid, fitted, color=COLORS["navy"], lw=1.5)
    correlation = None if np.ptp(y) == 0 else float(np.corrcoef(x, y)[0, 1])
    r_label = "未定义" if correlation is None else f"{correlation:.2f}"
    ax.text(0.03, 0.97, f"n = {len(x)}    r = {r_label}", transform=ax.transAxes, va="top", fontsize=10)
    if "labels" in data:
        labels = np.array(data["labels"])
        if len(labels) != len(mask):
            raise ValueError("Scatter labels must match the original rows")
        for px, py, name in zip(x, y, labels[mask]):
            ax.annotate(name, (px, py), xytext=(5, 5), textcoords="offset points", fontsize=8.5)
    return {"slope": float(slope), "intercept": float(intercept), "pearson_r": correlation,
            "n": len(x), "excluded_pairs": int((~mask).sum()), "band": "95% normal-approximation CI for mean response"}


def draw_bubble_scatter(fig, ax, data, spec):
    x, y, mask = paired_xy(data)
    sizes = vector(data, "sizes")
    if len(sizes) != len(mask) or np.any(sizes < 0) or not np.any(sizes[mask] > 0):
        raise ValueError("Bubble sizes must match x/y, be nonnegative and include a positive size")
    sizes = sizes[mask]
    groups = np.array(data.get("groups", ["样本"]*len(mask)))
    if len(groups) != len(mask):
        raise ValueError("groups must match x/y")
    groups = groups[mask]
    format_axis(ax)
    unique_groups = list(dict.fromkeys(groups.tolist()))
    for index, name in enumerate(unique_groups):
        selected = groups == name
        ax.scatter(x[selected], y[selected], s=sizes[selected]/sizes.max()*650,
                   color=SERIES_COLORS[index % 5], alpha=0.48, edgecolor="white", lw=0.8, label=name)
    legend_above(ax, len(unique_groups))
    ax.margins(0.15)
    return {"size_encoding": "marker area proportional to sizes", "n": len(x)}


def raw_groups(data):
    labels = data["labels"]
    groups = []
    for group in data["groups"]:
        values = np.asarray(group, dtype=float)
        if values.ndim != 1 or np.isinf(values).any():
            raise ValueError("Distribution groups must be one-dimensional without infinities")
        values = values[np.isfinite(values)]
        if not len(values):
            raise ValueError("Every group must contain an observed value")
        groups.append(values)
    if len(labels) != len(groups) or not groups:
        raise ValueError("labels must match nonempty groups")
    return labels, groups


def draw_box(fig, ax, data, spec):
    labels, groups = raw_groups(data)
    format_axis(ax)
    plot = ax.boxplot(groups, tick_labels=labels, patch_artist=True, widths=0.5,
                      medianprops={"color": COLORS["navy"], "lw": 1.7},
                      whiskerprops={"color": COLORS["muted"], "lw": 0.8},
                      capprops={"color": COLORS["muted"], "lw": 0.8},
                      flierprops={"marker": ".", "markersize": 3, "alpha": 0.5})
    for index, box in enumerate(plot["boxes"]):
        box.set(facecolor=SERIES_COLORS[index % 5], alpha=0.4, edgecolor=COLORS["muted"], lw=0.8)
    ax.scatter(range(1, len(groups)+1), [group.mean() for group in groups], color=COLORS["navy"], marker="D", s=28, zorder=4)
    return {"medians": [float(np.median(group)) for group in groups], "counts": [len(group) for group in groups]}


def draw_raincloud(fig, ax, data, spec):
    labels, groups = raw_groups(data)
    rng = np.random.default_rng(data.get("jitter_seed", 20261117))
    format_axis(ax)
    for index, values in enumerate(groups):
        position = index+1
        color = SERIES_COLORS[index % 5]
        if len(values) > 1 and np.ptp(values) > 0:
            padding = np.std(values)*0.4
            grid = np.linspace(values.min()-padding, values.max()+padding, 180)
            density = density_curve(values, grid)
            ax.fill_betweenx(grid, position-density/density.max()*0.36, position,
                             facecolor=color, alpha=0.28, edgecolor=color, lw=0.8)
        ax.scatter(position+0.08+rng.uniform(0, 0.12, len(values)), values,
                   s=7, alpha=0.24, color=color, edgecolor="none")
        ax.boxplot([values], positions=[position+0.32], widths=0.15, patch_artist=True, manage_ticks=False,
                   boxprops={"facecolor": "white", "edgecolor": COLORS["muted"], "lw": 0.8},
                   medianprops={"color": COLORS["navy"], "lw": 1.5},
                   whiskerprops={"color": COLORS["muted"], "lw": 0.8}, showfliers=False)
    ax.set_xticks(np.arange(1, len(groups)+1)+0.10, labels)
    ax.set_xlim(0.4, len(groups)+0.7)
    return {"counts": [len(group) for group in groups], "jitter_seed": data.get("jitter_seed", 20261117)}


def draw_histogram_kde(fig, ax, data, spec):
    values = vector(data, "values")
    format_axis(ax)
    counts, edges, _ = ax.hist(values, bins=data.get("bins", 25), color=COLORS["blue_light"],
                              edgecolor=COLORS["blue"], lw=0.6)
    if len(values) > 1 and np.ptp(values) > 0:
        grid = np.linspace(edges[0], edges[-1], 300)
        ax.plot(grid, density_curve(values, grid)*len(values)*np.diff(edges)[0], color=COLORS["blue"])
    ax.axvline(values.mean(), color=COLORS["gold"], ls="--", lw=1.3)
    ax.text(0.97, 0.96, f"n = {len(values):,}\n均值 = {values.mean():.3f}",
            transform=ax.transAxes, ha="right", va="top", fontsize=10)
    ax.set_ylabel("频数")
    ax.margins(y=0.15)
    return {"mean": float(values.mean()), "histogram_total": int(counts.sum())}


def draw_ecdf_threshold(fig, ax, data, spec):
    values = np.sort(vector(data, "values"))
    probabilities = np.arange(1, len(values)+1)/len(values)
    threshold = float(data.get("threshold", 0))
    if not np.isfinite(threshold):
        raise ValueError("threshold must be finite")
    format_axis(ax)
    ax.step(values, probabilities, where="post", color=COLORS["blue"], lw=1.5)
    ax.fill_between(values, probabilities, where=values <= threshold, step="post", color=COLORS["gold_light"])
    ax.fill_between(values, probabilities, where=values > threshold, step="post", color=COLORS["blue_light"])
    ax.axvline(threshold, color=COLORS["muted"], ls="--", lw=0.9)
    ax.set_ylim(0, 1.04)
    ax.set_ylabel("经验累积概率")
    fraction = float(np.mean(values <= threshold))
    ax.text(0.03, 0.96, f"P(X ≤ {threshold:g}) = {fraction:.1%}", transform=ax.transAxes, va="top", fontsize=10)
    return {"threshold": threshold, "fraction_at_or_below": fraction, "n": len(values)}


def draw_confusion_matrix(fig, ax, data, spec):
    matrix = np.asarray(data["matrix"], dtype=float)
    labels = data["labels"]
    if matrix.shape != (len(labels), len(labels)) or not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError("Confusion matrix must be square, finite and nonnegative")
    mode = data.get("normalize", "row")
    displayed = matrix.copy()
    if mode == "row":
        totals = matrix.sum(axis=1, keepdims=True)
        displayed = np.divide(matrix, totals, out=np.full_like(matrix, np.nan), where=totals != 0)
    elif mode != "none":
        raise ValueError("normalize must be row or none")
    cmap = LinearSegmentedColormap.from_list("confusion", ["#F4F8F7", COLORS["blue"]])
    cmap.set_bad(COLORS["gray"])
    image = ax.imshow(displayed, cmap=cmap, vmin=0, vmax=1 if mode == "row" else max(1, float(matrix.max())))
    for (row, col), value in np.ndenumerate(displayed):
        text = "NA" if np.isnan(value) else (f"{value:.1%}" if mode == "row" else f"{value:g}")
        ax.text(col, row, text, ha="center", va="center", fontsize=10, color=COLORS["text"])
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("预测类别")
    ax.set_ylabel("真实类别")
    ax.tick_params(length=0)
    ax.spines[:].set_visible(False)
    fig.colorbar(image, ax=ax, fraction=0.045, pad=0.04)
    return {"normalization": mode, "raw_total": float(matrix.sum()),
            "zero_rows": np.flatnonzero(matrix.sum(axis=1) == 0).tolist()}


def draw_annotated_table(fig, ax, data, spec):
    rows = data["rows"]
    columns = data["columns"]
    if not rows or any(len(row) != len(columns) for row in rows):
        raise ValueError("Every table row must match columns")
    ax.axis("off")
    text = [[f"{value:.2f}" if isinstance(value, float) else str(value) for value in row] for row in rows]
    table = ax.table(cellText=text, colLabels=columns, rowLabels=data.get("row_labels"),
                     cellLoc="center", loc="center", bbox=[0, 0.02, 1, 0.95])
    table.auto_set_font_size(False)
    table.set_fontsize(float(data.get("font_size", 10)))
    summary = set(data.get("summary_columns", []))
    for (row, column), cell in table.get_celld().items():
        cell.set(edgecolor="white", linewidth=1.3)
        if row == 0:
            cell.set_facecolor(COLORS["green_light"])
        elif column == -1:
            cell.set_facecolor(COLORS["blue_light"])
        elif columns[column] in summary:
            cell.set_facecolor(COLORS["gold_light"])
        else:
            cell.set_facecolor("#F4F7F8" if row % 2 else "white")
    return {"rows": len(rows), "columns": len(columns)}


def draw_matrix_marginals(fig, ax, data, spec):
    matrix = np.asarray(data["matrix"], dtype=float)
    rows, columns = data["row_labels"], data["column_labels"]
    if matrix.shape != (len(rows), len(columns)) or not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError("Count matrix must match labels and contain finite nonnegative values")
    ax.set_position([0.20, 0.28, 0.48, 0.45])
    top = fig.add_axes([0.20, 0.76, 0.48, 0.10], sharex=ax)
    right = fig.add_axes([0.71, 0.28, 0.15, 0.45], sharey=ax)
    cmap = LinearSegmentedColormap.from_list("counts", ["#F3F8F5", COLORS["green"]])
    ax.imshow(matrix, cmap=cmap, aspect="auto", origin="upper")
    ax.set_xticks(range(len(columns)), columns)
    ax.set_yticks(range(len(rows)), rows)
    ax.tick_params(length=0)
    if matrix.size <= 120:
        for (row, col), value in np.ndenumerate(matrix):
            ax.text(col, row, f"{value:g}", ha="center", va="center", fontsize=9)
    top.bar(range(len(columns)), matrix.sum(axis=0), color=COLORS["blue"], width=0.6)
    right.barh(range(len(rows)), matrix.sum(axis=1), color=COLORS["gold"], height=0.6)
    format_axis(top, None)
    format_axis(right, None)
    top.tick_params(labelbottom=False)
    right.tick_params(labelleft=False)
    top.set_title("列合计", fontsize=10, loc="left")
    right.set_title("行合计", fontsize=10, loc="left")
    return {"row_totals": matrix.sum(axis=1).tolist(), "column_totals": matrix.sum(axis=0).tolist(), "total": float(matrix.sum())}


def draw_coefficient_paths(fig, ax, data, spec):
    x = vector(data, "x")
    coefficients = np.asarray(data["coefficients"], dtype=float)
    names = data["feature_names"]
    if (not names or coefficients.shape != (len(x), len(names)) or not np.isfinite(coefficients).all()
            or len(x) < 2 or not (np.all(np.diff(x) > 0) or np.all(np.diff(x) < 0))):
        raise ValueError("Coefficients must be finite parameter-by-feature data, with strictly ordered x")
    format_axis(ax)
    selected = data.get("highlight_indices", np.argsort(np.max(np.abs(coefficients), axis=0))[-4:].tolist())
    if any(not isinstance(index, int) or index < 0 or index >= len(names) for index in selected):
        raise ValueError("highlight_indices must contain valid feature indices")
    for index in range(len(names)):
        color = COLORS["gray"]
        if index in selected:
            color = COLORS["blue"] if coefficients[np.argmax(np.abs(coefficients[:, index])), index] >= 0 else COLORS["gold"]
        ax.plot(x, coefficients[:, index], color=color, lw=1.7 if index in selected else 0.7,
                alpha=1 if index in selected else 0.5, label=names[index] if index in selected else None)
    ax.axhline(0, color=COLORS["gray"], ls="--", lw=0.8)
    ax.set_xlim(x[0], x[-1])
    ax.set_xlabel(data.get("parameter_name", r"$\log(\lambda)$"))
    ax.set_ylabel("标准化系数")
    for item in data.get("references", []):
        ax.axvline(item["x"], color=COLORS["navy"], ls="--", lw=1)
    secondary = ax.secondary_xaxis("top")
    indices = np.linspace(0, len(x)-1, min(5, len(x)), dtype=int)
    nonzero = np.count_nonzero(np.abs(coefficients) > data.get("zero_tolerance", 1e-10), axis=1)
    secondary.set_xticks(x[indices], nonzero[indices])
    secondary.set_xlabel("非零系数个数", fontsize=10)
    ax.legend(loc="best", fontsize=9)
    return {"nonzero_counts": nonzero.tolist(), "highlight_indices": list(selected)}


def draw_cv_curve(fig, ax, data, spec):
    x, means, se = vector(data, "x"), vector(data, "means"), vector(data, "se")
    if len(x) != len(means) or se.shape != means.shape or np.any(se < 0) or not (np.all(np.diff(x) > 0) or np.all(np.diff(x) < 0)):
        raise ValueError("CV x must be strictly ordered, with matching means and nonnegative SE")
    objective = data.get("objective", "max")
    if objective not in {"max", "min"}:
        raise ValueError("objective must be max or min")
    best = int(np.argmax(means) if objective == "max" else np.argmin(means))
    format_axis(ax)
    ax.fill_between(x, means-se, means+se, color=COLORS["blue"], alpha=0.14)
    ax.errorbar(x, means, yerr=se, fmt="o-", markersize=4, color=COLORS["blue"],
                ecolor="#A4B8C6", elinewidth=0.8, capsize=2)
    ax.axvline(x[best], color=COLORS["navy"], ls="--", lw=1.4, label="最优均值")
    statistics = {"best_index": best, "best_parameter": float(x[best]), "best_mean": float(means[best])}
    if "regularization_strength" in data:
        strength = vector(data, "regularization_strength")
        if strength.shape != x.shape or np.any(strength < 0):
            raise ValueError("regularization_strength must match x and be nonnegative")
        accepted = means >= means[best]-se[best] if objective == "max" else means <= means[best]+se[best]
        one_se = int(np.argmax(np.where(accepted, strength, -np.inf)))
        ax.axvline(x[one_se], color=COLORS["gold"], ls="--", lw=1.3, label="一标准误差选择")
        statistics.update(one_se_index=one_se, one_se_parameter=float(x[one_se]))
    ax.set_xlim(x[0], x[-1])
    ax.set_xlabel(data.get("parameter_name", r"$\log(\lambda)$"))
    legend_above(ax, 2)
    return statistics


def draw_volcano(fig, ax, data, spec):
    effects = vector(data, "effects")
    probabilities = vector(data, "p_values")
    if effects.shape != probabilities.shape or np.any(probabilities <= 0) or np.any(probabilities > 1):
        raise ValueError("p_values must match effects and lie in (0, 1]")
    cutoff = float(data.get("p_threshold", 0.05))
    effect_cutoff = float(data.get("effect_threshold", 0.2))
    if not 0 < cutoff <= 1 or effect_cutoff < 0:
        raise ValueError("Invalid volcano thresholds")
    y = -np.log10(probabilities)
    selected = (probabilities <= cutoff) & (np.abs(effects) >= effect_cutoff)
    colors = np.where(selected, np.where(effects >= 0, COLORS["blue"], COLORS["gold"]), COLORS["gray"])
    format_axis(ax)
    ax.scatter(effects, y, c=colors, s=25, alpha=0.65, edgecolor="none")
    ax.axhline(-np.log10(cutoff), color=COLORS["muted"], ls="--", lw=0.8)
    for sign in [-1, 1]:
        ax.axvline(sign*effect_cutoff, color=COLORS["gray"], ls="--", lw=0.8)
    ax.set_xlabel("效应值")
    ax.set_ylabel("−log10(p)")
    if "labels" in data:
        labels = data["labels"]
        if len(labels) != len(effects):
            raise ValueError("Volcano labels must match effects")
        candidates = np.flatnonzero(selected)
        top = candidates[np.argsort(probabilities[candidates])[:data.get("label_count", 6)]]
        for index in top:
            ax.annotate(labels[index], (effects[index], y[index]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    return {"selected_count": int(selected.sum()), "p_threshold": cutoff, "effect_threshold": effect_cutoff}


def draw_donut(fig, ax, data, spec):
    labels, values = labeled_values(data)
    if np.any(values < 0) or values.sum() <= 0:
        raise ValueError("Donut values must be nonnegative with a positive total")
    wedges, _, percentage_texts = ax.pie(values, colors=[SERIES_COLORS[i % 5] for i in range(len(values))],
                          startangle=90, counterclock=False, wedgeprops={"width": 0.42, "edgecolor": "white", "lw": 2},
                          autopct=lambda percent: f"{percent:.1f}%" if percent >= 5 else "", pctdistance=0.78,
                          textprops={"fontsize": 10, "color": COLORS["text"]})
    dark = np.asarray(to_rgb(COLORS["text"]))
    dark_linear = np.where(dark <= 0.04045, dark/12.92, ((dark+0.055)/1.055)**2.4)
    dark_luminance = float(dark_linear @ [0.2126, 0.7152, 0.0722])
    for wedge, text in zip(wedges, percentage_texts):
        rgb = np.asarray(wedge.get_facecolor()[:3])
        linear = np.where(rgb <= 0.04045, rgb/12.92, ((rgb+0.055)/1.055)**2.4)
        luminance = float(linear @ [0.2126, 0.7152, 0.0722])
        dark_contrast = (luminance+0.05)/(dark_luminance+0.05)
        white_contrast = 1.05/(luminance+0.05)
        text.set_color("white" if white_contrast > dark_contrast else COLORS["text"])
    center_text = data.get("center_text", f"合计\n{values.sum():g}")
    ax.text(0, 0, center_text, ha="center", va="center", fontsize=12)
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5))
    ax.set_aspect("equal")
    return {"shares": (values/values.sum()).tolist(), "total": float(values.sum())}


def draw_scalp_topography(fig, ax, data, spec):
    positions = np.asarray(data["positions"], dtype=float)
    values = vector(data, "values")
    labels = data["labels"]
    if (positions.shape != (len(values), 2) or len(labels) != len(values)
            or not np.isfinite(positions).all() or np.any(np.sum(positions**2, axis=1) > 1.05**2)):
        raise ValueError("Scalp positions must be finite normalized disk coordinates matching labels/values")
    cmap = LinearSegmentedColormap.from_list("scalp", [COLORS["blue_light"], COLORS["blue"], COLORS["navy"]])
    span = float(np.ptp(values))
    sizes = np.full(len(values), 65.0) if span == 0 else 35 + (values-values.min())/span*125
    dots = ax.scatter(positions[:, 0], positions[:, 1], c=values, s=sizes, cmap=cmap, edgecolor="white", lw=0.7)
    ax.add_patch(Circle((0, 0), 1, fill=False, edgecolor=COLORS["muted"], lw=1))
    ax.plot([-0.13, 0, 0.13], [0.99, 1.16, 0.99], color=COLORS["muted"], lw=1)
    for sign in [-1, 1]:
        ax.add_patch(Polygon([[sign, 0.25], [sign*1.1, 0.15], [sign*1.1, -0.2], [sign, -0.3]],
                             fill=False, edgecolor=COLORS["muted"], lw=0.8))
    for (x, y), label in zip(positions, labels):
        ax.annotate(label, (x, y), xytext=(4, 5), textcoords="offset points", fontsize=8)
    ax.set(aspect="equal", xlim=(-1.3, 1.3), ylim=(-1.17, 1.28))
    ax.axis("off")
    fig.colorbar(dots, ax=ax, fraction=0.04, pad=0.025, label=data.get("value_label", "通道重要性"))
    return {"channels": len(values), "representation": "provided 2D channel positions; node encoding"}


def draw_region_map(fig, ax, data, spec):
    regions = data["regions"]
    if not regions:
        raise ValueError("At least one region polygon is required")
    all_vertices = []
    for index, region in enumerate(regions):
        vertices = np.asarray(region["polygon"], dtype=float)
        if vertices.ndim != 2 or vertices.shape[1] != 2 or len(vertices) < 3 or not np.isfinite(vertices).all():
            raise ValueError("Each region needs at least three finite x/y vertices")
        value = float(region["value"])
        if not np.isfinite(value):
            raise ValueError("Region values must be finite")
        all_vertices.extend(vertices)
        ax.add_patch(Polygon(vertices, facecolor=SERIES_COLORS[index % 5], alpha=0.42, edgecolor="white", lw=2))
        center = region.get("label_position", vertices.mean(axis=0))
        ax.text(*center, f"{region['name']}\n{value:.2f}", ha="center", va="center", fontsize=10)
    all_vertices = np.asarray(all_vertices)
    low, high = all_vertices.min(axis=0), all_vertices.max(axis=0)
    padding = np.maximum((high-low)*0.12, 0.05)
    ax.set(xlim=(low[0]-padding[0], high[0]+padding[0]), ylim=(low[1]-padding[1], high[1]+padding[1]), aspect="equal")
    ax.axis("off")
    return {"regions": len(regions), "geometry_source": data.get("geometry_source", "user-supplied polygons")}


def layout_nodes(nodes, edges):
    ids = [node["id"] for node in nodes]
    if len(set(ids)) != len(ids):
        raise ValueError("Flowchart node IDs must be unique")
    incoming = {identifier: 0 for identifier in ids}
    children = {identifier: [] for identifier in ids}
    for edge in edges:
        if edge["from"] not in incoming or edge["to"] not in incoming:
            raise ValueError("Flowchart edges must reference existing nodes")
        incoming[edge["to"]] += 1
        children[edge["from"]].append(edge["to"])
    if all("position" in node for node in nodes):
        positions = {node["id"]: node["position"] for node in nodes}
        if any(np.asarray(position).shape != (2,) or not np.isfinite(position).all() for position in positions.values()):
            raise ValueError("Node positions must be finite x/y pairs")
        return positions
    queue = [identifier for identifier in ids if incoming[identifier] == 0]
    levels = {identifier: 0 for identifier in queue}
    visited = []
    while queue:
        identifier = queue.pop(0)
        visited.append(identifier)
        for child in children[identifier]:
            levels[child] = max(levels.get(child, 0), levels[identifier]+1)
            incoming[child] -= 1
            if incoming[child] == 0:
                queue.append(child)
    if len(visited) != len(nodes):
        raise ValueError("Cyclic diagrams need an explicit position for every node")
    positions = {}
    maximum = max(levels.values(), default=0)
    for level in range(maximum+1):
        layer = [identifier for identifier in ids if levels[identifier] == level]
        for index, identifier in enumerate(layer):
            positions[identifier] = (0.12 + level/max(maximum, 1)*0.76, 0.5 + ((len(layer)-1)/2-index)*0.38)
    return positions


def draw_flowchart(fig, ax, data, spec):
    nodes, edges = data["nodes"], data.get("edges", [])
    if not nodes:
        raise ValueError("A diagram needs at least one node")
    positions = layout_nodes(nodes, edges)
    patches, node_texts = {}, {}
    horizontal_centers = sorted({float(position[0]) for position in positions.values()})
    spacing = min(np.diff(horizontal_centers)) if len(horizontal_centers) > 1 else 0.4
    default_width = min(0.18, float(spacing)*0.62)
    for index, node in enumerate(nodes):
        x, y = positions[node["id"]]
        width = float(node.get("width", default_width))
        height = float(node.get("height", 0.18))
        if width <= 0 or height <= 0:
            raise ValueError("Node dimensions must be positive")
        color = SERIES_COLORS[index % 5]
        patch = FancyBboxPatch((x-width/2, y-height/2), width, height,
                               boxstyle="round,pad=0.012,rounding_size=0.02",
                               facecolor="white", edgecolor=color, lw=1.2, zorder=3)
        ax.add_patch(patch)
        patches[node["id"]] = patch
        text = "\n".join(textwrap.fill(line, width=int(node.get("wrap", 10))) for line in node["label"].splitlines())
        node_texts[node["id"]] = ax.text(x, y, text, ha="center", va="center", fontsize=node.get("font_size", 10), zorder=4)
    node_boxes = list(patches.values())
    for index, first in enumerate(node_boxes):
        for second in node_boxes[index+1:]:
            overlap_x = min(first.get_x()+first.get_width(), second.get_x()+second.get_width())-max(first.get_x(), second.get_x())
            overlap_y = min(first.get_y()+first.get_height(), second.get_y()+second.get_height())-max(first.get_y(), second.get_y())
            if overlap_x > 0 and overlap_y > 0:
                raise ValueError("Flowchart nodes overlap; adjust positions, width or height")
    for edge in edges:
        start, end = positions[edge["from"]], positions[edge["to"]]
        ax.add_patch(FancyArrowPatch(start, end, patchA=patches[edge["from"]], patchB=patches[edge["to"]],
                                     arrowstyle="-|>", mutation_scale=12, lw=1.0,
                                     color=COLORS["muted"], connectionstyle=edge.get("connectionstyle", "arc3,rad=0"), zorder=2))
        if edge.get("label"):
            midpoint = np.mean([start, end], axis=0)
            ax.text(midpoint[0], midpoint[1]+0.045, edge["label"], ha="center", fontsize=8.5,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 2})
    extents = np.array([[patch.get_x(), patch.get_y(), patch.get_x()+patch.get_width(), patch.get_y()+patch.get_height()]
                        for patch in patches.values()])
    ax.set(xlim=(min(-0.01, extents[:, 0].min()-0.03), max(1.01, extents[:, 2].max()+0.03)),
           ylim=(min(-0.03, extents[:, 1].min()-0.05), max(1.03, extents[:, 3].max()+0.05)))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for identifier, artist in node_texts.items():
        available_width = patches[identifier].get_window_extent(renderer).width-12
        lines = []
        for paragraph in artist.get_text().splitlines():
            line = ""
            paragraph_lines = []
            for character in paragraph:
                candidate = line+character
                width_px = renderer.get_text_width_height_descent(candidate, artist.get_fontproperties(), False)[0]
                if line and width_px > available_width:
                    paragraph_lines.append(line.rstrip())
                    line = character.lstrip()
                else:
                    line = candidate
            paragraph_lines.append(line.rstrip())
            if len(paragraph_lines) > 1 and len(paragraph_lines[-1]) == 1 and len(paragraph_lines[-2]) > 2:
                paragraph_lines[-1] = paragraph_lines[-2][-1]+paragraph_lines[-1]
                paragraph_lines[-2] = paragraph_lines[-2][:-1]
            lines.extend(paragraph_lines)
        artist.set_text("\n".join(lines))
    ax.axis("off")
    return {"nodes": len(nodes), "edges": len(edges), "positions": positions}


def draw_frequency_bands(fig, ax, data, spec):
    bands = data["bands"]
    time = vector(data, "time")
    if not bands or len(time) < 2 or not np.all(np.diff(time) > 0):
        raise ValueError("Frequency bands need a strictly increasing time vector and at least one band")
    ax.remove()
    top, bottom = 0.82, 0.24
    height = (top-bottom)/len(bands)
    modes = []
    for index, band in enumerate(bands):
        position = [0.23, top-(index+1)*height+height*0.12, 0.60, height*0.70]
        panel = fig.add_axes(position)
        if "signal" in band:
            signal = _finite_vector(band["signal"], "signal")
            if signal.shape != time.shape:
                raise ValueError("Band signal must match time")
            modes.append("provided signal")
        else:
            frequency = float(band["frequency"])
            amplitude = float(band.get("amplitude", 1))
            if not np.isfinite([frequency, amplitude]).all() or frequency < 0:
                raise ValueError("Wave frequency/amplitude must be finite, with nonnegative frequency")
            if frequency >= 0.5/np.max(np.diff(time)):
                raise ValueError("The time grid is too sparse for the requested sine frequency")
            signal = amplitude*np.sin(2*np.pi*frequency*time+float(band.get("phase", 0)))
            modes.append("sine schematic")
        color = SERIES_COLORS[index % 4]
        panel.plot(time, signal, color=color, lw=1.2)
        panel.fill_between(time, 0, signal, color=color, alpha=0.10)
        panel.text(-0.04, 0.5, band["name"], transform=panel.transAxes, ha="right", va="center", fontsize=10)
        panel.set_yticks([])
        panel.spines[["left", "right", "top"]].set_visible(False)
        panel.spines["bottom"].set_color(COLORS["grid"])
        if index < len(bands)-1:
            panel.set_xticks([])
        else:
            panel.set_xlabel("时间（秒）")
    return {"bands": len(bands), "representations": modes}


def draw_equation_panel(fig, ax, data, spec):
    formula = data["formula"]
    if not isinstance(formula, str) or not formula:
        raise ValueError("A nonempty MathText formula is required")
    ax.set_position([0.12, 0.27, 0.38, 0.5])
    format_axis(ax)
    x = vector(data, "x")
    for index, curve in enumerate(data["curves"]):
        values = _finite_vector(curve["y"], "curve y")
        if len(values) != len(x):
            raise ValueError("Equation-panel curves must match x")
        ax.plot(x, values, color=SERIES_COLORS[index % 5], label=curve["name"])
        ax.fill_between(x, values, color=SERIES_COLORS[index % 5], alpha=0.10)
    ax.legend(loc="upper right", fontsize=9)
    panel = fig.add_axes([0.57, 0.30, 0.35, 0.44])
    panel.axis("off")
    panel.text(0.5, 0.65, formula, ha="center", va="center", fontsize=data.get("formula_size", 18),
               bbox={"boxstyle": "round,pad=0.7", "fc": COLORS["green_light"], "ec": COLORS["green"], "lw": 0.8})
    panel.text(0.5, 0.22, "\n".join(textwrap.wrap(data.get("description", ""), width=19)),
               ha="center", va="center", fontsize=10, color=COLORS["muted"])
    return {"curve_count": len(data["curves"]), "formula": formula}


def draw_ternary_marginals(fig, ax, data, spec):
    probabilities, _ = ternary_coordinates(data["probabilities"], data.get("normalize", False))
    ax.set_position([0.07, 0.21, 0.54, 0.64])
    labels = data.get("labels", ["顶部情景", "左侧情景", "右侧情景"])
    statistics = plot_ternary(ax, probabilities, labels)
    statistics["normalization_applied"] = bool(data.get("normalize", False))
    for index, label in enumerate(labels):
        panel = fig.add_axes([0.69, 0.68-index*0.21, 0.24, 0.12])
        values = probabilities[:, index]
        if len(values) > 1 and np.ptp(values) > 0:
            grid = np.linspace(0, 1, 250)
            density = density_curve(values, grid)
            color = COLORS["gold"] if index == 0 else COLORS["blue"]
            panel.plot(grid, density, color=color, lw=1.2)
            panel.fill_between(grid, density, color=color, alpha=0.2)
        panel.axvline(values.mean(), color=COLORS["muted"], ls="--", lw=0.8)
        panel.set(xlim=(0, 1), xticks=[0, 0.5, 1], yticks=[])
        panel.set_title(f"{label}  均值 {values.mean():.2f}", fontsize=10, loc="left", pad=6)
        format_axis(panel, None)
        panel.spines["left"].set_visible(False)
    return statistics


DRAWERS = {
    "bar": draw_bar, "grouped_bar": draw_grouped_bar, "stacked_bar": draw_stacked_bar,
    "grouped_stacked_bar": draw_grouped_stacked_bar, "diverging_bar": draw_diverging_bar,
    "lollipop": draw_lollipop, "scatter_regression": draw_scatter_regression,
    "bubble_scatter": draw_bubble_scatter, "box": draw_box, "raincloud": draw_raincloud,
    "histogram_kde": draw_histogram_kde, "ecdf_threshold": draw_ecdf_threshold,
    "confusion_matrix": draw_confusion_matrix, "annotated_table": draw_annotated_table,
    "matrix_marginals": draw_matrix_marginals, "coefficient_paths": draw_coefficient_paths,
    "cv_curve": draw_cv_curve, "volcano": draw_volcano, "donut": draw_donut,
    "scalp_topography": draw_scalp_topography, "region_map": draw_region_map,
    "flowchart": draw_flowchart, "frequency_bands": draw_frequency_bands,
    "equation_panel": draw_equation_panel,
}


def render_extended(specification, output):
    kind = specification["type"]
    data = specification["data"]
    drawer = draw_ternary_marginals if kind == "ternary" else DRAWERS.get(kind)
    if drawer is None:
        raise ValueError(f"Unsupported chart type: {kind}")
    with style_context():
        fig, ax = plt.subplots(figsize=specification.get("figsize", [9, 5.8]))
        fig.subplots_adjust(left=0.14, right=0.91, bottom=0.26, top=0.80)
        try:
            statistics = drawer(fig, ax, data, specification)
            if ax in fig.axes:
                ax.set_xlabel(specification.get("xlabel", ax.get_xlabel()))
                ax.set_ylabel(specification.get("ylabel", ax.get_ylabel()))
            fig.suptitle(specification["title"], x=0.065, y=0.95, ha="left", fontsize=17)
            result = export_figure(fig, output, specification.get("source", "用户提供的 JSON 图表规格"),
                                   specification.get("note", ""), statistics)
        finally:
            plt.close(fig)
    return result
