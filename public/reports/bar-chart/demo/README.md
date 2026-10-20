# 实验二：条形图基础——单系列条形图绘制

## 运行方法

解压压缩包，用 Edge、Chrome 等浏览器双击打开 `index.html`。
请保留 `index.html` 和 `echarts.min.js` 在同一文件夹中；运行无需联网，也无需安装 Node.js。

## 提交内容

- `index.html`：完整 HTML 源代码，包含完整 `option` 和关键配置的中文注释。
- `运行截图.png`：浏览器实际运行截图。
- `echarts.min.js`：本地 ECharts 6.0.0 库。
- `LICENSE`、`NOTICE`：随 ECharts 库附带的许可与声明文件。

## 实验数据

| 班级 | 一班 | 二班 | 三班 | 四班 | 五班 |
| --- | --- | --- | --- | --- | --- |
| 平均分 | 82 | 78 | 90 | 85 | 76 |

## 关键配置说明

1. `xAxis.type: 'value'`：横轴显示数值，`name: '平均分'` 设置横轴名称。
2. `yAxis.type: 'category'`：纵轴显示五个班级，`name: '班级'` 设置纵轴名称。
3. `yAxis.inverse: true`：让一班至五班从上到下依次显示，不改变数据对应关系。
4. `series` 只有一个对象，`type: 'bar'` 表示条形图，`data` 是与班级顺序对应的平均分。
5. `label.show: true`：直接在条形右侧显示分数。
6. `myChart.setOption(option)`：将完整配置应用到图表。

数值轴放在横轴、类别轴放在纵轴，因此得到横向条形图。容器严格采用实验要求的 800 × 500 像素。

## 运行验证

已在 Microsoft Edge 浏览器中通过本地文件、离线方式运行验证：

- 图表容器为 800 × 500 像素，五个班级及分数与题目一致。
- 横轴为数值轴、纵轴为类别轴，仅有一个条形图系列。
- 鼠标悬停三班时显示“平均分：90 分”。
- 未检测到 JavaScript 异常、控制台错误或资源加载失败。
- `运行截图.png` 是实际运行截图，按 2 倍像素密度保存，文字更清晰。

## 参考

- [Apache ECharts 入门文档](https://echarts.apache.org/handbook/en/get-started/)
- [Apache ECharts 条形图文档](https://echarts.apache.org/handbook/en/how-to/chart-types/bar/basic-bar/)
- 库文件来源：`https://cdn.jsdelivr.net/npm/echarts@6.0.0/dist/echarts.min.js`
