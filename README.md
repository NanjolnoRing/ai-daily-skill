# AI Daily

> 自动化 AI 资讯日报生成器 - 每天自动获取、分析、归类 AI 前沿资讯，生成精美的可访问网页

---

## 简介

AI Daily 是一个自动化工具，帮助 AI 从业者每天快速获取行业最新动态。它从 [smol.ai](https://news.smol.ai/) 获取资讯，使用 Claude AI 进行智能分析和分类，生成结构化的日报网页，并通过邮件通知你更新结果。

### 解决的问题

- **信息过载**：AI 领域发展太快，每天有大量资讯，难以筛选重点
- **时间成本**：手动收集、阅读、整理资讯耗时耗力
- **信息分散**：资讯散落在各个平台，缺乏统一的汇总入口

### 核心价值

- 每天自动获取前一天的重要 AI 资讯
- AI 自动提取核心摘要，无需阅读全文
- 按主题智能分类（模型发布、产品动态、研究论文等）
- 精美的网页界面，支持移动端阅读
- 邮件通知，无需主动查看

---

## 快速开始

### 前置要求

你只需要：
- 一个 GitHub 账号
- 一个智谱 AI API Key（用于调用 Claude）
- 一个邮箱（用于接收通知）

### 三步即可使用

**第一步：复制仓库**

点击右上角的 "Fork" 按钮，将仓库复制到你的账号下。

**第二步：配置密钥**

在仓库页面进入 `Settings` -> `Secrets and variables` -> `Actions`，点击 `New repository secret` 添加以下配置：

| Secret 名称 | 填写内容 | 获取方式 |
|-------------|----------|----------|
| `ZHIPU_API_KEY` | 你的智谱 API Key | [智谱AI开放平台](https://open.bigmodel.cn/) |
| `ANTHROPIC_BASE_URL` | `https://open.bigmodel.cn/api/anthropic` | 固定值 |
| `SMTP_HOST` | `smtp.gmail.com`（或其他邮箱服务器） | 见下方邮箱配置说明 |
| `SMTP_PORT` | `587`（或其他端口） | 见下方邮箱配置说明 |
| `SMTP_USER` | 你的邮箱地址 | |
| `SMTP_PASSWORD` | 邮箱授权码（非登录密码） | 见下方邮箱配置说明 |
| `NOTIFICATION_TO` | 接收通知的邮箱地址 | |

**第三步：启用 GitHub Pages**

1. 进入仓库 `Settings` -> `Pages`
2. 在 "Source" 下拉菜单中选择 `GitHub Actions`
3. 点击 Save

完成！系统会在每天北京时间上午 10 点自动运行，生成日报并发送邮件通知。

---

## 常见问题

### 关于配置

**Q: 智谱 API Key 如何获取？**

A: 访问 [智谱AI开放平台](https://open.bigmodel.cn/)，注册账号后在控制台获取 API Key。

**Q: 如何配置邮箱通知？**

A: 不同邮箱的配置方式如下：

| 邮箱服务商 | SMTP 服务器 | 端口 | 获取授权码方式 |
|------------|-------------|------|----------------|
| Gmail | smtp.gmail.com | 587 | 账号设置 -> 安全 -> 两步验证 -> 应用专用密码 |
| QQ 邮箱 | smtp.qq.com | 587 | 设置 -> 账户 -> POP3/SMTP 服务 -> 生成授权码 |
| 163 邮箱 | smtp.163.com | 465 | 设置 -> POP3/SMTP/IMAP -> 开启服务 |
| Outlook | smtp.office365.com | 587 | 使用常规登录密码 |

**Q: 我不想配置邮箱通知，可以跳过吗？**

A: 可以。不配置邮箱相关的 Secrets 会导致程序报错，但日报仍会正常生成。你可以修改代码跳过邮件发送。

**Q: GitHub Pages 是什么？**

A: GitHub 提供的免费静态网站托管服务。启用后，你的日报会通过 `https://你的用户名.github.io/ai-daily-skill/` 公开访问。

### 关于使用

**Q: 每天什么时候生成日报？**

A: 北京时间每天上午 10 点（UTC 时间 02:00）自动运行。

**Q: 为什么获取的是前两天的资讯？**

A: 考虑到资讯源更新时间和时区差异，获取前两天的内容更加可靠。例如：1 月 15 日运行时，会获取 1 月 13 日的资讯。

**Q: 可以手动触发运行吗？**

A: 可以。进入仓库的 `Actions` 标签页，选择 "AI Daily News Generator"，点击 "Run workflow" 按钮即可手动运行。

**Q: 如果某天没有资讯会怎样？**

A: 系统会生成一个空页面，并发送邮件通知你当日无数据。

### 关于二次开发

**Q: 如何在本地运行？**

A: 安装 Python 3.11+，然后执行：

```bash
pip install -r requirements.txt
export ZHIPU_API_KEY="你的API密钥"
python src/main.py
```

生成的文件在 `docs/` 目录下。

**Q: 如何更换资讯源？**

A: 修改 `src/config.py` 中的 `RSS_URL` 配置，或设置 `RSS_URL` 环境变量。RSS 源需要包含标准的 `<item>`、`<title>`、`<content:encoded>` 等标签。

**Q: 如何修改主题颜色？**

A: 编辑 `src/config.py` 中的 `THEMES` 字典，修改对应的颜色值。

**Q: 如何修改邮件通知模板？**

A: 编辑 `src/notifier.py` 中的邮件 HTML 模板。

**Q: 可以添加多个资讯源吗？**

A: 可以。需要修改 `src/rss_fetcher.py`，支持多个 RSS URL 的合并处理。

---

## 功能说明

### 资讯分类

系统将资讯自动分为以下 6 类：

| 分类 | 图标 | 说明 |
|------|------|------|
| 模型发布 | Robot | 新模型、版本更新、架构突破 |
| 产品动态 | Briefcase | 新产品、功能、企业动态 |
| 研究论文 | Book | 学术研究、技术突破、论文 |
| 工具框架 | Wrench | 开发工具、开源项目、SDK |
| 融资并购 | Money | 投资、收购、IPO |
| 行业事件 | Trophy | 奖项、争议、政策、监管 |

### 智能主题

系统根据内容类型自动选择 8 种主题之一：

| 主题 | 适用场景 |
|------|----------|
| 柔和蓝色 | 模型、框架、开发工具类内容 |
| 深靛蓝 | 企业动态、产品发布 |
| 冷色青绿 | 融资、并购、金融 |
| 优雅紫色 | 创意、AIGC、设计 |
| 清新绿色 | 医疗、健康 AI |
| 温暖橙色 | 热点、争议话题 |
| 中性灰色 | 研究、论文、数据 |
| 玫瑰粉色 | 应用、生活、消费 |

---

## 项目结构

```
ai-daily-skill/
├── .github/workflows/
│   └── daily.yml           # GitHub Actions 定时任务配置
├── src/
│   ├── config.py           # 配置：主题、分类、API 设置
│   ├── rss_fetcher.py      # RSS 下载与解析
│   ├── claude_analyzer.py  # Claude AI 分析调用
│   ├── html_generator.py   # HTML 页面生成
│   ├── notifier.py         # 邮件通知
│   └── main.py             # 主入口
├── docs/                   # 输出目录（GitHub Pages 发布）
│   ├── index.html          # 索引页
│   ├── 2026-01-13.html     # 日报页面
│   └── css/styles.css      # 样式文件
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量示例
└── README.md
```

---

## 技术架构

```
GitHub Actions (定时触发)
    ↓
下载 RSS XML
    ↓
解析并提取目标日期内容
    ↓
调用 Claude API 分析分类
    ↓
生成 HTML 页面
    ↓
发送邮件通知
    ↓
部署到 GitHub Pages
```

---

## 本地开发

### 环境要求

- Python 3.11 或更高版本
- pip 包管理器

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourname/ai-daily-skill.git
cd ai-daily-skill
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

4. 运行
```bash
python src/main.py
```

### 测试

运行后检查 `docs/` 目录，应该会生成 `index.html` 和对应日期的 HTML 文件。

---

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 贡献

欢迎提交 Issue 和 Pull Request。在提交 PR 前，请确保：

1. 代码通过本地测试
2. 添加必要的注释
3. 遵循现有的代码风格

---

## 更新日志

### v1.0.0 (2026-01-15)

- 初始版本发布
- 支持 smol.ai RSS 源
- 8 种智能主题
- Claude AI 分析
- 邮件通知
- GitHub Actions 自动部署
