"""Render four reference-inspired figures with explicitly simulated data."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

from chart_style import (
    COLORS, density_curve, export_figure, format_axis,
    plot_tail_distribution, plot_ternary, plot_violin, style_context,
)


SOURCE = "数据为固定种子模拟，用于验证绘图风格与接口。"
SEED = 20261117


def regularization_figure(output, rng):
    """Show a numerical schematic of paths and the one-standard-error rule."""
    log_lambda = np.linspace(-1, -6, 65)
    lambdas = np.exp(log_lambda)
    amplitudes = np.r_[np.linspace(0.90, 0.18, 16), -np.linspace(0.17, 0.82, 16)]
    thresholds = rng.uniform(0.009, 0.30, len(amplitudes))
    paths = amplitudes[:, None] * np.maximum(1 - lambdas[None, :] / thresholds[:, None], 0)
    score = 0.04 + 0.115 * np.exp(-((log_lambda + 3.75) / 1.6) ** 2)
    se = 0.009 + 0.003 * np.cos(log_lambda) ** 2
    best = int(np.argmax(score))
    acceptable = score >= score[best] - se[best]
    one_se = int(np.argmax(np.where(acceptable, lambdas, -np.inf)))
    if lambdas[one_se] < lambdas[best]:
        raise AssertionError("The one-SE choice must have at least as much regularization")
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.0))
    fig.subplots_adjust(left=0.075, right=0.95, bottom=0.24, top=0.77, wspace=0.40)
    fig.suptitle("因子模型的复杂度与验证表现", x=0.065, y=0.96, ha="left", fontsize=18)
    fig.text(0.065, 0.89, "Elastic Net  ·  参数向右递减，惩罚减弱，非零系数逐步增加",
             fontsize=11, color=COLORS["muted"])
    highlighted = {0: "价值", 4: "盈利", 8: "质量", 23: "波动", 27: "杠杆", 31: "换手"}
    for index, path in enumerate(paths):
        selected = index in highlighted
        color = (COLORS["blue"] if amplitudes[index] > 0 else COLORS["gold"]) if selected else COLORS["gray"]
        axes[0].plot(log_lambda, path, color=color, lw=1.6 if selected else 0.65,
                     alpha=1 if selected else 0.55, zorder=3 if selected else 2)
        if selected:
            axes[0].text(-6.12, path[-1], highlighted[index], color=color, fontsize=10, va="center")
    axes[0].axhline(0, color=COLORS["gray"], ls="--", lw=0.8)
    axes[0].set(ylabel="标准化系数", xlabel=r"$\log(\lambda)$", xlim=(-1, -6.8))
    fig.text(0.075, 0.85, "A. 因子系数路径", fontsize=13)
    top_axis = axes[0].secondary_xaxis("top")
    ticks = [-1, -2, -3, -4, -5, -6]
    top_axis.set_xticks(ticks)
    counts = [int(np.count_nonzero(paths[:, np.argmin(abs(log_lambda - tick))])) for tick in ticks]
    top_axis.set_xticklabels(counts)
    top_axis.set_xlabel("非零系数个数", fontsize=10, labelpad=7)
    top_axis.tick_params(labelsize=9, length=2)
    indices = np.arange(0, len(score), 3)
    axes[1].fill_between(log_lambda, score - se, score + se, color=COLORS["blue"], alpha=0.15)
    axes[1].errorbar(log_lambda[indices], score[indices], yerr=se[indices], fmt="o-",
                     color=COLORS["blue"], ecolor="#A4B8C6", markersize=3.5, capsize=2, lw=1.2)
    axes[1].set(xlim=(-1, -6), ylim=(0, 0.205), xlabel=r"$\log(\lambda)$", ylabel="交叉验证得分")
    fig.text(axes[1].get_position().x0, 0.85, "B. 验证均值与标准误", fontsize=13)
    for ax in axes:
        format_axis(ax)
        ax.axvline(log_lambda[best], color=COLORS["navy"], lw=1.3, ls=(0, (4, 4)))
        ax.axvline(log_lambda[one_se], color=COLORS["gray"], lw=1.3, ls=(0, (4, 4)))
    for index, label, offset in [(best, r"$\lambda_{min}$", (26, 34)),
                                  (one_se, r"$\lambda_{1se}$", (-70, 42))]:
        axes[1].annotate(label + f"\nScore = {score[index]:.3f}",
                         xy=(log_lambda[index], score[index]), xytext=offset,
                         textcoords="offset points", fontsize=10,
                         bbox={"boxstyle": "round,pad=0.4", "fc": "white", "ec": COLORS["gray"], "lw": 0.7},
                         arrowprops={"arrowstyle": "->", "color": COLORS["muted"], "lw": 0.7})
    handles = [Line2D([], [], color=COLORS["blue"], label="关注的正向系数"),
               Line2D([], [], color=COLORS["gold"], label="关注的负向系数"),
               Line2D([], [], color=COLORS["gray"], label="其余系数"),
               Patch(facecolor=COLORS["blue_light"], label="验证均值 ± SE")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.11), ncol=4)
    export_figure(fig, output / "01-regularization", SOURCE,
                  "路径与验证分数为数值示意，参数位置按一标准误差规则计算。",
                  {"lambda_min": float(lambdas[best]), "lambda_1se": float(lambdas[one_se]),
                   "display_direction": "decreasing log(lambda)", "seed": SEED})
    plt.close(fig)


def ternary_figure(output, rng):
    """Show consistent ternary components, exact boundary and marginals."""
    probabilities = rng.dirichlet([4.8, 3.0, 2.7], 1600)
    fig = plt.figure(figsize=(12.8, 7.5))
    grid = fig.add_gridspec(3, 2, width_ratios=[2.1, 1], left=0.065, right=0.94,
                          bottom=0.23, top=0.80, wspace=0.22, hspace=0.70)
    triangle = fig.add_subplot(grid[:, 0])
    statistics = plot_ternary(triangle, probabilities, ["增长情景", "基准情景", "压力情景"])
    triangle.text(0.5, 0.10, "其余情景合计 > 50%", ha="center", color=COLORS["navy"], fontsize=10)
    fig.suptitle("情景概率结构与边际分布", x=0.065, y=0.96, ha="left", fontsize=18)
    fig.text(0.065, 0.89, "每个点代表一组三情景概率  ·  三项之和为 1  ·  虚线表示增长情景概率为 0.5",
             color=COLORS["muted"], fontsize=11)
    for index, name in enumerate(["增长情景", "基准情景", "压力情景"]):
        ax = fig.add_subplot(grid[index, 1])
        values = probabilities[:, index]
        x = np.linspace(0, 1, 300)
        density = density_curve(values, x)
        color = COLORS["gold"] if index == 0 else COLORS["blue"]
        ax.fill_between(x, density, color=color, alpha=0.23)
        ax.plot(x, density, color=color, lw=1.2)
        ax.axvline(values.mean(), color=color, ls=(0, (4, 4)), lw=1.0)
        ax.set(xlim=(0, 1), ylim=(0, density.max() * 1.20), yticks=[], xticks=[0, 0.5, 1])
        ax.set_title(f"{name}    均值 {values.mean():.2f}", loc="left", fontsize=11, pad=8)
        format_axis(ax, grid=None)
        ax.spines["left"].set_visible(False)
    fig.legend(handles=[Patch(facecolor=COLORS["gold_light"], edgecolor=COLORS["gold"], label="增长情景 ≥ 50%"),
                        Patch(facecolor=COLORS["blue_light"], edgecolor=COLORS["blue"], label="其余情景合计 > 50%"),
                        Line2D([], [], color=COLORS["muted"], ls="--", label="等概率边界")],
               loc="lower center", bbox_to_anchor=(0.5, 0.11), ncol=3)
    export_figure(fig, output / "02-ternary", SOURCE,
                  "均值来自同一组归一化概率，横向边界按 q基准 + q压力 = q增长 推导。", statistics)
    plt.close(fig)


def violin_figure(output, rng):
    """Show the reference violin/box/mean treatment with investment categories."""
    labels = ["电子", "电力设备", "机械", "医药", "汽车", "传媒", "计算机", "食品饮料", "化工", "地产", "银行", "煤炭"]
    centers = np.linspace(2.2, -2.1, len(labels))
    groups = [rng.normal(mean, 0.8 + 0.2 * (i % 3), 240) for i, mean in enumerate(centers)]
    fig, ax = plt.subplots(figsize=(12.8, 6.5))
    fig.subplots_adjust(left=0.08, right=0.96, bottom=0.30, top=0.80)
    statistics = plot_violin(ax, groups, labels)
    fig.suptitle("行业月度超额收益分布", x=0.065, y=0.96, ha="left", fontsize=18)
    fig.text(0.065, 0.89, "按样本均值排序  ·  每组 240 个模拟观测  ·  箱体与分布轮廓共同呈现组间差异",
             color=COLORS["muted"], fontsize=11)
    ax.set_ylabel("月度超额收益（%）")
    ax.set_ylim(-5.8, 5.8)
    for label in ax.get_xticklabels():
        label.set_rotation(35)
        label.set_ha("right")
    for position, mean in enumerate(statistics["means"], 1):
        color = COLORS["blue"] if mean >= 0 else COLORS["gold_text"]
        ax.text(position, -0.24, f"{mean:.2f}", transform=ax.get_xaxis_transform(),
                ha="center", color=color, fontsize=10, clip_on=False)
    ax.text(0.0, -0.24, "均值", transform=ax.transAxes, ha="right", fontsize=9, color=COLORS["muted"])
    fig.legend(handles=[Patch(facecolor=COLORS["blue_light"], edgecolor=COLORS["blue"], label="均值 ≥ 0"),
                        Patch(facecolor=COLORS["gold_light"], edgecolor=COLORS["gold"], label="均值 < 0"),
                        Line2D([], [], color=COLORS["navy"], lw=1.7, label="中位数"),
                        Line2D([], [], color=COLORS["navy"], marker="D", ls="", label="均值")],
               loc="lower center", bbox_to_anchor=(0.5, 0.11), ncol=4)
    export_figure(fig, output / "03-violin", SOURCE,
                  "单位按 0–100 百分数表示，图中数值与标签由同一数组计算。", statistics)
    plt.close(fig)


def permutation_figure(output, rng):
    """Show two null distributions with tail counts and observed statistics."""
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 6.0))
    fig.subplots_adjust(left=0.075, right=0.95, bottom=0.24, top=0.78, wspace=0.28)
    fig.suptitle("因子与策略的置换检验", x=0.065, y=0.96, ha="left", fontsize=18)
    fig.text(0.065, 0.89, "观测统计量与置换样本对照  ·  金色柱体表示右尾样本  ·  p 值采用加一校正",
             color=COLORS["muted"], fontsize=11)
    statistics = {}
    for ax, title, values, observed, color, xlabel in [
        (axes[0], "A. 因子 Rank IC", rng.normal(0, 0.019, 2000), 0.044, "blue", "Rank IC"),
        (axes[1], "B. 策略年化超额收益", rng.normal(0, 3.0, 2000), 6.4, "green", "年化超额收益（%）"),
    ]:
        statistics[title] = plot_tail_distribution(ax, values, observed, color=color)
        ax.set_title(title, loc="left", pad=14)
        ax.set_xlabel(xlabel)
    fig.legend(handles=[Patch(facecolor=COLORS["blue_light"], edgecolor=COLORS["blue"], label="置换分布"),
                        Line2D([], [], color=COLORS["navy"], lw=2, label="观测值"),
                        Patch(facecolor=COLORS["gold_light"], edgecolor=COLORS["gold"], label="右尾样本")],
               loc="lower center", bbox_to_anchor=(0.5, 0.11), ncol=3)
    export_figure(fig, output / "04-permutation", SOURCE,
                  "图表入口接收已有置换结果，真实研究须按实际时间或分组结构生成置换样本。", statistics)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    with style_context():
        for render in (regularization_figure, ternary_figure, violin_figure, permutation_figure):
            render(arguments.output_dir, rng)
    print(json.dumps({"output_dir": str(arguments.output_dir), "figures": 4, "seed": SEED}, ensure_ascii=False))


if __name__ == "__main__":
    main()
