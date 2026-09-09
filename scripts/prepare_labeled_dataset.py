"""
scripts/prepare_labeled_dataset.py
Runs Milestone 7 & 8:
- Reads processed_conversations.parquet
- Labels conversations according to intent taxonomy
- Splits into 70% Train / 15% Val / 15% Test without data leakage
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.intents.labeling import label_dataset, split_and_save_dataset

def main():
    start = time.time()
    print("Executing Intent Labeling and Conversation-level Partitioning...")
    df_labeled = label_dataset(
        input_parquet="data/processed_conversations.parquet",
        sample_size=12_000,
        random_state=42
    )
    split_and_save_dataset(df_labeled, output_dir="data")
    print(f"Dataset preparation complete in {time.time() - start:.1f}s!")

if __name__ == "__main__":
    main()
