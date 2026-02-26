#!/usr/bin/env python3
"""
Scrape Reddit posts from old.reddit.com using JSON API
"""
import json
import sqlite3
from datetime import datetime
import urllib.request
import urllib.parse
import time
import os

DB_PATH = "/Users/openclaw-bot/.openclaw/workspace/reddit-needs-discovery/reddit_posts.db"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/605.1.15"

SUBREDDITS = [
    "productivity",
    "getdisciplined", 
    "ADHD",
    "entrepreneur",
    "smallbusiness",
    "iphonestocks",
    "ios",
    "appstore",
    "apple",
]

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
    count = 0
    for post in posts:
        try:
            c.execute('''INSERT OR REPLACE INTO posts 
                (id, title, author, subreddit, url, flair, timestamp, score, num_comments, selftext, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (post['id'], post['title'], post['author'], post['subreddit'],
                 post['url'], post.get('flair', ''), post.get('timestamp', ''), 
                 post.get('score', 0), post.get('num_comments', 0), 
                 post.get('selftext', ''), datetime.now().isoformat()))
            count += 1
        except Exception as e:
            print(f"Error saving post {post.get('id')}: {e}")
    conn.commit()
    return count

def get_existing_ids(conn):
    c = conn.cursor()
    c.execute('SELECT id FROM posts')
    return set(row[0] for row in c.fetchall())

def fetch_subreddit(subreddit, after=None):
    """Fetch posts from a subreddit using the JSON API"""
    url = f"https://old.reddit.com/r/{subreddit}/new.json?limit=25"
    if after:
        url += f"&after={after}"
    
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error fetching r/{subreddit}: {e}")
        return None

def parse_posts(data, subreddit):
    """Parse posts from Reddit JSON response"""
    posts = []
    children = data.get('data', {}).get('children', [])
    
    for child in children:
        post_data = child.get('data', {})
        posts.append({
            'id': post_data.get('id', ''),
            'title': post_data.get('title', ''),
            'author': post_data.get('author', ''),
            'subreddit': subreddit,
            'url': post_data.get('url', ''),
            'flair': post_data.get('link_flair_text', ''),
            'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
            'created_utc': post_data.get('created_utc', 0),
            'score': post_data.get('score', 0),
            'num_comments': post_data.get('num_comments', 0),
            'selftext': post_data.get('selftext', '')
        })
    
    return posts, data.get('data', {}).get('after', None)

def main():
    conn = init_db()
    existing_ids = get_existing_ids(conn)
    print(f"Existing posts: {len(existing_ids)}")
    
    total_added = 0
    target = 1000
    
    # Scrape multiple pages from each subreddit
    for subreddit in SUBREDDITS:
        if total_added >= target:
            break
            
        print(f"\n=== Scraping r/{subreddit} ===")
        after = None
        
        # Fetch 10 pages per subreddit (250 posts)
        for page in range(10):
            if total_added >= target:
                break
                
            print(f"  Page {page+1}...", end=" ")
            data = fetch_subreddit(subreddit, after)
            
            if not data:
                print("failed")
                break
                
            posts, after = parse_posts(data, subreddit)
            
            # Filter out existing posts
            new_posts = [p for p in posts if p['id'] not in existing_ids]
            existing_ids.update(p['id'] for p in new_posts)
            
            if new_posts:
                count = save_posts(new_posts, conn)
                total_added += count
                print(f"added {count} new posts (total: {total_added})")
            else:
                print("no new posts")
            
            if not after:
                print("  No more pages")
                break
                
            time.sleep(1)  # Rate limiting
    
    print(f"\n=== Done! Total new posts added: {total_added} ===")
    
    # Print final stats
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM posts')
    print(f"Total posts in database: {c.fetchone()[0]}")
    
    conn.close()

if __name__ == "__main__":
    main()
