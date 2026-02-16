#!/usr/bin/env python3
"""Reddit需求分析器"""

import sqlite3
import re
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DB_PATH = '/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/data/reddit_posts.db'
OUTPUT_DIR = Path('/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/reports')

# 痛点关键词
PAIN_KEYWORDS = [
    'wish there was', 'wish I had', 'need an app', 'looking for',
    'missing feature', 'frustrated', 'annoying', 'too complicated',
    'hate using', "can't find", "doesn't exist", 'too slow',
    'wish app', 'need tool', 'anyone know', 'too expensive',
    'waste of time', 'broken', "doesn't work", 'manual work',
    'repetitive', 'automate', 'offline', 'no ads', 'dark mode'
]

# 需求类别关键词
NEED_CATEGORIES = {
    'productivity': ['task', 'todo', 'habit', 'schedule', 'calendar', 'reminder', 'focus', 'time', 'project', 'organize'],
    'finance': ['budget', 'expense', 'track', 'invest', 'portfolio', 'save', 'money', 'tax', 'bill', 'split'],
    'health': ['workout', 'exercise', 'sleep', 'diet', 'weight', 'run', 'pace', 'calorie', 'water', 'fitness'],
    'travel': ['flight', 'hotel', 'trip', 'itinerary', 'currency', 'translate', 'booking', 'map', 'packing'],
    'learning': ['note', 'learn', 'study', 'flashcard', 'book', 'course', 'knowledge', 'journal'],
    'utilities': ['simple', 'clean', 'minimal', 'fast', 'offline', 'widget', 'shortcut', 'quick']
}

def load_data():
    """加载数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM posts")
    posts = [dict(row) for row in c.fetchall()]
    conn.close()
    return posts

def detect_pain_points(text):
    """检测痛点"""
    text_lower = text.lower()
    return [kw for kw in PAIN_KEYWORDS if kw in text_lower]

def categorize_needs(text):
    """分类需求"""
    text_lower = text.lower()
    found = []
    for category, keywords in NEED_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            found.append(category)
    return found if found else ['other']

def analyze(posts):
    """分析帖子"""
    pain_posts = []
    keyword_counter = Counter()
    category_counts = defaultdict(list)
    
    for post in posts:
        text = f"{post['title']} {post.get('selftext', '')}"
        
        # 痛点检测
        pains = detect_pains = detect_pain_points(text)
        if detect_pain_points:
            pain_posts.append({
                'id': post['id'],
                'subreddit': post['subreddit'],
                'title': post['title'],
                'score': post['score'],
                'pains': pains,
                'categories': categorize_needs(text)
            })
        
        # 类别统计
        for cat in categorize_needs(text):
            category_counts[cat].append(post)
        
        # 关键词提取
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        stop_words = {'this', 'that', 'with', 'have', 'from', 'they', 'would', 'there', 'what', 'when', 'make', 'just', 'over', 'some', 'could'}
        words = [w for w in words if w not in stop_words]
        keyword_counter.update(words)
    
    return {
        'total': len(posts),
        'pain_posts': pain_posts,
        'pain_count': len(pain_posts),
        'keywords': keyword_counter.most_common(30),
        'categories': dict(category_counts)
    }

def generate_report(analysis):
    """生成报告"""
    report = []
    report.append("# Reddit需求分析报告\n")
    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    report.append(f"**数据统计**: {analysis['total']} 条帖子，{analysis['pain_count']} 条痛点帖子\n\n")
    
    report.append("## 🔥 Top 20 关键词\n\n")
    for i, (word, count) in enumerate(analysis['keywords'][:20], 1):
        report.append(f"{i}. **{word}** - {count} 次\n")
    
    report.append("\n## 📊 需求类别分布\n\n")
    sorted_cats = sorted(analysis['categories'].items(), key=lambda x: len(x[1]), reverse=True)
    for cat, posts in sorted_cats:
        report.append(f"- **{cat.title()}**: {len(posts)} 条\n")
    
    report.append("\n## 💡 Top 15 痛点需求\n\n")
    sorted_pain = sorted(analysis['pain_posts'], key=lambda x: x['score'], reverse=True)[:15]
    for post in sorted_pain:
        report.append(f"### [{post['title']}](https://reddit.com/{post['id']})\n")
        report.append(f"- Sub: r/{post['subreddit']} | Score: {post['score']}\n")
        report.append(f"- 痛点: {', '.join(post['pains'][:3])}\n")
        report.append(f"- 类别: {', '.join(post['categories'])}\n\n")
    
    return ''.join(report)

def main():
    print("=" * 60)
    print("Reddit需求分析器 v2")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n📊 加载数据...")
    posts = load_data()
    print(f"   帖子数: {len(posts)}")
    
    print("\n🔍 分析中...")
    analysis = analyze(posts)
    
    print("\n📝 生成报告...")
    report = generate_report(analysis)
    
    # 保存报告
    report_path = OUTPUT_DIR / 'needs_analysis_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    
    # 保存JSON
    json_path = OUTPUT_DIR / 'analysis_results.json'
    with open(json_path, 'w') as f:
        json.dump({
            'total_posts': analysis['total'],
            'pain_point_posts': analysis['pain_count'],
            'top_keywords': analysis['keywords'][:20],
            'category_counts': {k: len(v) for k, v in analysis['categories'].items()}
        }, f, indent=2)
    
    print(f"\n✅ 完成!")
    print(f"📁 报告: {report_path}")
    print(f"📁 数据: {json_path}")

if __name__ == '__main__':
    main()
