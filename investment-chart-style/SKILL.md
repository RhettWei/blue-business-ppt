---
name: investment-chart-style
description: 按统一的蓝金低饱和风格生成与重绘投研、统计和科研图表，提供 30 类可运行模板，覆盖比较、分布、模型验证、概率、矩阵、通道与区域图和流程示意，适用于成套报告图表或统一已有 Matplotlib 图形。
metadata:
  version: "2.0.0"
---

# 投研图表设计

把用户数据绘制为适合研究报告和展示的图表。默认采用白底、低饱和蓝金与鼠尾草绿、细轴线、轻网格、半透明分布、就近标注和统一面板布局。根据用户的模板、语义和展示尺寸调整这些默认值。

## 开始工作

识别图表回答的问题、数据来源、字段、单位和交付位置。利用现有文件和上下文补齐输入，只询问会改变结论或图形含义的缺失信息。先检查数据，再决定聚合、排序、归一化和图形类型。

- 读取 [references/design-system.md](references/design-system.md)，确定配色、尺寸、字体和标注。
- 按所需图形读取 [references/chart-recipes.md](references/chart-recipes.md) 中的相关部分。
- 用 [references/coverage.md](references/coverage.md) 查找 30 类任务及样图对应关系，新增任务的字段见 [references/extended-patterns.md](references/extended-patterns.md)。
- 涉及估值、收益、模型、概率或统计检验时，读取 [references/data-checks.md](references/data-checks.md) 的对应项目。

## 实现方式

Python 3.10+，基础运行依赖为 Matplotlib 3.9+ 和 NumPy。直接绘图模板不依赖另一个 skill。读取 CSV / Excel 或拟合模型时按任务使用 Pandas、openpyxl、scikit-learn 等依赖。实际使用前检查依赖是否可导入。

`scripts/chart_style.py` 提供统一样式和原有六类图形，`scripts/extended_patterns.py` 提供新增 24 类模板及三元边际组合。全部入口共享配色、字体、轴线、图注和导出逻辑。

```python
from pathlib import Path
import sys

skill_dir = Path("<当前 skill 的绝对目录>")
sys.path.insert(0, str(skill_dir / "scripts"))
from chart_style import style_context, format_axis, export_figure
import matplotlib.pyplot as plt

with style_context():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    format_axis(ax)
    # 从用户文件计算数据，并在此绘图。
    export_figure(fig, Path("outputs/chart"), source="用户提供的实际数据文件")
```

也可将计算后的数据写成 JSON 规格，调用基础渲染入口。

```bash
python <skill-dir>/scripts/render_chart.py chart.json --output outputs/chart
```

原有 `line`、`ranked`、`violin`、`permutation`、`ternary` 和 `heatmap` 规格继续可用。完整类型列表可用以下命令查看。

```bash
python <skill-dir>/scripts/render_chart.py --list-types
```

30 类 JSON 示例见 `examples/catalog/`，索引为 [examples/catalog/index.json](examples/catalog/index.json)。从匹配的示例复制结构，用实际数据替换数组、来源和口径。组合页可在一个脚本内调用多种模板，保留各面板的数值定义。

同风格图集可直接重新生成。

```bash
python <skill-dir>/scripts/render_catalog.py --output-dir outputs/chart-catalog
```

30 类按生成任务计数，其中包含基础图形、统计专用模板和组合图。参考总览中的重复页及组合页可通过同一模板的不同数据、布局或多面板组合覆盖。

## 视觉选择

- 以共同坐标上的位置表达主要比较。用灰色压低背景系列，用蓝色、金色或绿色强调少量关注对象。
- 按样图风格绘制分布时，采用半透明小提琴、白色箱体、深色中位线、菱形均值及必要参考线。
- 多面板图按阅读顺序编排，使用 A / B 等面板标记。相同指标采用一致的刻度、单位和颜色语义。
- 中文采用系统可用的中文字体，英文和数字优先 Arial。打印和投影时按最终尺寸检查字号。
- 数量、金融含义和读者习惯决定正负颜色。默认蓝金编码适用于分类和相对参考值的比较。A 股涨跌色、客户模板等按明确需求设置。

## 交付与检查

默认保存 PNG 300 DPI、SVG、PDF、可复现脚本及来源记录。用户要求其他格式时遵从其要求。SVG 保留文本，PDF 嵌入 TrueType 字体。实际可编辑效果受接收端字体支持影响。

运行生成脚本并查看 PNG，检查中文缺字、标签重叠、图例遮挡、边界裁切、面板对齐、颜色和最终尺寸可读性。核对单位、坐标映射、排序、标注值及样本范围。修复观察到的问题后重新导出受影响图形。

已有 `matplotlib` skill 可作为额外的图形实现资源。用户同时调用两者时，以本 skill 的配色、轴线和图例为视觉约定，结合其图形模式与检查工具。其检查器中的 STYLE 项反映原版默认风格，按当前用户目标评估。

随附样例由 `scripts/render_gallery.py` 生成，数据使用固定随机种子模拟，图注明确标识模拟。样例用于展示风格和接口。真实投研任务从用户数据与可核实来源计算数值，保留处理脚本、口径及来源。

头皮节点图使用输入的二维电极位置，区域图使用输入的多边形。真实研究沿用实际坐标、配准结果和测量单位。演示轮廓与电极示意在图注中标明。对需要连续 EEG 插值的任务，可结合 MNE 读取实际 montage 并应用本 skill 的颜色、标注与导出规范。

## 风格来源

本 skill 根据用户提供的五张图归纳视觉规则，独立编写绘图实现。参考图中的软件、私有 skill 名称和提示词无法从最终图片确认。模板采用标准数值定义，例如正则化参数方向、三元归一化及由置换样本计算的 p 值。
