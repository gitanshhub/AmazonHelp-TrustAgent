"""
tests/test_conversation_builder.py
Unit tests for conversation tree stitching and cleaning.
"""

import pytest
import pandas as pd
from src.preprocessing.cleaner import clean_text, is_valid_message
from src.ingestion.conversation_builder import build_conversations

def test_clean_text_removes_handles_and_normalizes_links():
    raw = "@AmazonHelp where is my order? https://t.co/abc123xyz ^JD"
    cleaned = clean_text(raw)
    assert "@AmazonHelp" not in cleaned
    assert "^JD" not in cleaned
    assert "[LINK]" in cleaned
    assert "where is my order?" in cleaned

def test_is_valid_message():
    assert is_valid_message("My package hasn't arrived.") is True
    assert is_valid_message("") is False
    assert is_valid_message("   ") is False
    assert is_valid_message("?") is False

def test_build_conversations_stitches_turns():
    df_sample = pd.DataFrame([
        {
            "tweet_id": "1",
            "author_id": "1001",
            "inbound": "True",
            "in_response_to_tweet_id": "",
            "text": "Where is my package? @AmazonHelp",
            "created_at": "Wed Oct 11 06:55:44 +0000 2017"
        },
        {
            "tweet_id": "2",
            "author_id": "AmazonHelp",
            "inbound": "False",
            "in_response_to_tweet_id": "1",
            "text": "We can help, please check tracking at [LINK]",
            "created_at": "Wed Oct 11 07:05:00 +0000 2017"
        }
    ])
    convs = build_conversations(df_sample, target_brand="AmazonHelp", min_turns=2)
    assert len(convs) == 1
    assert convs[0]["num_turns"] == 2
    assert "Where is my package?" in convs[0]["customer_inquiry"]
    assert "We can help" in convs[0]["brand_resolution"]
