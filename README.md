# Reddit Needs Discovery

从Reddit发现真实用户需求的数据采集与分析项目。

## 项目目标

1. 采集14个Subreddits的帖子和评论
2. 使用NLP分析识别用户痛点和需求
3. 输出可开发为简单App的需求列表

## Subreddits

- 开发: iOSProgramming, productivity
- 理财: investing, FIREUK, UKPersonalFinance
- 学习: Notion, bulletjournal
- 健康: running, fitness
- 旅行: travelhacks, Flights
- 实用: IWantToBuy, lifehacks, legaladviceUK

## 使用方法

```bash
# 采集数据
python scripts/crawl_reddit_v2.py

# 分析需求
python scripts/analyze_v2.py

# 查看报告
cat reports/needs_analysis_report.md
```

## 输出

- `data/reddit_posts.db` - SQLite数据库
- `reports/needs_analysis_report.md` - 需求分析报告
- `reports/analysis_results.json` - 统计摘要

## 技术栈

- Python 3
- SQLite
- PRAW / Pushshift API
- NLP关键词分析

## 许可证

MIT
