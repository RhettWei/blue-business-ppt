"""Inspect visible text for clipping, small fonts and text-to-text collisions."""

import numpy as np


def visible_texts(fig):
    texts = list(fig.texts)
    axes = list(fig.axes)
    for axis in list(axes):
        axes.extend(axis.child_axes)
    for ax in axes:
        if not ax.get_visible():
            continue
        texts.extend([ax.title, ax._left_title, ax._right_title, ax.xaxis.label, ax.yaxis.label])
        texts.extend(ax.texts)
        for dimension in (ax.xaxis, ax.yaxis):
            lower, upper = sorted(dimension.get_view_interval())
            for tick in dimension.get_major_ticks():
                if lower-1e-8 <= tick.get_loc() <= upper+1e-8:
                    texts.extend([tick.label1, tick.label2])
        legend = ax.get_legend()
        if legend:
            texts.extend(legend.get_texts())
        for table in ax.tables:
            texts.extend(cell.get_text() for cell in table.get_celld().values())
    for legend in fig.legends:
        texts.extend(legend.get_texts())
    unique = {}
    for text in texts:
        if text.get_visible() and text.get_text().strip():
            unique[id(text)] = text
    return list(unique.values())


def inspect_layout(fig):
    """Return observations in physical figure coordinates after an actual draw."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = visible_texts(fig)
    entries = [(text, text.get_window_extent(renderer)) for text in texts]
    frame = fig.bbox
    clipping = []
    small = []
    collisions = []
    for text, box in entries:
        if not np.isfinite(box.extents).all():
            continue
        if box.x0 < frame.x0-1 or box.y0 < frame.y0-1 or box.x1 > frame.x1+1 or box.y1 > frame.y1+1:
            clipping.append(text.get_text())
        if text.get_fontsize() < 8:
            small.append(text.get_text())
    for index, (first, first_box) in enumerate(entries):
        for second, second_box in entries[index+1:]:
            width = min(first_box.x1, second_box.x1)-max(first_box.x0, second_box.x0)
            height = min(first_box.y1, second_box.y1)-max(first_box.y0, second_box.y0)
            minimum_area = min(first_box.width*first_box.height, second_box.width*second_box.height)
            if width > 1 and height > 1 and minimum_area > 0 and width*height/minimum_area > 0.10:
                collisions.append([first.get_text(), second.get_text()])
    return {"text_count": len(entries), "clipped_text": clipping, "small_text": small,
            "text_collision_candidates": collisions,
            "fonts": sorted({name for text in texts for name in text.get_fontfamily()})}
