# UserCF 实验复现说明

本项目实现基于用户的协同过滤，比较余弦、Jaccard 和 Pearson 三种相似度，提供可运行的 Python 代码、实际运行结果和 Word 实验报告。数据采用 GroupLens MovieLens 100K，包含 943 名用户、1682 部电影和 100000 条评分。

## 运行方法

使用 **Python 3.12**，已验证版本为 Python 3.12.14。解压后，在本文件所在文件夹打开终端，依次运行：

```bash
python -m pip install -r requirements.txt
python usercf_experiment.py --download
python -m unittest -v test_usercf
python build_report.py
```

第二条命令从 GroupLens 下载缺失的数据并执行完整实验；第三条运行算法与评估测试；第四条读取 `results` 中的数据与图表，重建 Word 报告。已有数据时，可直接运行 `python usercf_experiment.py`。重跑会更新结果文件，耗时因机器而异。

如已从官网下载并解压数据，也可运行：

```bash
python usercf_experiment.py --data-dir ./ml-100k
```

该目录中应有 `u.data` 和 `u.item`。本项目应在本地 Python 环境运行；不要粘贴到 Node.js 或 JavaScript 判题入口。

## 实验设置与结果口径

- 随机种子为 `20261005`，按用户随机拆分约 60% 训练、20% 验证、20% 测试数据。本次实际分别为 60734、19633、19633 条评分。矩阵中的 `0` 表示未评分。
- 在验证集比较三种相似度与 `K = 5、10、20、40、80` 的组合，固定推荐数量 `N = 10`。按验证集 Precision@10 选参，并列时依次比较 Recall@10、较小的 K 和方法名。选定后用训练集与验证集合并重训，最后在独立测试集评估，并与热门电影基线比较。
- 余弦使用零填充的评分向量；Jaccard 使用已评分电影集合；Pearson 仅在两名用户共同评分的电影上计算均值与相关系数。三种方法均要求至少 3 部共同评分电影；不足、分母为零或对角线上的相似度均置零。选邻居时只保留正相似度。
- Top-N 根据邻居的正反馈加权投票，评分不低于 4 分视为正反馈：`score(u,i) = Σ[sim(u,v) × I(r(v,i) ≥ 4)] / Σsim(u,v)`。求和范围为选中的邻居，分母对同一用户的全部候选一致。推荐排除用户已评分电影，仅保留排序分大于零的电影；**排序分不是预测星级**。
- Precision@10 为所有用户的命中数之和除以 `用户数 × 10`，不足 10 条的推荐不缩小分母。Recall@10 仅对留出集中存在正反馈的用户求平均。电影覆盖率为所有用户推荐电影的并集大小除以完整目录 **1682**；用户覆盖率为获得至少一条推荐的用户比例。
- 计时先预热一次，再运行三次取中位数；数据读取、下载和画图不计入算法时间。线性代数计算线程固定为 1。运行时间与机器、系统负载及依赖环境有关，重跑时无需与已附计时逐位一致。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `usercf_experiment.py` | 数据处理、相似度计算、邻居选择、推荐生成、评估和绘图 |
| `test_usercf.py` | 算法正确性、拆分与评估边界的自动测试 |
| `build_report.py` | 根据已有实验结果重建 Word 报告 |
| `requirements.txt` | 固定本次使用的依赖版本 |
| `results/experiment_results.json` | 数据统计、参数实验、最终评估、计时和示例推荐的完整结果 |
| `results/validation_metrics.csv`、`test_metrics.csv` | 验证参数对比与独立测试指标 |
| `results/sample_recommendations.csv`、`scaling_metrics.csv` | 用户 1 的推荐示例与用户规模计时结果 |
| `results/similarity_matrices.npz` | 三种训练集相似度完整矩阵及最终所选模型矩阵，均为 943 × 943 |
| `results/similarity_*_first6.csv`、`similarity_matrices.png` | 前 6 名用户的相似度节选与热力图 |
| `results/topk_*.png`、`runtime_scaling.png` | K 与准确率、覆盖率、耗时的关系及用户规模耗时曲线 |

`similarity_matrices.npz` 的键为 `cosine`、`jaccard`、`pearson` 和 `final_selected`，可通过 `numpy.load()` 读取。内部用户和电影索引从 0 开始；CSV 示例中的公开用户与电影 ID 从 1 开始。

## 数据来源与使用许可

数据来源：[GroupLens MovieLens 100K](https://grouplens.org/datasets/movielens/100k/)。原始评分与电影数据不包含在交付压缩包内；`--download` 从官方网站下载所需文件，并保留数据集 README。

请遵守[数据集使用许可与引用要求](https://files.grouplens.org/datasets/movielens/ml-100k-README.txt)：研究成果需注明数据来源，未经单独许可不得再分发原始数据，商业用途需事先获得许可。数据集推荐引用：F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context*. [DOI 10.1145/2827872](https://doi.org/10.1145/2827872)。
