---
title: 快速开始
order: 1
date: '2026-03-28'
icon: 🚀
---

# 快速开始

欢迎使用技术文档站点。本站基于 Next.js 构建，支持完整 Markdown 渲染和 Mermaid 图表。

## 功能特性

- [x] 完整 GFM Markdown 支持
- [x] Mermaid 图表渲染
- [x] 代码语法高亮
- [x] 分屏对比查看
- [x] 用户标签归类
- [x] 文本批注功能
- [ ] 全文搜索（规划中）

## 添加文档

在 `docs/` 目录下创建 `.md` 文件，支持 front-matter：

```yaml
---
title: 文档标题
order: 1
---
```

> **提示**：`order` 数字越小，在侧边栏中排序越靠前。

## 代码示例

```python
class DataCollector:
    """数据采集器"""
    def __init__(self, config: dict):
        self.config = config
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            data = await self.collect()
            await self.process(data)
```

```json
{
  "name": "tech-docs",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build"
  }
}
```

## 表格示例

| 功能 | 状态 | 说明 |
|------|:----:|------|
| Markdown 渲染 | ✅ | 支持 GFM 扩展 |
| Mermaid 图表 | ✅ | 架构图、流程图、时序图 |
| 代码高亮 | ✅ | 自动语言检测 |
| ~~旧版渲染器~~ | ❌ | 已替换为 rehype |

## 批注功能

选中页面上的任意文本，会弹出批注按钮，点击后可以添加笔记。
