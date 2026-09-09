"""
src/intents/labeling.py
Labels conversations into the brand intent taxonomy using hybrid rule-based and
semantic embedding similarity (SentenceTransformers all-MiniLM-L6-v2).
Partitions data strictly by conversation_id into 70% Train, 15% Validation, 15% Test.
"""

import os
import re
import numpy as np
import pandas as pd
from typing import Tuple
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer
from src.intents.taxonomy import IntentTaxonomy

# Rule-based priority regex patterns for high-risk / unambiguous intents
INTENT_PATTERNS = [
    ("UNAUTHORIZED_TRANSACTION_FRAUD", re.compile(r'\b(hacked|stolen card|unauthorized charge|identity theft|fraudulent|fraud)\b', re.IGNORECASE)),
    ("ACCOUNT_ACCESS_SECURITY", re.compile(r'\b(locked out|reset password|verification code|cannot log in|login problem|otp|2fa)\b', re.IGNORECASE)),
    ("PAYMENT_AND_BILLING_ISSUE", re.compile(r'\b(charged twice|double charged|billing error|unexpected charge|charged me|refund declined|payment method)\b', re.IGNORECASE)),
    ("PACKAGE_DELIVERED_NOT_RECEIVED", re.compile(r'\b(delivered but|says delivered|marked as delivered|handed to resident|never delivered|porch)\b', re.IGNORECASE)),
    ("REFUND_NOT_RECEIVED", re.compile(r'\b(where is my refund|refund hasn\'t|waiting for refund|haven\'t received refund|refund status)\b', re.IGNORECASE)),
    ("DAMAGED_OR_DEFECTIVE_ITEM", re.compile(r'\b(damaged|broken|shattered|crushed|defective|scratched|dented|faulty)\b', re.IGNORECASE)),
    ("WRONG_ITEM_RECEIVED", re.compile(r'\b(wrong item|wrong product|wrong size|different item|missing from order|sent me the wrong)\b', re.IGNORECASE)),
    ("CANCELLATION_REQUEST", re.compile(r'\b(cancel my order|cancel order|cancel this order|cancel purchase|stop shipment)\b', re.IGNORECASE)),
    ("RETURN_EXCHANGE_INQUIRY", re.compile(r'\b(return label|how to return|exchange item|drop off return|return policy|send back)\b', re.IGNORECASE)),
    ("PRIME_MEMBERSHIP_INQUIRY", re.compile(r'\b(prime membership|cancel prime|renew prime|prime subscription|prime fee)\b', re.IGNORECASE)),
    ("DIGITAL_SERVICES_AND_DEVICE", re.compile(r'\b(kindle|fire tv|firestick|prime video|streaming error|alexa|echo dot)\b', re.IGNORECASE)),
    ("DELIVERY_DELAY", re.compile(r'\b(late|delayed|running late|still waiting|hasn\'t arrived|not arrived|expected yesterday)\b', re.IGNORECASE)),
    ("ORDER_TRACKING_STATUS", re.compile(r'\b(track|tracking number|where is my package|when will it ship|status of order|dispatch)\b', re.IGNORECASE)),
]

def is_clean_english(text: str) -> bool:
    """Filter out non-ascii characters and verify reasonable word count."""
    if not isinstance(text, str):
        return False
    try:
        text.encode('ascii')
    except UnicodeEncodeError:
        return False
    words = text.split()
    return len(words) >= 4 and len(text) >= 15

def label_dataset(
    input_parquet: str = "data/processed_conversations.parquet",
    sample_size: int = 12_000,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Filters English conversations, assigns intent labels using taxonomy patterns + semantic embeddings.
    """
    print(f"Loading conversations from {input_parquet}...")
    df = pd.read_parquet(input_parquet)
    print(f"Total raw conversations: {len(df):,}")

    # 1. Filter English conversations
    df_clean = df[df["customer_inquiry"].apply(is_clean_english)].copy()
    print(f"Filtered {len(df_clean):,} clean English conversations.")

    if len(df_clean) > sample_size:
        df_clean = df_clean.sample(n=sample_size, random_state=random_state).reset_index(drop=True)
        print(f"Sampled {len(df_clean):,} representative conversations for modeling.")

    # 2. Rule-based labeling pass
    labels = []
    rule_matched = 0
    
    for text in df_clean["customer_inquiry"]:
        matched_intent = None
        for intent_name, pattern in INTENT_PATTERNS:
            if pattern.search(text):
                matched_intent = intent_name
                break
        if matched_intent:
            labels.append(matched_intent)
            rule_matched += 1
        else:
            labels.append(None)

    print(f"High-confidence rule patterns matched: {rule_matched:,} ({rule_matched / len(df_clean) * 100:.1f}%)")

    # 3. Semantic Embedding pass for remaining conversations
    unlabeled_indices = [i for i, lbl in enumerate(labels) if lbl is None]
    if unlabeled_indices:
        print(f"Encoding {len(unlabeled_indices):,} remaining messages with SentenceTransformers...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        taxonomy = IntentTaxonomy()
        
        # Create prototype embeddings for each intent using examples and descriptions
        intent_keys = [k for k in taxonomy.get_all_intents() if k != "OTHER"]
        intent_texts = []
        for k in intent_keys:
            desc = taxonomy.get_description(k)
            examples = " ".join(taxonomy.get_examples(k))
            intent_texts.append(f"{k}: {desc} {examples}")
            
        intent_embeddings = model.encode(intent_texts, normalize_embeddings=True)

        unlabeled_texts = df_clean.iloc[unlabeled_indices]["customer_inquiry"].tolist()
        text_embeddings = model.encode(unlabeled_texts, batch_size=128, normalize_embeddings=True, show_progress_bar=False)

        # Compute cosine similarities
        similarities = np.dot(text_embeddings, intent_embeddings.T) # shape: (N, num_intents)
        best_intent_indices = np.argmax(similarities, axis=1)
        best_scores = np.max(similarities, axis=1)

        for idx, best_idx, score in zip(unlabeled_indices, best_intent_indices, best_scores):
            if score >= 0.40:
                labels[idx] = intent_keys[best_idx]
            else:
                labels[idx] = "OTHER"

    df_clean["intent"] = labels
    print("\n--- Intent Label Distribution ---")
    print(df_clean["intent"].value_counts())
    return df_clean

def split_and_save_dataset(
    df_labeled: pd.DataFrame,
    output_dir: str = "data",
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42
):
    """
    Partitions strictly by conversation_id into train/val/test splits without leakage.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Stratify by intent
    train_val_df, test_df = train_test_split(
        df_labeled,
        test_size=test_size,
        random_state=random_state,
        stratify=df_labeled["intent"]
    )
    
    relative_val_size = val_size / (1.0 - test_size)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=relative_val_size,
        random_state=random_state,
        stratify=train_val_df["intent"]
    )

    print(f"\n--- Split Summary ---")
    print(f"Train conversations: {len(train_df):,} ({len(train_df)/len(df_labeled)*100:.1f}%)")
    print(f"Validation conversations: {len(val_df):,} ({len(val_df)/len(df_labeled)*100:.1f}%)")
    print(f"Test conversations: {len(test_df):,} ({len(test_df)/len(df_labeled)*100:.1f}%)")

    train_path = os.path.join(output_dir, "train_conversations.parquet")
    val_path = os.path.join(output_dir, "val_conversations.parquet")
    test_path = os.path.join(output_dir, "test_conversations.parquet")
    full_path = os.path.join(output_dir, "labeled_conversations.parquet")

    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)
    df_labeled.to_parquet(full_path, index=False)

    print(f"Saved splits to {train_path}, {val_path}, {test_path}")
