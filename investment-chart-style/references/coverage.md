# 30 类任务与参考图覆盖表

第一张总览包含重复图、多面板组合和流程示意。下表按可调用的生成任务计数，基本图形与专用组合模板都有独立数据入口。示例均采用统一主题和标明的模拟数据。

| 序号 | 类型标识 | 图形任务 | 参考总览对应内容 | 旧版直接入口 |
|---|---|---|---|---|
| 01 | `line` | 折线、误差带、参考线 | 逐被试 Macro-F1、会话稳定性 | 已有 |
| 02 | `ranked` | 排序点估计与区间、森林图 | Subject PERS ranking | 已有 |
| 03 | `violin` | 小提琴叠加箱线、均值与中位数 | 被试 PERS 分布、情绪概率分布 | 已有 |
| 04 | `permutation` | 置换直方图、密度与尾部 | Macro-F1 / PERS 置换检验 | 已有 |
| 05 | `ternary` | 三元散点与可选边际密度 | happy 条件下三元概率结构 | 已有，扩充组合布局 |
| 06 | `heatmap` | 有符号矩阵热力图 | Channel × Band importance | 已有 |
| 07 | `bar` | 单系列柱图、横向条形图 | Macro-F1、频段重要性、positive shift 排名 | 新增 |
| 08 | `grouped_bar` | 多模型或多指标分组柱图 | 模型性能比较 | 新增 |
| 09 | `stacked_bar` | 堆叠数量或百分比柱图 | 会话的情绪样本构成 | 新增 |
| 10 | `grouped_stacked_bar` | 分组内堆叠柱图 | 左上角 H4/H3 与分组构成 | 新增 |
| 11 | `diverging_bar` | 正负发散条形图 | PERS 正相关与负相关特征 | 新增 |
| 12 | `lollipop` | 棒棒糖排序图 | 重要性排名的点线表达变体 | 新增 |
| 13 | `scatter_regression` | 散点、回归线与均值置信带 | Subject PERS 与 Macro-F1 | 新增 |
| 14 | `bubble_scatter` | 面积编码的气泡散点 | 被试关系图增加第三变量的变体 | 新增 |
| 15 | `box` | 箱线与均值比较 | 会话分布中的箱体摘要 | 新增 |
| 16 | `raincloud` | 半小提琴、原始点与箱线 | PERS 跨会话分布 | 新增 |
| 17 | `histogram_kde` | 直方图与核密度 | 分布面板的通用形式 | 新增 |
| 18 | `ecdf_threshold` | 经验累积分布与阈值分区 | PERS 阈值与概率结构的累积分布表达 | 新增 |
| 19 | `confusion_matrix` | 归一化混淆矩阵 | Normalized Confusion Matrix | 新增 |
| 20 | `annotated_table` | 分组着色统计表 | Session-level PERS stability | 新增 |
| 21 | `matrix_marginals` | 样本矩阵与行列合计 | Subject × Emotion sample distribution | 新增 |
| 22 | `coefficient_paths` | 系数路径与非零特征数 | Elastic Net coefficient paths | 原有布局示例，现新增数据入口 |
| 23 | `cv_curve` | 验证曲线、SE 与一标准误差选择 | Cross-validation performance | 原有布局示例，现新增数据入口 |
| 24 | `volcano` | 效应值与 p 值筛选火山图 | EEG feature screening volcano plot | 新增 |
| 25 | `donut` | 环形构成图 | Band-level importance | 新增 |
| 26 | `scalp_topography` | 头皮轮廓与通道节点图 | EEG channel topography | 新增 |
| 27 | `region_map` | 输入区域轮廓与数值的示意图 | Brain region importance | 新增 |
| 28 | `flowchart` | 流程、分支、管线与概念关系 | 实验层级、数据检查、特征提取、PERS 概念图 | 新增 |
| 29 | `frequency_bands` | 多频段信号或正弦波示意 | delta / theta / alpha / beta / gamma 分解 | 新增 |
| 30 | `equation_panel` | 分布曲线与公式解释面板 | 差分熵和分布关系解释 | 新增 |

`bar` 的方向由 `data.orientation` 设置。`line` 可通过多个系列和 lower / upper 展示稳定性或模型比较。`flowchart` 可用自动 DAG 布局或显式节点坐标表达实验设计、数据处理和概念关系。多面板组合复用同一颜色语义和字号规则。

`scalp_topography` 是通道节点表达，连续电位或功率场需使用实际通道坐标与适用的空间插值。`region_map` 的解剖轮廓由输入数据决定，演示使用已标明的风格化轮廓。
