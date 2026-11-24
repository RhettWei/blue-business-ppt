"""Render the 30-task catalog with reproducible, explicitly simulated inputs."""

import argparse
import json
from pathlib import Path

import numpy as np

from render_chart import CHART_TYPES, render


TASK_NAMES = {
    "line": "折线与误差带", "ranked": "排序区间与森林图", "violin": "小提琴叠加箱线图",
    "permutation": "置换检验分布", "ternary": "三元概率与边际分布", "heatmap": "数值热力图",
    "bar": "单系列柱状与条形图", "grouped_bar": "分组柱状图", "stacked_bar": "堆叠柱状图",
    "grouped_stacked_bar": "分组堆叠柱状图", "diverging_bar": "正负发散条形图", "lollipop": "棒棒糖排序图",
    "scatter_regression": "散点回归与置信带", "bubble_scatter": "气泡散点图", "box": "箱线比较图",
    "raincloud": "雨云与半小提琴图", "histogram_kde": "直方图与核密度", "ecdf_threshold": "累积概率与阈值分区",
    "confusion_matrix": "归一化混淆矩阵", "annotated_table": "着色统计表", "matrix_marginals": "样本矩阵与边际合计",
    "coefficient_paths": "正则化系数路径", "cv_curve": "交叉验证与一标准误差规则", "volcano": "特征筛选火山图",
    "donut": "环形构成图", "scalp_topography": "头皮通道节点分布图", "region_map": "区域轮廓与脑区示意图",
    "flowchart": "流程与概念关系图", "frequency_bands": "频段波形图", "equation_panel": "分布与公式解释图",
}


def example_data(seed=20261117):
    rng = np.random.default_rng(seed)
    groups = [rng.normal(mean, 0.16, 70).tolist() for mean in [0.24, 0.10, -0.04, -0.18]]
    log_lambda = np.linspace(-1, -6, 35)
    lambdas = np.exp(log_lambda)
    amplitudes = np.array([0.9, 0.65, 0.4, 0.2, -0.25, -0.5, -0.78])
    thresholds = np.array([0.22, 0.12, 0.04, 0.018, 0.15, 0.09, 0.025])
    coefficients = amplitudes[None, :]*np.maximum(1-lambdas[:, None]/thresholds[None, :], 0)
    cv_x = np.linspace(-1, -6, 20)
    scores = 0.09+0.12*np.exp(-((cv_x+3.8)/1.6)**2)
    scatter_x = np.linspace(-0.2, 0.25, 24)
    scatter_y = 0.34+0.25*scatter_x+rng.normal(0, 0.027, len(scatter_x))
    effects = rng.normal(0, 0.32, 180)
    p_values = np.clip(np.exp(-7*np.abs(effects)+rng.normal(0, 0.8, len(effects))), 1e-8, 1)
    channels = ["Fp1", "Fp2", "F3", "Fz", "F4", "T7", "C3", "Cz", "C4", "T8", "P3", "Pz", "P4", "O1", "Oz", "O2"]
    positions = [[-0.32, 0.84], [0.32, 0.84], [-0.47, 0.48], [0, 0.54], [0.47, 0.48],
                 [-0.88, 0], [-0.45, 0], [0, 0], [0.45, 0], [0.88, 0],
                 [-0.45, -0.45], [0, -0.52], [0.45, -0.45], [-0.32, -0.84], [0, -0.88], [0.32, -0.84]]
    time = np.linspace(0, 1, 401)
    normal_x = np.linspace(-3.2, 3.2, 160)
    examples = {
        "line": {"x": list(range(1, 11)), "series": [
            {"name": "模型 A", "y": [0.29, 0.33, 0.31, 0.36, 0.32, 0.35, 0.34, 0.38, 0.35, 0.37],
             "lower": [0.26, 0.30, 0.28, 0.33, 0.29, 0.32, 0.31, 0.35, 0.32, 0.34],
             "upper": [0.32, 0.36, 0.34, 0.39, 0.35, 0.38, 0.37, 0.41, 0.38, 0.40]},
            {"name": "比较基线", "y": [0.27, 0.28, 0.29, 0.27, 0.29, 0.30, 0.28, 0.29, 0.30, 0.31]}]},
        "ranked": {"labels": ["S01", "S02", "S03", "S04", "S05", "S06"],
                   "values": [0.24, 0.18, 0.10, 0.02, -0.06, -0.16],
                   "lower": [0.18, 0.12, 0.02, -0.04, -0.13, -0.23],
                   "upper": [0.30, 0.25, 0.16, 0.09, 0.02, -0.09]},
        "violin": {"labels": ["组 A", "组 B", "组 C", "组 D"], "groups": groups},
        "permutation": {"null_values": rng.normal(0.24, 0.033, 800).tolist(), "observed": 0.32, "bins": 25},
        "ternary": {"probabilities": rng.dirichlet([4.5, 3, 2.5], 350).tolist(),
                    "labels": ["增长", "基准", "压力"], "marginals": True},
        "heatmap": {"matrix": np.round(rng.uniform(-0.8, 0.8, (7, 5)), 2).tolist(),
                    "row_labels": ["Fp1", "F3", "Fz", "C3", "Cz", "P3", "Oz"],
                    "column_labels": ["delta", "theta", "alpha", "beta", "gamma"]},
        "bar": {"labels": ["基线", "方法 A", "方法 B", "方法 C"], "values": [0.26, 0.31, 0.34, 0.39], "highlight_indices": [3]},
        "grouped_bar": {"labels": ["Accuracy", "Macro-F1", "Recall"], "series": [
            {"name": "基线", "values": [0.42, 0.28, 0.31]}, {"name": "模型 A", "values": [0.55, 0.37, 0.40]},
            {"name": "模型 B", "values": [0.60, 0.41, 0.45]}]},
        "stacked_bar": {"labels": ["Session 1", "Session 2", "Session 3"], "series": [
            {"name": "neutral", "values": [90, 90, 90]}, {"name": "sad", "values": [90, 90, 90]},
            {"name": "fear", "values": [90, 90, 90]}, {"name": "happy", "values": [90, 90, 90]}]},
        "grouped_stacked_bar": {"labels": ["pTE", "cTE", "non-TE"], "groups": [
            {"name": "H4", "series": [{"name": "组分 A", "values": [38, 24, 47]}, {"name": "组分 B", "values": [7, 6, 9]}, {"name": "组分 C", "values": [9, 5, 12]}]},
            {"name": "H3", "series": [{"name": "组分 A", "values": [42, 23, 43]}, {"name": "组分 B", "values": [8, 5, 10]}, {"name": "组分 C", "values": [7, 6, 9]}]}]},
        "diverging_bar": {"labels": ["因子 A", "因子 B", "因子 C", "因子 D", "因子 E", "因子 F"],
                          "values": [-0.27, -0.20, -0.13, 0.12, 0.21, 0.29]},
        "lollipop": {"labels": ["gamma", "beta", "alpha", "theta", "delta"], "values": [0.28, 0.22, 0.19, 0.17, 0.14]},
        "scatter_regression": {"x": scatter_x.tolist(), "y": scatter_y.tolist()},
        "bubble_scatter": {"x": [0.02, 0.07, 0.10, 0.15, 0.18, 0.24, 0.28, 0.31],
                           "y": [0.29, 0.33, 0.35, 0.32, 0.37, 0.40, 0.36, 0.43],
                           "sizes": [50, 100, 75, 140, 80, 170, 110, 160],
                           "groups": ["组 A", "组 A", "组 B", "组 A", "组 B", "组 B", "组 A", "组 B"]},
        "box": {"labels": ["Session 1", "Session 2", "Session 3"], "groups": groups[:3]},
        "raincloud": {"labels": ["Session 1", "Session 2", "Session 3"], "groups": groups[:3]},
        "histogram_kde": {"values": rng.normal(0.01, 0.045, 450).tolist(), "bins": 25},
        "ecdf_threshold": {"values": rng.normal(0.06, 0.24, 350).tolist(), "threshold": 0},
        "confusion_matrix": {"matrix": [[31, 12, 10, 9], [13, 28, 12, 11], [10, 14, 29, 12], [8, 11, 13, 35]],
                             "labels": ["neutral", "sad", "fear", "happy"], "normalize": "row"},
        "annotated_table": {"columns": ["Session 1", "Session 2", "Session 3", "均值"],
                            "rows": [[0.21, 0.26, 0.24, 0.24], [0.18, 0.18, 0.19, 0.18],
                                     [0.12, 0.14, 0.10, 0.12], [-0.04, -0.07, -0.05, -0.05], [-0.16, -0.20, -0.18, -0.18]],
                            "row_labels": ["S01", "S02", "S03", "S04", "S05"], "summary_columns": ["均值"]},
        "matrix_marginals": {"matrix": [[18, 18, 18, 18], [18, 18, 18, 18], [17, 18, 16, 19],
                                        [19, 18, 18, 17], [18, 20, 18, 18], [16, 17, 18, 18]],
                             "row_labels": ["S01", "S02", "S03", "S04", "S05", "S06"],
                             "column_labels": ["neutral", "sad", "fear", "happy"]},
        "coefficient_paths": {"x": log_lambda.tolist(), "coefficients": coefficients.tolist(),
                              "feature_names": ["价值", "盈利", "质量", "规模", "杠杆", "波动", "换手"], "highlight_indices": [0, 1, 5, 6]},
        "cv_curve": {"x": cv_x.tolist(), "means": scores.tolist(), "se": [0.012]*len(cv_x),
                     "regularization_strength": np.exp(cv_x).tolist(), "objective": "max"},
        "volcano": {"effects": effects.tolist(), "p_values": p_values.tolist(), "p_threshold": 0.05,
                    "effect_threshold": 0.25, "labels": [f"F{i+1}" for i in range(len(effects))], "label_count": 3},
        "donut": {"labels": ["gamma", "beta", "alpha", "theta", "delta"], "values": [0.28, 0.22, 0.19, 0.17, 0.14], "center_text": "频段\n重要性"},
        "scalp_topography": {"positions": positions, "values": rng.uniform(0.1, 0.35, len(channels)).tolist(),
                             "labels": channels, "value_label": "通道重要性"},
        "region_map": {"geometry_source": "stylized demonstration polygons", "regions": [
            {"name": "Frontal", "value": 0.24, "polygon": [[0, 0.55], [0.12, 0.91], [0.46, 1.04], [0.51, 0.55]], "label_position": [0.26, 0.76]},
            {"name": "Central", "value": 0.21, "polygon": [[0.46, 1.04], [0.78, 1.0], [0.80, 0.60], [0.51, 0.55]], "label_position": [0.64, 0.80]},
            {"name": "Parietal", "value": 0.18, "polygon": [[0.78, 1.0], [1.08, 0.78], [1.12, 0.48], [0.80, 0.60]], "label_position": [0.94, 0.72]},
            {"name": "Occipital", "value": 0.16, "polygon": [[0.80, 0.60], [1.12, 0.48], [1.00, 0.14], [0.67, 0.10]], "label_position": [0.91, 0.32]},
            {"name": "Temporal", "value": 0.21, "polygon": [[0, 0.55], [0.51, 0.55], [0.80, 0.60], [0.67, 0.10], [0.25, 0.12]], "label_position": [0.42, 0.32]}]},
        "flowchart": {"nodes": [{"id": "a", "label": "数据输入"}, {"id": "b", "label": "质量检查"},
                                {"id": "c", "label": "特征计算"}, {"id": "d", "label": "分组验证"},
                                {"id": "e", "label": "模型评估"}, {"id": "f", "label": "结论整理"}],
                      "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "c"}, {"from": "c", "to": "d"},
                                {"from": "d", "to": "e"}, {"from": "d", "to": "f"}]},
        "frequency_bands": {"time": time.tolist(), "bands": [
            {"name": "delta · 1.5 Hz", "frequency": 1.5}, {"name": "theta · 6 Hz", "frequency": 6},
            {"name": "alpha · 10 Hz", "frequency": 10}, {"name": "beta · 20 Hz", "frequency": 20},
            {"name": "gamma · 35 Hz", "frequency": 35}]},
        "equation_panel": {"x": normal_x.tolist(), "curves": [
            {"name": "σ = 1.0", "y": (np.exp(-0.5*normal_x**2)/np.sqrt(2*np.pi)).tolist()},
            {"name": "σ = 0.6", "y": (np.exp(-0.5*(normal_x/0.6)**2)/(0.6*np.sqrt(2*np.pi))).tolist()}],
            "formula": r"$h(X)=\frac{1}{2}\log(2\pi e\sigma^2)$",
            "description": "正态分布的微分熵取决于方差，图示对比两种标准差。", "formula_size": 16},
    }
    specs = []
    axis_labels = {
        "line": ("留出样本序号", "Macro-F1"), "ranked": ("Subject PERS", ""),
        "violin": ("样本组", "PERS sample"), "permutation": ("Macro-F1", "频数"),
        "bar": ("比较方法", "Macro-F1"), "grouped_bar": ("评价指标", "得分"),
        "stacked_bar": ("会话", "样本数"), "grouped_stacked_bar": ("分组", "比例（%）"),
        "diverging_bar": ("标准化系数", ""), "lollipop": ("归一化重要性", ""),
        "scatter_regression": ("Subject PERS", "Macro-F1"), "bubble_scatter": ("因子 IC", "收益率（%）"),
        "box": ("会话", "PERS sample"), "raincloud": ("会话", "PERS sample"),
        "histogram_kde": ("月度收益率", "频数"), "ecdf_threshold": ("PERS sample", "经验累积概率"),
        "cv_curve": (r"$\log(\lambda)$", "交叉验证得分"),
        "equation_panel": ("X", "概率密度"),
    }
    for index, kind in enumerate(CHART_TYPES, 1):
        note = "模拟数据，用于展示统一风格及该类图表的生成接口。"
        if kind == "scalp_topography":
            note = "通道数值及二维位置为示意，真实任务读取实际电极坐标。"
        elif kind == "region_map":
            note = "区域轮廓与数值为示意，真实任务可输入已配准的区域多边形。"
        elif kind == "scatter_regression":
            note = "阴影为均值响应的 95% 正态近似置信带，数据为模拟。"
        elif kind == "frequency_bands":
            note = "按所列频率计算的正弦波示意，真实波形可通过 signal 数组输入。"
        spec = {"type": kind, "title": TASK_NAMES[kind], "source": f"统一风格图集 · 模拟数据 · 随机种子 {seed}",
                "note": note, "data": examples[kind], "figsize": [9, 5.8]}
        if kind in axis_labels:
            spec["xlabel"], spec["ylabel"] = axis_labels[kind]
        if kind in {"ternary", "equation_panel"}:
            spec["figsize"] = [12, 7]
        if kind == "coefficient_paths":
            spec["figsize"] = [10, 6.5]
        specs.append((f"{index:02d}-{kind}", spec))
    return specs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", default=20261117, type=int)
    parser.add_argument("--specs-only", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    specification_dir = args.output_dir / "specifications"
    specification_dir.mkdir(exist_ok=True)
    specs = example_data(args.seed)
    if len(specs) != 30 or len(set(CHART_TYPES)) != 30:
        raise AssertionError("The catalog must contain exactly 30 distinct task identifiers")
    manifest = []
    for stem, specification in specs:
        path = specification_dir / (stem+".json")
        path.write_text(json.dumps(specification, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.specs_only:
            render(specification, args.output_dir / stem)
        manifest.append({"stem": stem, "type": specification["type"], "title": specification["title"],
                         "specification": "specifications/"+path.name})
        print(stem, flush=True)
    (args.output_dir / "catalog.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
