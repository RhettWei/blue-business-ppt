# 扩展模板字段与数值定义

共用顶层字段为 `type`、`title`、`data`，可设置 `source`、`note`、`figsize`、`xlabel`、`ylabel` 和 `unit`。数据从真实来源处理后写入 JSON，代码保留计算过程。

每类都有 `examples/catalog/NN-type.json` 示例，使用索引文件查找。示例中的模拟说明随实际数据和来源一起替换。所有模板共享 `chart_style.py` 中的样式，单独改配色时同时检查同一报告的其他面板。

## 比较与构成

| 类型 | data 必需字段 | 可选字段 |
|---|---|---|
| `bar` | `labels`，`values` | `orientation` 为 vertical / horizontal，`highlight_indices` |
| `grouped_bar` | `labels`，`series`，每组为 name / values | `show_values` |
| `stacked_bar` | `labels`，`series` | `normalize` 默认 false，true 按每类别总和转为百分比 |
| `grouped_stacked_bar` | `labels`，`groups`，每组为 name / series | 各组的堆叠组分名称和顺序一致 |
| `diverging_bar` | `labels`，`values` | 正负分别使用蓝色和金色，横轴关于零对称 |
| `lollipop` | `labels`，`values` | 从零到观测值绘制细杆，按值排序 |
| `donut` | `labels`，`values` | `center_text` |

普通柱图保留零基线。堆叠图的正负值分别累积。归一化和分组堆叠要求非负构成。环图份额从输入值与总和计算。

## 散点与分布

| 类型 | data 必需字段 | 可选字段 |
|---|---|---|
| `scatter_regression` | `x`，`y` | `labels`，显示用户提供的点标签 |
| `bubble_scatter` | `x`，`y`，`sizes` | `groups` |
| `box` | `labels`，`groups` | 每组为原始观测数组 |
| `raincloud` | `labels`，`groups` | `jitter_seed` 仅控制点的横向错位 |
| `histogram_kde` | `values` | `bins` |
| `ecdf_threshold` | `values` | `threshold` 默认零 |

散点回归使用 OLS，并绘制均值响应的 95% 正态近似置信带。实际小样本推断、聚类稳健区间、面板依赖或加权回归可用相应模型的估计结果另行绘制，图注说明方法。常量 y 的相关系数记录为未定义。

气泡面积与 sizes 成正比，零尺寸保留为零。x/y 缺失按完整配对处理，其他字段同步对齐。分布图只移除本组缺失值，保留实际样本量。直方图与 KDE 使用同一数组，KDE 曲线按频数刻度缩放。经验累积概率按小于等于阈值的实际样本比例计算。

## 矩阵与表格

| 类型 | data 必需字段 | 可选字段 |
|---|---|---|
| `confusion_matrix` | `matrix`，`labels` | `normalize` 为 row / none |
| `annotated_table` | `rows`，`columns` | `row_labels`，`summary_columns`，`font_size` |
| `matrix_marginals` | `matrix`，`row_labels`，`column_labels` | 矩阵为非负计数 |

混淆矩阵的行表示真实类别，列表示预测类别。按行归一化时零样本行显示 NA，原始矩阵仍记录在输入文件中。样本矩阵的行列边际从同一矩阵计算。统计表的均值、p 值和其他摘要应在数据准备脚本中计算。

## 模型与特征

| 类型 | data 必需字段 | 可选字段 |
|---|---|---|
| `coefficient_paths` | `x`，`coefficients`，`feature_names` | `highlight_indices`，`parameter_name`，`references`，`zero_tolerance` |
| `cv_curve` | `x`，`means`，`se` | `objective` 为 max / min，`regularization_strength`，`parameter_name` |
| `volcano` | `effects`，`p_values` | `p_threshold`，`effect_threshold`，`labels`，`label_count` |

系数矩阵形状为参数点数 × 特征数，x 严格单调，默认保持输入方向。次坐标轴从系数数组计算非零个数。正则化值递减显示时，标明 log(λ) 的实际刻度。

CV 一标准误差选择需要同长度的 `regularization_strength`，它表示实际惩罚强度。模板先确定最优均值，再从一标准误差可接受区间中选择最大惩罚强度。指标最大化和最小化分别计算阈值。

火山图的 p 值范围为 (0, 1]，纵轴为 −log10(p)。输入是调整后 p 值时在标题或图注说明，筛选按输入 p 值和效应阈值执行。下溢零值按实际统计计算精度处理后输入，处理方法写入数据准备代码。

## 空间、流程与解释图

| 类型 | data 必需字段 | 可选字段 |
|---|---|---|
| `scalp_topography` | `positions`，`values`，`labels` | `value_label` |
| `region_map` | `regions`，每项为 name / polygon / value | `geometry_source`，各区域 `label_position` |
| `flowchart` | `nodes`，每项为 id / label | `edges`，各节点 position / width / height / wrap / font_size |
| `frequency_bands` | `time`，`bands` | 每频段输入 signal 或 frequency / amplitude / phase |
| `equation_panel` | `x`，`curves`，`formula` | `description`，`formula_size` |

头皮图接收归一化圆盘中的二维位置，节点颜色和相对大小编码通道值。连续 EEG 场可用 MNE 的实际 montage 和插值接口实现，并沿用本主题。区域图直接绘制输入多边形，图注标明几何来源和数值含义。

流程图 edges 的 from / to 引用节点 id，可包含 label 和 Matplotlib connectionstyle。自动布局用于有向无环图，循环图为每个节点提供 position。节点文本中的换行会保留。

频段图传入 signal 时绘制实际数组。传入 frequency 时按时间数组计算正弦示意，图注写明示意。时间单位为秒，frequency 单位为 Hz。公式图接收 Matplotlib MathText 字符串，并从输入 curves 绘制曲线。

三元图在原规格上增加 `data.marginals=true`，会展示来自同一归一化数组的三条边际密度。顶点顺序和边界定义见 chart-recipes.md。

## 开源方法参考

模板采用独立实现，共用 Matplotlib 和 NumPy 数值及绘图接口。以下官方文档可用于核对 API、统计图形表达和专业空间图的输入要求。

- [Matplotlib 小提琴图示例](https://matplotlib.org/stable/gallery/statistics/violinplot.html)
- [Matplotlib 环形图与标注示例](https://matplotlib.org/stable/gallery/pie_and_polar_charts/pie_and_donut_labels.html)
- [MNE topomap 接口与通道位置要求](https://mne.tools/stable/generated/mne.viz.plot_topomap.html)
