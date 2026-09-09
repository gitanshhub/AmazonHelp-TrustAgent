"""
scripts/brand_ranking.py
Analyzes twcs.csv for brand selection (Milestones 1 & 2).
Computes:
1. General dataset metrics: total tweets, inbound vs outbound, unique brands.
2. Per-brand conversation depth, multi-turn volume, and customer-brand interactions.
3. Ranks candidate brands (e.g. AmazonHelp, AppleSupport, SpotifyCares, etc.)
"""

import csv
import sys
import os
import json
import time
from collections import Counter, defaultdict

def analyze_dataset(csv_path="twcs/twcs.csv", max_rows=None):
    start_time = time.time()
    print(f"Starting brand analysis on {csv_path}...", flush=True)
    
    total_tweets = 0
    inbound_count = 0
    outbound_count = 0
    brand_outbound = Counter()
    
    # Store parent pointers: tweet_id -> in_response_to_tweet_id
    # And tweet_id -> (author_id, inbound_bool)
    # To keep memory light, we can sample or track top brands directly
    # First pass: identify top 15 brands by volume
    print("Pass 1: Identifying top brands by response volume...", flush=True)
    with open(csv_path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            total_tweets += 1
            inbound = row['inbound'].strip().lower() == 'true'
            author = row['author_id'].strip()
            
            if inbound:
                inbound_count += 1
            else:
                outbound_count += 1
                brand_outbound[author] += 1
                
            if (i + 1) % 500000 == 0:
                elapsed = time.time() - start_time
                print(f"Scanned {i+1:,} rows in {elapsed:.1f}s...", flush=True)

    top_brands = [b for b, _ in brand_outbound.most_common(15)]
    print(f"\nTotal Tweets: {total_tweets:,}", flush=True)
    print(f"Customer Tweets: {inbound_count:,} ({inbound_count/total_tweets*100:.1f}%)", flush=True)
    print(f"Brand Tweets: {outbound_count:,} ({outbound_count/total_tweets*100:.1f}%)", flush=True)
    print(f"Top 15 Support Brands: {', '.join(top_brands)}", flush=True)

    # Pass 2: Measure conversation depth and multi-turn threads for top brands
    print("\nPass 2: Measuring conversation structure for top brands...", flush=True)
    # We will track chains for top brands
    brand_thread_counts = Counter() # number of conversation starts
    brand_multiturn_counts = Counter() # threads with >= 3 turns
    brand_customer_replies = Counter()
    
    # Map tweet_id -> author for tweets belonging to top brands or replying to them
    top_brand_set = set(top_brands)
    
    # Let's do a fast second pass for brand-specific conversations
    with open(csv_path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows and i >= max_rows:
                break
            author = row['author_id'].strip()
            in_reply = row['in_response_to_tweet_id'].strip()
            resp_tweets = row['response_tweet_id'].strip()
            
            if author in top_brand_set:
                # This is a brand reply
                if resp_tweets: # Brand got further replies (multi-turn!)
                    brand_multiturn_counts[author] += 1

    print("\n" + "="*80, flush=True)
    print(f"{'Brand':<20} | {'Total Tweets':<14} | {'Multi-turn Replies':<20} | {'Domain':<20}", flush=True)
    print("="*80, flush=True)
    
    domains = {
        "AmazonHelp": "E-Commerce / Deliveries",
        "AppleSupport": "Tech / Hardware / OS",
        "Uber_Support": "Rideshare / Transport",
        "SpotifyCares": "Digital Subscription / Music",
        "Delta": "Airlines / Travel",
        "Tesco": "Retail / Supermarket",
        "AmericanAir": "Airlines / Travel",
        "comcastcares": "Telecom / ISP",
        "TMobileHelp": "Telecom / Mobile",
        "British_Airways": "Airlines / Travel",
        "SouthwestAir": "Airlines / Travel",
        "Ask_Spectrum": "Telecom / ISP",
        "XboxSupport": "Gaming / Consoles",
        "hpsupport": "Hardware / Computers",
        "ChipotleTweets": "Food / Restaurant"
    }

    results = []
    for brand in top_brands:
        vol = brand_outbound[brand]
        multi = brand_multiturn_counts[brand]
        dom = domains.get(brand, "Support")
        print(f"{brand:<20} | {vol:<14,} | {multi:<20,} | {dom:<20}", flush=True)
        results.append({
            "brand": brand,
            "total_tweets": vol,
            "multiturn_replies": multi,
            "domain": dom
        })

    os.makedirs("data", exist_ok=True)
    summary_path = "data/brand_ranking.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_tweets": total_tweets,
            "inbound_count": inbound_count,
            "outbound_count": outbound_count,
            "unique_brands": len(brand_outbound),
            "brands": results
        }, f, indent=2)
    print(f"\nSaved brand ranking analysis to {summary_path}", flush=True)
    print(f"Total time elapsed: {time.time() - start_time:.1f}s", flush=True)

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "twcs/twcs.csv"
    max_r = int(sys.argv[2]) if len(sys.argv) > 2 else None
    analyze_dataset(csv_file, max_r)
