#!/usr/bin/env python3
"""
Reddit Data Crawler for Needs Discovery
采集14个Subreddits的帖子和评论
"""

import praw
import json
import time
import os
from datetime import datetime
from pathlib import Path
import sqlite3

# 配置
SUBREDDITS = [
    'iOSProgramming', 'productivity',  # 开发/效率
    'investing', 'FIREUK', 'UKPersonalFinance',  # 理财
    'Notion', 'bulletjournal',  # 学习/笔记
    'running', 'fitness',  # 健康
    'travelhacks', 'Flights',  # 旅行
    'IWantToBuy', 'lifehacks', 'legaladviceUK'  # 实用
]

OUTPUT_DIR = Path('/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/data')

# 数据库路径
DB_PATH = OUTPUT_DIR / 'reddit_posts.db'

def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 创建帖子表
    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            title TEXT,
            selftext TEXT,
            author TEXT,
            created_utc REAL,
            ups INTEGER,
            downs INTEGER,
            score INTEGER,
            num_comments INTEGER,
            is_self BOOLEAN,
            flair TEXT,
            url TEXT,
            collected_at TEXT
        )
    ''')
    
    # 创建评论表
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            post_id TEXT,
            subreddit TEXT,
            author TEXT,
            body TEXT,
            created_utc REAL,
            score INTEGER,
            parent_id TEXT,
            is_top_level BOOLEAN,
            collected_at TEXT
        )
    ''')
    
    # 创建索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_subreddit ON posts(subreddit)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_created ON posts(created_utc DESC)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_post_comments ON comments(post_id)')
    
    conn.commit()
    return conn

def get_reddit_client():
    """创建Reddit API客户端（无需认证）"""
    return praw.Reddit(
        client_id=os.environ.get('REDDIT_CLIENT_ID', 'demo'),
        client_secret=os.environ.get('REDDIT_CLIENT_SECRET', 'demo'),
        user_agent='NeedsDiscoveryBot/1.0',
        read_only=True
    )

def collect_posts(reddit, subreddit_name, limit=500):
    """采集帖子"""
    subreddit = reddit.subreddit(subreddit_name)
    
    posts = []
    collected_at = datetime.utcnow().isoformat()
    
    # 采集热门帖子
    for post in subreddit.hot(limit=limit):
        posts.append({
            'id': post.id,
            'subreddit': subreddit_name,
            'title': post.title,
            'selftext': post.selftext[:5000] if post.selftext else '',  # 限制长度
            'author': str(post.author) if post.author else '[deleted]',
            'created_utc': post.created_utc,
            'ups': post.ups,
            'downs': post.downs,
            'score': post.score,
            'num_comments': post.num_comments,
            'is_self': post.is_self,
            'flair': post.link_flair_text or '',
            'url': post.url,
            'collected_at': collected_at
        })
    
    return posts

def collect_comments(reddit, post_id, limit=20):
    """采集帖子评论"""
    submission = reddit.submission(post_id)
    
    comments = []
    collected_at = datetime.utcnow().isoformat()
    
    # 替换更多回复以获取所有评论
    submission.comments.replace_more(limit=0)
    
    def process_comments(comments_list, post_id, subreddit, level=0):
        for comment in comments_list[:limit]:
            if level == 0 or comment.score > 0:  # 只采顶级评论或高赞评论
                comments.append({
                    'id': comment.id,
                    'post_id': post_id,
                    'subreddit': subreddit,
                    'author': str(comment.author) if comment.author else '[deleted]',
                    'body': comment.body[:2000] if comment.body else '',
                    'created_utc': comment.created_utc,
                    'score': comment.score,
                    'parent_id': comment.parent_id,
                    'is_top_level': level == 0,
                    'collected_at': collected_at
                })
            
            # 递归处理回复
            if hasattr(comment, 'replies'):
                process_comments(comment.replies, post_id, subreddit, level + 1)
    
    process_comments(submission.comments, post_id, subreddit_name)
    
    return comments

def save_to_db(conn, posts, comments):
    """保存到SQLite数据库"""
    c = conn.cursor()
    
    # 保存帖子
    for post in posts:
        c.execute('''
            INSERT OR REPLACE INTO posts 
            (id, subreddit, title, selftext, author, created_utc, ups, downs, score, num_comments, is_self, flair, url, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post['id'], post['subreddit'], post['title'], post['selftext'],
            post['author'], post['created_utc'], post['ups'], post['downs'],
            post['score'], post['num_comments'], post['is_self'], 
            post['flair'], post['url'], post['collected_at']
        ))
    
    # 保存评论
    for comment in comments:
        c.execute('''
            INSERT OR REPLACE INTO comments 
            (id, post_id, subreddit, author, body, created_utc, score, parent_id, is_top_level, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comment['id'], comment['post_id'], comment['subreddit'],
            comment['author'], comment['body'], comment['created_utc'],
            comment['score'], comment['parent_id'], comment['is_top_level'],
            comment['collected_at']
        ))
    
    conn.commit()

def main():
    """主函数"""
    print("=" * 60)
    print("Reddit Data Crawler - Needs Discovery Project")
    print("=" * 60)
    
    # 初始化
    conn = init_database()
    reddit = get_reddit_client()
    
    total_posts = 0
    total_comments = 0
    
    start_time = time.time()
    
    for subreddit in SUBREDDITS:
        print(f"\n📦 正在采集 r/{subreddit}...")
        
        try:
            # 采集帖子
            posts = collect_posts(reddit, subreddit, limit=500)
            print(f"   采集到 {len(posts)} 条帖子")
            
            # 采集评论（只采高赞帖子的评论）
            all_comments = []
            for post in posts[:100]:  # 只采前100个帖子的评论
                try:
                    comments = collect_comments(reddit, post['id'], limit=20)
                    all_comments.extend(comments)
                    time.sleep(0.5)  # 避免请求过快
                except Exception as e:
                    print(f"   评论采集失败: {e}")
            
            print(f"   采集到 {len(all_comments)} 条评论")
            
            # 保存到数据库
            save_to_db(conn, posts, all_comments)
            
            total_posts += len(posts)
            total_comments += len(all_comments)
            
            print(f"   ✅ r/{subreddit} 完成")
            
        except Exception as e:
            print(f"   ❌ r/{subreddit} 失败: {e}")
        
        time.sleep(1)  # 避免请求过快
    
    conn.close()
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 完成！共采集 {total_posts} 条帖子，{total_comments} 条评论")
    print(f"📁 数据保存在: {DB_PATH}")
    print(f"⏱️ 用时: {elapsed:.1f} 秒")
    print("=" * 60)

if __name__ == '__main__':
    main()
