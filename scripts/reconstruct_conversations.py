"""
scripts/reconstruct_conversations.py
Executes Milestone 4 & 5:
1. Loads all tweets for AmazonHelp and their customer counter-parts
2. Reconstructs multi-turn conversation trees
3. Cleans text and filters noise
4. Exports data/processed_conversations.parquet
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.loader import load_brand_tweets
from src.ingestion.conversation_builder import build_conversations, save_conversations

def main(csv_path="twcs/twcs.csv", target_brand="AmazonHelp", max_tweets=None):
    start = time.time()
    print(f"Starting conversation reconstruction for {target_brand}...")
    
    # 1. Load brand tweets
    df_tweets = load_brand_tweets(csv_path=csv_path, target_brand=target_brand, max_tweets=max_tweets)
    
    # 2. Build conversation trees
    conversations = build_conversations(df_tweets, target_brand=target_brand, min_turns=2)
    
    # 3. Save to parquet
    save_conversations(conversations, output_parquet="data/processed_conversations.parquet")
    
    print(f"Done in {time.time() - start:.1f}s!")

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "twcs/twcs.csv"
    brand = sys.argv[2] if len(sys.argv) > 2 else "AmazonHelp"
    main(csv_file, brand)
