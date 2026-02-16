#!/usr/bin/env python3
"""
Reddit Data Analyzer for Needs Discovery
分析帖子内容，识别用户需求
"""

import sqlite3
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import pandas as pd

# 配置
DB_PATH = Path('/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/data/reddit_posts.db')
OUTPUT_DIR = Path('/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/reports')

# 痛点关键词（英文）
PAIN_POINT_KEYWORDS = [
    'wish there was', 'wish I had', 'need an app', 'looking for a tool',
    'missing feature', 'frustrated with', 'annoying with', 'too complicated',
    'hate using', 'can\'t find', 'doesn\'t exist', 'too slow',
    'wish app', 'need tool', 'anyone know', 'how to',
    'too expensive', 'waste of time', 'broken', 'doesn\'t work',
    'simple tool', 'clean app', 'minimal', 'offline', 'no ads',
    'dark mode', 'sync issue', 'data loss', 'slow sync',
    'manual work', 'repetitive task', 'automate this'
]

# 需求类别关键词
NEED_CATEGORIES = {
    'productivity': ['task', 'todo', 'schedule', 'calendar', 'reminder', 'focus', 'time track', 'habit', 'goal', 'project'],
    'finance': ['budget', 'expense', 'track', 'invest', 'portfolio', 'save', 'money', 'spending', 'bank', 'tax'],
    'health': ['workout', 'exercise', 'sleep', 'diet', 'weight', 'run', 'pace', 'distance', 'calorie', 'water'],
    'learning': ['note', 'learn', 'study', 'flashcard', 'memory', 'review', 'book', 'course', 'knowledge'],
    'travel': ['flight', 'hotel', 'trip', 'itinerary', 'currency', 'translate', 'map', 'booking'],
    'social': ['share', 'collaborate', 'team', 'family', 'friend', 'group']
}

def load_data():
    """加载数据"""
    conn = sqlite3.connect(DB_PATH)
    
    # 加载帖子
    posts_df = pd.read_sql_query('SELECT * FROM posts', conn)
    
    # 加载评论
    comments_df = pd.read_sql_query('SELECT * FROM comments', conn)
    
    conn.close()
    
    return posts_df, comments_df

def detect_pain_points(text):
    """检测痛点"""
    text_lower = text.lower()
    pain_points = []
    
    for keyword in PAIN_POINT_KEYWORDS:
        if keyword in text_lower:
            pain_points.append(keyword)
    
    return pain_points

def categorize_needs(text):
    """分类需求"""
    text_lower = text.lower()
    categories = []
    
    for category, keywords in NEED_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                categories.append(category)
                break
    
    return categories if categories else ['other']

def analyze_posts(posts_df):
    """分析帖子"""
    results = {
        'total_posts': len(posts_df),
        'pain_point_posts': [],
        'needs_by_category': defaultdict(list),
        'top_keywords': [],
        'subreddit_stats': {}
    }
    
    keyword_counter = Counter()
    pain_count = 0
    
    for _, row in posts_df.iterrows():
        text = f"{row['title']} {row['selftext']}"
        
        # 检测痛点
        pain_points = detect_pain_points(text)
        if pain_points:
            pain_count += 1
            results['pain_point_posts'].append({
                'id': row['id'],
                'subreddit': row['subreddit'],
                'title': row['title'],
                'score': row['score'],
                'pain_points': pain_points,
                'categories': categorize_needs(text)
            })
        
        # 分类需求
        categories = categorize_needs(text)
        for cat in categories:
            results['needs_by_category'][cat].append({
                'id': row['id'],
                'title': row['title'],
                'score': row['score']
            })
        
        # 提取关键词
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        stop_words = {'this', 'that', 'with', 'have', 'from', 'they', 'would', 
                      'there', 'what', 'when', 'make', 'just', 'over', 'such',
                      'into', 'than', 'them', 'some', 'could', 'other', 'more'}
        words = [w for w in words if w not in stop_words]
        keyword_counter.update(words)
    
    results['top_keywords'] = keyword_counter.most_common(50)
    results['pain_point_count'] = pain_count
    
    # 统计每个subreddit
    for subreddit in posts_df['subreddit'].unique():
        sub_posts = posts_df[posts_df['subreddit'] == subreddit]
        results['subreddit_stats'][subreddit] = {
            'total': len(sub_posts),
            'avg_score': sub_posts['score'].mean(),
            'avg_comments': sub_posts['num_comments'].mean()
        }
    
    return results

def analyze_comments(comments_df):
    """分析评论"""
    results = {
        'total_comments': len(comments_df),
        'pain_point_comments': [],
        'top_words': []
    }
    
    keyword_counter = Counter()
    
    for _, row in comments_df.iterrows():
        if row['body']:
            pain_points = detect_pain_points(row['body'])
            if pain_points:
                results['pain_point_comments'].append({
                    'id': row['id'],
                    'post_id': row['post_id'],
                    'body': row['body'][:500],
                    'score': row['score'],
                    'pain_points': pain_points
                })
            
            words = re.findall(r'\b[a-z]{4,}\b', row['body'].lower())
            stop_words = {'this', 'that', 'with', 'have', 'from', 'they', 'would'}
            words = [w for w in words if w not in stop_words]
            keyword_counter.update(words)
    
    results['top_words'] = keyword_counter.most_common(30)
    
    return results

def generate_needs_report(posts_analysis, comments_analysis, posts_df):
    """生成需求报告"""
    report = []
    report.append("# Reddit需求分析报告\n")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report.append(f"数据来源: Reddit 14个Subreddits\n")
    report.append(f"分析帖子数: {posts_analysis['total_posts']}\n")
    report.append(f"痛点帖子数: {posts_analysis['pain_point_count']}\n")
    report.append(f"分析评论数: {comments_analysis['total_comments']}\n")
    
    report.append("\n## 📊 数据概览\n")
    report.append("| Subreddit | 帖子数 | 平均得分 | 平均评论数 |\n")
    report.append("|-----------|--------|----------|------------|\n")
    for sub, stats in posts_analysis['subreddit_stats'].items():
        report.append(f"| r/{sub} | {stats['total']} | {stats['avg_score']:.1f} | {stats['avg_comments']:.1f} |\n")
    
    report.append("\n## 🔥 Top 20 关键词\n")
    report.append("| 排名 | 关键词 | 出现次数 |\n")
    report.append("|------|--------|----------|\n")
    for i, (word, count) in enumerate(posts_analysis['top_keywords'][:20], 1):
        report.append(f"| {i} | {word} | {count} |\n")
    
    report.append("\n## 🎯 识别到的需求（按类别）\n")
    
    for category, posts in sorted(posts_analysis['needs_by_category'].items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"\n### {category.upper()}\n")
        report.append(f"发现 {len(posts)} 条相关帖子\n\n")
        
        # 按得分排序，取Top 5
        top_posts = sorted(posts, key=lambda x: x['score'], reverse=True)[:5]
        for post in top_posts:
            report.append(f"- [{post['title']}](https://reddit.com/{post['id']}) (Score: {post['score']})\n")
    
    report.append("\n## 💡 痛点帖子Top 20\n")
    pain_posts = sorted(posts_analysis['pain_point_posts'], 
                       key=lambda x: x['score'], reverse=True)[:20]
    for post in pain_posts:
        report.append(f"\n### [{post['title'][:80]}...](https://reddit.com/{post['id']})\n")
        report.append(f"Subreddit: r/{post['subreddit']} | Score: {post['score']}\n")
        report.append(f"痛点: {', '.join(post['pain_points'][:3])}\n")
    
    return ''.join(report)

def main():
    """主函数"""
    print("=" * 60)
    print("Reddit Data Analyzer - Needs Discovery Project")
    print("=" * 60)
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    print("\n📊 加载数据...")
    posts_df, comments_df = load_data()
    print(f"   帖子数: {len(posts_df)}")
    print(f"   评论数: {len(comments_df)}")
    
    # 分析帖子
    print("\n🔍 分析帖子...")
    posts_analysis = analyze_posts(posts_df)
    
    # 分析评论
    print("🔍 分析评论...")
    comments_analysis = analyze_comments(comments_df)
    
    # 生成报告
    print("📝 生成报告...")
    report = generate_needs_report(posts_analysis, comments_analysis, posts_df)
    
    # 保存报告
    report_path = OUTPUT_DIR / 'needs_analysis_report.md'
    with open(report_path, 'w') as f:
        f.write(report)
    
    # 保存JSON格式的详细数据
    json_path = OUTPUT_DIR / 'analysis_results.json'
    with open(json_path, 'w') as f:
        json.dump({
            'posts_analysis': {
                'total_posts': posts_analysis['total_posts'],
                'pain_point_count': posts_analysis['pain_point_count'],
                'top_keywords': posts_analysis['top_keywords'],
                'subreddit_stats': posts_analysis['subreddit_stats']
            },
            'comments_analysis': {
                'total_comments': comments_analysis['total_comments'],
                'top_words': comments_analysis['top_words']
            }
        }, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ 分析完成!")
    print(f"📁 报告保存在: {report_path}")
    print("=" * 60)

if __name__ == '__main__':
    main()
