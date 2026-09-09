"""
src/ingestion/conversation_builder.py
Reconstructs multi-turn conversation trees from raw tweets.
Traces parent pointers (in_response_to_tweet_id) to the root inquiry,
orders messages chronologically, assigns roles ('customer', 'brand'), and applies cleaning.
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.preprocessing.cleaner import clean_text, is_valid_message

def parse_twitter_date(date_str: str) -> Optional[datetime]:
    """Parse Twitter created_at timestamp string."""
    try:
        # Format: Wed Oct 11 06:55:44 +0000 2017
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        return None

def build_conversations(
    df_tweets: pd.DataFrame,
    target_brand: str = "AmazonHelp",
    min_turns: int = 2
) -> List[Dict[str, Any]]:
    """
    Reconstructs conversation threads from a DataFrame of tweets.
    Returns a list of conversation dictionaries.
    """
    print(f"Reconstructing conversations for {target_brand} from {len(df_tweets):,} tweets...")
    
    # Index tweets by tweet_id
    tweet_dict = {}
    parent_map = {} # child_id -> parent_id
    
    for _, row in df_tweets.iterrows():
        tid = str(row["tweet_id"]).strip()
        author = str(row["author_id"]).strip()
        inbound = str(row["inbound"]).strip().lower() == "true"
        parent_id = str(row.get("in_response_to_tweet_id", "")).strip()
        text = str(row.get("text", "")).strip()
        created_at_raw = str(row.get("created_at", "")).strip()
        dt = parse_twitter_date(created_at_raw)
        
        tweet_dict[tid] = {
            "tweet_id": tid,
            "author_id": author,
            "inbound": inbound,
            "parent_id": parent_id,
            "raw_text": text,
            "dt": dt,
            "role": "customer" if (inbound or author != target_brand) else "brand"
        }
        
        if parent_id and parent_id != "nan" and parent_id != "None":
            parent_map[tid] = parent_id

    # Trace each tweet to its conversation root
    def find_root(t_id: str) -> str:
        visited = set()
        curr = t_id
        while curr in parent_map and curr not in visited:
            visited.add(curr)
            parent = parent_map[curr]
            if parent in tweet_dict:
                curr = parent
            else:
                # Parent tweet not in dataset, curr is top-most ancestor
                break
        return curr

    # Group tweets by root
    conv_groups = {}
    for tid, info in tweet_dict.items():
        root_id = find_root(tid)
        if root_id not in conv_groups:
            conv_groups[root_id] = []
        conv_groups[root_id].append(info)

    print(f"Identified {len(conv_groups):,} candidate conversation trees.")
    
    reconstructed = []
    for root_id, msgs in conv_groups.items():
        # Sort chronologically by datetime if available, otherwise by parent chain order
        msgs_sorted = sorted(msgs, key=lambda m: m["dt"].timestamp() if m["dt"] else 0)
        
        # Clean messages
        cleaned_msgs = []
        has_customer = False
        has_brand = False
        
        for m in msgs_sorted:
            cleaned = clean_text(m["raw_text"])
            if not is_valid_message(cleaned):
                continue
            
            role = m["role"]
            if role == "customer":
                has_customer = True
            elif role == "brand":
                has_brand = True
                
            cleaned_msgs.append({
                "role": role,
                "text": cleaned,
                "tweet_id": m["tweet_id"]
            })
            
        # Filter: must have at least min_turns, must have both customer and brand
        if len(cleaned_msgs) < min_turns or not (has_customer and has_brand):
            continue
            
        # First message should ideally be customer inquiry
        # Find first customer message and first brand message
        first_cust = next((m["text"] for m in cleaned_msgs if m["role"] == "customer"), None)
        first_brand = next((m["text"] for m in cleaned_msgs if m["role"] == "brand"), None)
        
        if not first_cust or not first_brand:
            continue
            
        reconstructed.append({
            "conversation_id": f"conv_{root_id}",
            "brand": target_brand,
            "num_turns": len(cleaned_msgs),
            "customer_inquiry": first_cust,
            "brand_resolution": first_brand,
            "messages": cleaned_msgs
        })

    print(f"Successfully reconstructed {len(reconstructed):,} valid support conversations.")
    return reconstructed

def save_conversations(conversations: List[Dict[str, Any]], output_parquet: str = "data/processed_conversations.parquet"):
    """Saves reconstructed conversations to Parquet and a small JSON sample."""
    os.makedirs(os.path.dirname(output_parquet), exist_ok=True)
    df = pd.DataFrame(conversations)
    df.to_parquet(output_parquet, index=False)
    print(f"Saved {len(df):,} conversations to {output_parquet}")
    
    sample_json = os.path.splitext(output_parquet)[0] + "_sample.json"
    with open(sample_json, "w", encoding="utf-8") as f:
        json.dump(conversations[:20], f, indent=2)
    print(f"Saved 20 sample conversations to {sample_json}")
