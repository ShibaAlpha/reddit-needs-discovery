#!/usr/bin/env python3
"""
Scrape Reddit posts from old.reddit.com using browser automation
"""
import json
import time
import sqlite3
from datetime import datetime

# Database setup
DB_PATH = "/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/reddit_posts.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT,
        subreddit TEXT,
        url TEXT,
        flair TEXT,
        timestamp TEXT,
        created_utc REAL,
        score INTEGER,
        num_comments INTEGER,
        selftext TEXT,
        scraped_at TEXT
    )''')
    conn.commit()
    return conn

def save_posts(posts, conn):
    c = conn.cursor()
    for post in posts:
        try:
            c.execute('''INSERT OR REPLACE INTO posts 
                (id, title, author, subreddit, url, flair, timestamp, score, num_comments, selftext, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (post['id'], post['title'], post['author'], post['subreddit'],
                 post['url'], post['flair'], post['timestamp'], post['score'],
                 post['num_comments'], post.get('selftext', ''), datetime.now().isoformat()))
        except Exception as e:
            print(f"Error saving post: {e}")
    conn.commit()

def get_existing_ids(conn):
    c = conn.cursor()
    c.execute('SELECT id FROM posts')
    return set(row[0] for row in c.fetchall())

# Manual extraction from the page - these are posts I observed
# Let me try a different approach - use the Reddit API with proper credentials

# Actually, let's try using web_fetch with a different approach
# But first, let's try using the json endpoint that old.reddit uses

if __name__ == "__main__":
    conn = init_db()
    print("Database initialized")
    print(f"Existing posts: {len(get_existing_ids(conn))}")
