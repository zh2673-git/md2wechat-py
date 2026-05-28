# 配图方案

## 核心原则

**图文相辅，不为配图而配图。** 配图是为了帮助读者理解复杂概念、建立视觉记忆，而不是装饰。每张图都必须有"为什么这里需要一张图"的理由。

---

## 三种方案

| 方案 | 适用场景 | 优点 | 优先级 |
|------|---------|------|--------|
| **方案A：SVG 直出 → PNG** | 结构图、流程图、数据图、层级图、概念示意图 | 精确可控、文字清晰、文件小、公众号渲染友好 | **首选** |
| **方案B：Canvas 动画 → GIF** | 状态转换、运动过程、流动路径、力度衰减等变化过程 | 微信支持 GIF 动图、动态过程比静态图直观10倍 | **动态过程必选** |
| **方案C：image_gen AI 生图** | 需要实际照片风格、写实场景、复杂视觉效果 | 视觉丰富、可处理复杂构图 | **最后备选** |

**决策核心：内容是否包含时间维度？**
- 静态结构/关系/对比 → 方案A（SVG→PNG）
- 有变化过程/状态转换/运动 → 方案B（Canvas→GIF）
- 需要写实照片风格 → 方案C（AI生图）

---

## 配图触发条件

| 场景 | 配图类型 | 说明 |
|------|---------|------|
| 文章解释**层级/递归/嵌套结构** | 结构示意图（方案A） | 将抽象的层级关系可视化 |
| 文章描述**流程/步骤/决策链** | 流程图（方案A） | 帮助读者跟随逻辑推进 |
| 文章涉及**多个维度对比** | 对比图/矩阵图（方案A） | 表格不够直观时用图 |
| 核心概念需要**直观理解** | 概念示意图（方案A） | 用图形帮助读者建立直觉 |
| 文章有**前后对比/演变** | 前后对比图（方案A） | 展示变化结果 |
| 文章描述**变化过程/状态转换** | 动态过程图（方案B） | 必须通过动画展示 |
| 文章涉及**运动/流动/生长** | 动态过程图（方案B） | 运动轨迹、数据流动 |
| 需要**写实照片风格** | AI 生图（方案C） | 无法用几何图形表达 |

---

## 不需要配图的场景

- 纯观点/评论类内容（配图反而分散注意力）
- 已有表格清晰展示数据
- 短文（< 1000字），图片会打断阅读节奏
- 概念本身足够简单，文字已能清晰传达

---

## 配图数量原则

- **图文并茂是硬要求**：文章必须包含配图，纯文字文章体验差
- **3-5张静图 + 0-2个动图为宜**
- **GIF 是稀缺资源**：每篇文章最多1-2个GIF，放在最核心的"变化过程"处
- **封面不算在内**：封面是独立的，配图指正文中的插图
- **论文风格版优先配图**：对话版一般不配图（保持对话节奏）
- **长文必须多配**：超过3000字的文章，每增加1000字至少多配1张。7000-8000字的长文应有5张以上配图
- **图文比例协调**：图片间距均匀，不要集中在一个章节

---

## 配图位置规则（重要）

- **每个章节开头放一张配图**：文章的每个主要章节（## H2 级别）开头都应放置一张与该章节内容相关的配图，图片紧跟在章节标题之后、正文文字之前
- **长章节灵活添加**：如果某个章节文字超过1500字，除了章节开头的配图外，可在章节中间适当位置再添加1张配图
- **配图与内容协调**：每张配图必须与所在章节的内容直接相关

---

## 方案A：SVG 直出 → PNG（首选）

### ⚠️ 微信图片要点

1. SVG 不能直接在微信文章中显示（微信仅支持 JPG/PNG/GIF）
2. 本地路径图片不能直接显示，必须上传到微信 CDN
3. **SVG→PNG 转换优先用 Playwright 渲染**——cairosvg 无法正确渲染中文字体
4. `wechat-pub publish` 内置的 cairosvg 转换仅适用于纯英文/数字的 SVG

### SVG 通用模板

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {height}" width="800" height="{height}">
  <rect width="800" height="{height}" fill="#FAF7F2" rx="12"/>
  <style>
    .title   { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; font-size: 22px; font-weight: bold; fill: #3C2415; text-anchor: middle; }
    .sub     { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; font-size: 14px; fill: #666; text-anchor: middle; }
    .box-title { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; font-size: 18px; font-weight: bold; fill: #fff; text-anchor: middle; }
    .box-desc  { font-family: 'PingFang SC','Microsoft YaHei',sans-serif; font-size: 14px; fill: rgba(255,255,255,0.9); text-anchor: middle; }
  </style>
  <text x="400" y="40" class="title">{图标题}</text>
</svg>
```

### SVG 配色规范

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 背景 | `#FAF7F2` | 奶油白，全图背景 |
| 一级底色（主色） | `#C96442` | 赭石橙，主层级/主要步骤 |
| 二级底色（深色） | `#8B5E3C` | 深棕，次级层级/步骤 |
| 三级底色（最深） | `#3C2415` | 最深色，最高级/汇总 |
| 上涨阳线 | `#A3D4A0` | K线图中上涨 |
| 下跌阴线 | `#E8836B` | K线图中下跌 |
| 文字（主） | `#3C2415` | 标题文字 |
| 文字（次） | `#666` | 正文说明文字 |

### SVG→PNG 转换脚本

```python
import os, glob, re, base64

svgs = sorted(glob.glob('0*.svg'))

try:
    from playwright.sync_api import sync_playwright
    print("Using Playwright for SVG→PNG conversion...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for svg_file in svgs:
            png_file = svg_file.replace('.svg', '.png')
            with open(svg_file, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            m = re.search(r'width="(\d+)".*?height="(\d+)"', svg_content)
            w, h = int(m.group(1)), int(m.group(2))
            page = browser.new_page(viewport={'width': w, 'height': h}, device_scale_factor=2)
            svg_b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            page.goto(f'data:image/svg+xml;base64,{svg_b64}', timeout=60000)
            page.wait_for_timeout(500)
            page.screenshot(path=png_file, timeout=60000)
            page.close()
        browser.close()
except ImportError:
    import cairosvg
    print("WARNING: Playwright not available, falling back to cairosvg...")
    for svg_file in svgs:
        png_file = svg_file.replace('.svg', '.png')
        cairosvg.svg2png(url=svg_file, write_to=png_file, scale=3)
```

---

## 方案B：Canvas 动画录制为 GIF（动态过程必选）

### ⚠️ 微信公众号动态内容限制

微信不支持 JavaScript（Canvas 无法运行）、不支持 `<video>` 自动播放、不支持 SVG 动画。**GIF 动图是公众号中展示动态内容的唯一方式。**

### 触发条件（必须同时满足）

1. 文章内容描述了一个**变化过程**
2. 静态图**无法完整表达**该过程的语义

### GIF 参数约束

| 参数 | 推荐值 | 最大值 | 说明 |
|------|--------|--------|------|
| 时长 | 3-6秒 | 8秒 | 越短越好 |
| 帧率 | 8-10 fps | 15 fps | 公众号场景不需要高帧率 |
| 宽度 | 400-600px | 600px | 手机屏幕宽度有限 |
| 颜色 | 128色 | 256色 | 减少文件体积 |
| 文件大小 | ≤1MB | 2MB | 超大GIF加载慢 |
| 每篇数量 | 0-1个 | 2个 | GIF是稀缺资源 |

### Canvas 动画 HTML 模板

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body { margin: 0; background: #FAF7F2; display: flex; justify-content: center; align-items: center; height: 100vh; }
  canvas { display: block; }
</style>
</head>
<body>
<canvas id="canvas" width="600" height="400"></canvas>
<script>
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
function animate() {
  // ... 绘制逻辑
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
```

### 录制命令

```bash
wechat-pub record-gif animation.html -o output/images/demo.gif
wechat-pub record-gif animation.html --fps 8 --duration 6 --width 500 -o output/images/demo.gif
wechat-pub record-gif animation.html --selector "#my-canvas" --scale 2.0 -o output/images/demo.gif
wechat-pub record-gif animation.html --json
```

### Canvas 动画设计规范

| 规范 | 说明 |
|------|------|
| **自动播放** | 动画必须在页面加载后自动开始 |
| **循环播放** | 设置 `loop=0`（无限循环） |
| **配色一致** | 使用 claude-warm 主题配色 |
| **文字标注** | 关键状态/步骤用文字标注在 Canvas 上 |
| **简洁聚焦** | 一个 GIF 只展示一个变化过程 |
| **首帧有意义** | GIF 第一帧就应该是有意义的状态 |

---

## 方案C：image_gen AI 生图（最后备选）

当内容需要写实风格的图时，使用 image_gen 工具直接生成 PNG 格式图片。大多数场景应优先使用方案A或方案B。

### prompt 编写规范

**好的 prompt**（具体、可执行）：
```
"一张缠论级别递归结构示意图：底部是5根K线重叠构成一笔，3笔构成线段，
3段线段重叠构成中枢，箭头从下往上连接各层级，标注'K线→笔→线段→中枢'，
每个层级用不同颜色区分（赭石橙/深棕/暖灰），背景为奶白色，风格简洁现代"
```

**prompt 核心要素**：图类型、核心要素、布局、配色（claude-warm: 赭石橙+奶油白）、风格（简洁现代）
