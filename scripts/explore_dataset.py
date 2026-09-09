"""
scripts/explore_dataset.py
Explores twcs.csv to compute dataset statistics and rank brands.
Designed to be fast, memory-efficient, and runnable with standard library or pandas.
"""

import csv
import sys
import os
import json
from collections import Counter, defaultdict

def explore(csv_path: str, max_rows: int = None):
    print(f"Reading dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        sys.exit(1)

    file_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")

    total_tweets = 0
    inbound_count = 0  # customer tweets
    outbound_count = 0 # brand tweets
    brand_counts = Counter()
    brand_inbound_replies = Counter()
    
    # Track conversation graph: tweet_id -> response_tweet_id / in_response_to
    # We also track author per tweet
    tweet_authors = {}
    in_response_to = {}
    
    with open(csv_path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        print(f"Columns: {columns}")
        
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            total_tweets += 1
            tid = row['tweet_id']
            author = row['author_id']
            inbound = row['inbound'].strip().lower() == 'true'
            resp_to = row['in_response_to_tweet_id'].strip()
            
            if inbound:
                inbound_count += 1
            else:
                outbound_count += 1
                brand_counts[author] += 1
            
            if resp_to:
                in_response_to[tid] = resp_to
            tweet_authors[tid] = (author, inbound)
            
            if (i + 1) % 500000 == 0:
                print(f"Processed {i + 1:,} rows...")

    print(f"\n--- General Statistics ---")
    print(f"Total rows scanned: {total_tweets:,}")
    print(f"Customer (inbound) messages: {inbound_count:,} ({inbound_count / total_tweets * 100:.1f}%)")
    print(f"Brand (outbound) messages: {outbound_count:,} ({outbound_count / total_tweets * 100:.1f}%)")
    print(f"Unique brands identified: {len(brand_counts):,}")
    
    print("\n--- Top 20 Brands by Outbound Support Volume ---")
    print(f"{'Brand':<25} | {'Brand Tweets':<12}")
    print("-" * 42)
    for brand, count in brand_counts.most_common(20):
        print(f"{brand:<25} | {count:<12,}")

    stats = {
        "file_size_mb": round(file_size_mb, 2),
        "total_tweets": total_tweets,
        "customer_messages": inbound_count,
        "brand_messages": outbound_count,
        "unique_brands": len(brand_counts),
        "top_brands": brand_counts.most_common(20)
    }
    
    os.makedirs("data", exist_ok=True)
    out_json = "data/exploration_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"\nSaved summary to {out_json}")

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "twcs/twcs.csv"
    max_r = int(sys.argv[2]) if len(sys.argv) > 2 else None
    explore(csv_file, max_r)
