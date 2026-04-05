---
description: MotherDuck 风格前端 UI — 色彩、排版、组件、布局与动效
globs: '**/*.{tsx,ts,jsx,js,css,scss,vue,html}'
alwaysApply: false
---

# MotherDuck 风格前端设计规则

在实现或修改本项目的营销页、落地页、文档页与产品壳层 UI 时，遵循以下规范；产品内密集数据界面在保持层级清晰的前提下可略微收敛黄色用量。

## 1. 品牌色彩（必须使用 CSS 变量或等价 token）

| Token                   | HEX                   | 用途                                |
| ----------------------- | --------------------- | ----------------------------------- |
| primary / DuckDB Yellow | `#FFF100`             | 主品牌、大面积背景、主 CTA、高亮块  |
| black                   | `#0D0D0D`             | 主文字、深色区、描边、硬阴影色      |
| purple                  | `#7D66FF`             | 区块区分、图表强调、focus ring 紫系 |
| orange                  | `#FF6900`             | 警告、次要 CTA、字符串高亮感        |
| blue                    | `#2EAFFF`             | 链接、信息、函数高亮感              |
| green                   | `#00C770`             | 成功                                |
| bg light                | `#FFFFFF` / `#FAFAFA` | 主背景                              |
| bg dark / code          | `#1E1E1E`             | 代码块、深色内容区                  |
| text primary            | `#0D0D0D`             | 标题与正文主色                      |
| text secondary          | `#626262`             | 辅助说明                            |
| border                  | `#E5E5E5` / `#D4D4D4` | 分割线、输入框默认边框              |

正文大段文字可用 `rgba(13, 13, 13, 0.85)` 替代纯黑，减轻疲劳。

## 2. 字体

- **标题**：粗体无衬线（Inter / Geist / Space Grotesk），`700–800`。
- **正文**：系统无衬线栈：`-apple-system, BlinkMacSystemFont, "Segoe UI", …`。
- **代码**：`JetBrains Mono`、`Fira Code`、`SF Mono`，`13–14px`，行高约 `1.5`。

字号层级：Hero `48–64px` / H1 `36–40px` / H2 `24–28px` / Body large `18px` / Body `16px` / Caption `14px`。

## 3. 间距与布局

- 基础单位 **4px**；常用：`8 / 16 / 24 / 32 / 48 / 64 / 96`。
- 内容容器 **max-width 1200px**（宽屏可到 **1400px**）。
- 水平边距：移动 `16px`、平板 `24px`、桌面 `48px`。
- 区块上下间距优先 **64–96px**；12 列网格、列间隙 **24px**。

## 4. 组件约定

**主按钮（黄）**：背景 `#FFF100`，文字 `#0D0D0D`，`border: 2px solid #0D0D0D`，`border-radius: 8px`，`padding: 12px 24px`，`font-weight: 600`，**硬阴影** `4px 4px 0 #0D0D0D`。`hover`：`translate(2px, 2px)`，阴影改为 `2px 2px 0`。

**次按钮**：透明底、黑字、`2px` 黑边框，无偏移阴影。

**卡片**：白底或黄底强调；圆角 `12–16px`（大卡片可到 `24px`）；可选 `2px solid #0D0D0D`；轻量偏移阴影如 `4px 4px 0 rgba(13,13,13,0.1)`；内边距 `24px` 或 `32px`。

**输入框**：白底、`2px solid #D4D4D4`、`radius 8px`、`padding 12px 16px`。`:focus` 边框 `#7D66FF`，`outline: none`，`box-shadow: 0 0 0 3px rgba(125,102,255,0.2)`。

**代码块**：深背景 `#1E1E1E` 或 `#0D0D0D`，圆角 `8–12px`，内边距 `16–24px`；语法高亮意象：黄关键字、蓝函数、橙字符串、紫变量。

## 5. 插画与图标

- 插画：**手绘卡通**、粗黑描边、扁平色块、少渐变；品牌色点缀；鸭子/角色可白身黄喙等与 MotherDuck 一致的气质。
- 图标：**线性**、`2–3px` 描边、圆角端点；可带铁路图式几何；尺寸 `20 / 24 / 32px`。
- 装饰：手绘星星、波浪、点阵；黄底涂鸦感标签/徽章。

## 6. 布局模式

- **顶栏**：固定高度约 `64–72px`；透明或白底，滚动后可加底边框；左 Logo（约 `32px` 高），右区 CTA 用主按钮。
- **Hero**：高 `~80vh` 或 `≥600px`；大面积 `#FFF100` 与白色可斜切或波浪分割；左文右图或上下堆叠；标题黑字大字号，可用 `<mark>` 式黄底黑字高亮。
- **三栏产品壳**（若适用）：左 `280px` 导航/浏览器 `#FAFAFA`，中栏弹性编辑器白底，右 `320px` 预览；小屏改为单栏堆叠。

页面区块可 **白 / 黄** 交替，黄块上保持黑字、高对比。

## 7. 动效

- 按钮：硬阴影 + 位移的「按压」感（见上）。
- 链接：下划线展开或黄底高亮 hover。
- 卡片：`translateY(-4px)` + 略加深阴影（保持克制）。
- 全局：`scroll-behavior: smooth`；区块入场可用 `translateY(20px)→0` + opacity，`300–400ms`，`cubic-bezier(0.4, 0, 0.2, 1)`。

## 8. 响应式

- `<640`：单列，Hero 标题缩至 `32–40px`，黄块全宽出血，导航改汉堡。
- `640–1024`：两列网格，字号略减。
- `≥1024`：完整布局；`≥1440` 用更大 max-width 与间距。

## 9. 设计原则（决策时自检）

1. **黄 × 黑** 高对比是品牌核心。
2. **友好技术感**：插画软化「纯工具感」。
3. **结构化**：铁路图式线条/节点可传达数据流。
4. **手绘人情味**：避免过度光滑的「通用 SaaS 玻璃拟态」。
5. **产品区功能优先**：层级清晰、可读性先于装饰。

## 10. 推荐实现与 `:root` 参考

技术选型可与栈一致：**React/Next**，样式可用 **Tailwind** 映射 token；动画可用 **CSS** 或 **Framer Motion**。

```css
:root {
  --color-primary: #fff100;
  --color-black: #0d0d0d;
  --color-purple: #7d66ff;
  --color-orange: #ff6900;
  --color-blue: #2eafff;
  --color-green: #00c770;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-offset: 4px 4px 0px;
  --shadow-color: #0d0d0d;
}
```

新增 UI 时优先复用上述 token 与组件形态，避免引入与品牌冲突的霓虹渐变、细线玻璃拟态主按钮或与硬阴影体系冲突的弥散大阴影主 CTA。
