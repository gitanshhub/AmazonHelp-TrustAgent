"""
src/ingestion/loader.py
Loads raw Twitter customer support data for a specific brand.
Filters tweets related to the target brand (both inbound customer queries and outbound brand responses).
"""

import os
import pandas as pd
from typing import Optional, Set

def load_brand_tweets(
    csv_path: str = "twcs/twcs.csv",
    target_brand: str = "AmazonHelp",
    chunksize: int = 250_000,
    max_tweets: Optional[int] = None
) -> pd.DataFrame:
    """
    Reads twcs.csv in chunks and filters tweets related to target_brand.
    Returns a consolidated DataFrame with relevant tweets.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    print(f"Filtering dataset for brand '{target_brand}' from {csv_path}...")
    
    # First pass: collect all tweet IDs authored by target_brand and their in_response_to / response ids
    brand_tweet_ids: Set[str] = set()
    referenced_tweet_ids: Set[str] = set()
    
    # We first find all tweets directly authored by the brand to get all interaction anchors
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, dtype=str, keep_default_na=False):
        brand_mask = chunk["author_id"] == target_brand
        brand_rows = chunk[brand_mask]
        
        for _, row in brand_rows.iterrows():
            brand_tweet_ids.add(row["tweet_id"])
            if row["in_response_to_tweet_id"]:
                referenced_tweet_ids.add(row["in_response_to_tweet_id"])
            if row["response_tweet_id"]:
                for resp_id in row["response_tweet_id"].split(","):
                    resp_id_clean = resp_id.strip()
                    if resp_id_clean:
                        referenced_tweet_ids.add(resp_id_clean)

    print(f"Found {len(brand_tweet_ids):,} brand tweets and {len(referenced_tweet_ids):,} referenced tweets.")
    all_relevant_ids = brand_tweet_ids | referenced_tweet_ids

    # Second pass: extract all rows belonging to all_relevant_ids
    collected_chunks = []
    total_extracted = 0
    
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, dtype=str, keep_default_na=False):
        relevant_mask = chunk["tweet_id"].isin(all_relevant_ids)
        filtered = chunk[relevant_mask]
        if not filtered.empty:
            collected_chunks.append(filtered)
            total_extracted += len(filtered)
            if max_tweets and total_extracted >= max_tweets:
                break

    df_result = pd.concat(collected_chunks, ignore_index=True)
    df_result.drop_duplicates(subset=["tweet_id"], inplace=True)
    print(f"Extracted {len(df_result):,} total relevant tweets for {target_brand}.")
    return df_result
