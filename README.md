# WeChat Article Extractor

一个用于提取微信公众号（`mp.weixin.qq.com`）公开文章正文的工具，包含可独立运行的 Python 脚本，以及可被 Codex 直接识别的技能文件。

它会读取文章的标题、作者、发布时间（如有）和正文，并按你的问题提取重点、总结或整理成笔记。

## 它能做什么

- 提取微信公众号文章的可读正文和基础元数据
- 输出纯文本、Markdown 或 JSON
- 按需求总结、结构化、对比文章观点或提炼待办
- 过滤常见的公众号页尾杂项；不登录、不下载图片

## AI Agent 支持

任何能够运行 Python 脚本或调用本地命令的 AI Agent，都可以复用它来读取公众号文章、取得结构化结果，再按自己的工作流进行总结或分析。

项目中的 `SKILL.md` 和 `agents/openai.yaml` 是 Codex 的技能配置；其他 Agent 可以直接使用同一个脚本，并把其中的提取与分析原则适配到各自的技能或提示词格式中。

## 使用方式

### 作为 Codex 技能安装

将整个项目文件夹复制或克隆到你的 Codex 技能目录：

```text
~/.codex/skills/wechat-article-extractor/
```

在 Codex 中直接发送公众号文章链接，并提出“提取”“总结”“整理成笔记”等需求即可；也可以明确写：

```text
$wechat-article-extractor 帮我提取这篇公众号文章，并总结重点
```

### 单独运行脚本

仅需 Python 3 标准库，无需安装第三方依赖：

```bash
python scripts/extract_wechat_article.py "https://mp.weixin.qq.com/s/文章标识" --format markdown
```

可选格式为 `text`、`markdown` 和 `json`。如需保存到文件，可添加 `--output article.md`。

## 限制

- 只处理 `mp.weixin.qq.com` 的公开文章链接。
- 遇到验证码、登录墙或无法取得正文时，脚本会停止并报告原因，不会尝试绕过。
- 文章中的内容可能会过期；需要据此作决定时，请另行核实来源。

## 项目结构

```text
wechat-article-extractor/
├── SKILL.md                         # Codex 的技能说明
├── agents/openai.yaml               # 技能显示信息与调用设置
└── scripts/extract_wechat_article.py # 正文提取脚本
```

## 许可

MIT License。
