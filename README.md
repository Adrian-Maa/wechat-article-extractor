# WeChat Article Extractor

一个用于提取微信公众号（`mp.weixin.qq.com`）公开文章正文的 Codex 技能。

它会读取文章的标题、作者、发布时间（如有）和正文，并按你的问题提取重点、总结或整理成笔记。遇到旅行攻略中的签证、入境卡、票价、营业时间等会变化的信息，技能会要求另外核实官方来源。

## 它能做什么

- 提取微信公众号文章的可读正文和基础元数据
- 输出纯文本、Markdown 或 JSON
- 按需求总结、结构化、对比文章观点或提炼待办
- 对旅行攻略，可协助与自己的行程、预算和日期进行对比
- 过滤常见的公众号页尾杂项；不登录、不下载图片

## 使用方式

### 作为 Codex 技能安装

将整个项目文件夹复制或克隆到你的 Codex 技能目录：

```text
~/.codex/skills/wechat-article-extractor/
```

在 Codex 中直接发送公众号攻略链接并提出“提取”“总结”“对比我的行程”等需求即可；也可以明确写：

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
- 文章中的价格、时间、入境规则等可能已过期；请以官方当前信息为准。

## 项目结构

```text
wechat-article-extractor/
├── SKILL.md                         # Codex 的技能说明
├── agents/openai.yaml               # 技能显示信息与调用设置
└── scripts/extract_wechat_article.py # 正文提取脚本
```

## 许可

MIT License。
