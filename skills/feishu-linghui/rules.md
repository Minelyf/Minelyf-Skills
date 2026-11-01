# 飞书画板的限制

都是在真实画板上试出来的。SVG 能写的东西很多，飞书只认其中一部分，其余会被拍成图片或直接丢掉。

## 能用的形状

- 只用 `<rect>`（可圆角 `rx`）、`<circle>`、`<ellipse>`、直线 `<line>` / 折线 `<polyline>`、`<text>` / `<tspan>`。这些会变成画板里可编辑的原生元素。
- `<polygon>`、曲线 `<path>` 会被当成图片嵌进去，边缘发糊，不要拿来做结构。
- 箭头：给 `<line>` / `<polyline>` 加 `marker-end="url(#arrow)"`，marker 里的 path 要带 `fill`，飞书会转成干净的实心箭头连线。不要自己画三角形当箭头。连线保持横平竖直。

## 不支持的

- 渐变、滤镜、阴影模糊、`pattern`、`clipPath`、`mask`。
- 透明度：`opacity` 一律当不透明。要浅色就直接用更浅的色值。
- 字体：画板只有一种字体，不要写 `font-family`。层次只靠字号、粗细。
- 变形：只用 `translate` / `rotate` / `scale`，不要 `skew` / `matrix`。

## 线宽

画板只有三档：≤1 很细，1.5～2 细，≥3 中等。虚线 `stroke-dasharray` 会保留。

## 文字

- 文字必须是 `<text>`，不能转成路径。
- 字按字宽折行：中文约 1 个字号宽，英文数字约 0.6 个字号宽。框要留足余量，长句自己拆成几行，别靠缩小字号塞进去。
- 1000 宽的画布上，最小字号 14；正文 16；分区标题 18；大标题 26；大数字 28。
- 导出的 PNG 里文字颜色经常不准（常显示成黑色），判断颜色看线上画板或 raw 节点里的色值，别看导出图。

## 导出和检查

- 本地渲染：`npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -o diagram.png -f svg`，加 `--check` 会报文字溢出和重叠（有意的重叠可忽略，以看图为准）。
- 写入后：`lark-cli whiteboard +export --output-type svg` 再本地转 PNG 看效果。写入后立刻用 `+query --output_as image` 拿到的是缓存，常常只有一部分，不要据此判断。
- raw 节点：`+export --output-type raw` 导出的 JSON 可以原样用 `+update --input_format raw --overwrite` 写回，改字、加行都靠它。文字节点是 `text_shape`，宽度固定，改长了要同步调 `width`。
