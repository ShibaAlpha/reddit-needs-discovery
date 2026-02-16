#!/usr/bin/env python3
"""
Reddit Data Crawler using Pushshift API
无需Reddit认证，直接从Pushshift获取数据
"""

import requests
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
import json

# 配置
SUBREDDITS = [
    'iOSProgramming', 'productivity',
    'investing', 'FIREUK', 'UKPersonalFinance',
    'Notion', 'bulletjournal',
    'running', 'fitness',
    'travelhacks', 'Flights',
    'IWantToBuy', 'lifehacks', 'legaladviceUK'
]

OUTPUT_DIR = Path('/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/data')
DB_PATH = OUTPUT_DIR / 'reddit_posts.db'

def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            title TEXT,
            selftext TEXT,
            author TEXT,
            created_utc INTEGER,
            ups INTEGER,
            score INTEGER,
            num_comments INTEGER,
            url TEXT,
            collected_at TEXT
        )
    ''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_subreddit ON posts(subreddit)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_score ON posts(score DESC)')
    
    conn.commit()
    return conn

def fetch_posts_pushshift(subreddit, limit=500, before=None):
    """从Pushshift API获取帖子"""
    url = "https://api.pushshift.io/reddit/search/submission/"
    
    params = {
        'subreddit': subreddit,
        'size': limit,
        'sort': 'desc',
        'sort_type': 'score'
    }
    
    if before:
        params['before'] = before
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        print(f"   Pushshift错误: {e}")
        return []

def fetch_comments_pushshift(subreddit, limit=1000):
    """从Pushshift API获取评论"""
    url = "https://api.pushshift.io/reddit/search/comment/"
    
    params = {
        'subreddit': subreddit,
        'size': limit,
        'sort': 'desc',
        'sort_type': 'score'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        print(f"   评论错误: {e}")
        return []

def save_to_db(conn, posts, comments):
    """保存到数据库"""
    c = conn.cursor()
    
    for post in posts:
        c.execute('''
            INSERT OR REPLACE INTO posts 
            (id, subreddit, title, selftext, author, created_utc, ups, score, num_comments, url, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post.get('id'), post.get('subreddit'), post.get('title'),
            post.get('selftext', '')[:5000], post.get('author', '[deleted]'),
            post.get('created_utc'), post.get('ups', 0), post.get('score', 0),
            post.get('num_comments', 0), post.get('url'),
            datetime.now().isoformat()
        ))
    
    # 简单保存评论数量统计
    comment_counts = {}
    for comment in comments:
        post_id = comment.get('link_id', '').replace('t3_', '')
        if post_id:
            comment_counts[post_id] = comment_counts.get(post_id, 0) + 1
    
    for post_id, count in comment_counts.items():
        c.execute('UPDATE posts SET num_comments = ? WHERE id = ?', (count, post_id))
    
    conn.commit()

def main():
    """主函数"""
    print("=" * 60)
    print("Reddit Data Crawler (Pushshift API)")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = init_database()
    
    total_posts = 0
    total_comments = 0
    start_time = time.time()
    
    for subreddit in SUBREDDITS:
        print(f"\n📦 正在采集 r/{subreddit}...")
        
        try:
            # 获取帖子
            posts = fetch_posts_pushshift(subreddit, limit=500)
            print(f"   帖子: {len(posts)}")
            
            # 获取评论
            comments = fetch_comments_pushshift(subreddit, limit=1000)
            print(f"   评论: {len(comments)}")
            
            # 保存
            save_to_db(conn, posts, comments)
            
            total_posts += len(posts)
            total_comments += len(comments)
            
            print(f"   ✅ 完成")
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
        
        time.sleep(1)  # 避免请求过快
    
    conn.close()
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 完成! 采集 {total_posts} 条帖子, {total_comments} 条评论")
    print(f"📁 数据: {DB_PATH}")
    print(f"⏱️ 用时: {elapsed:.1f}秒")
    print("=" * 60)

if __name__ == '__main__':
    main()
