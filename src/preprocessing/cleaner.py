"""
src/preprocessing/cleaner.py
Cleans and normalizes customer and brand messages.
Removes noisy mentions, anonymized user tokens (@12345), simplifies URLs, and filters low-value turns.
"""

import re
from typing import Optional

# Regex patterns for cleaning Twitter text
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+')
USER_HANDLE_PATTERN = re.compile(r'@[\w_]+')
MULTIPLE_SPACES_PATTERN = re.compile(r'\s+')
BOT_SIGNATURE_PATTERN = re.compile(r'\s*\^[A-Z]{1,3}\s*$|\s*/[A-Z]{1,3}\s*$')

def clean_text(text: str, remove_handles: bool = True, normalize_urls: bool = True) -> str:
    """
    Cleans raw tweet text.
    - Normalizes URLs to [URL] or removes them
    - Strips noisy user handles (@AmazonHelp, @12345)
    - Strips agent signatures (e.g. ^RR, /AY)
    - Normalizes whitespace
    """
    if not isinstance(text, str):
        return ""

    cleaned = text
    
    # Strip agent initials signatures (e.g. "^JD", "/SW")
    cleaned = BOT_SIGNATURE_PATTERN.sub('', cleaned)

    if normalize_urls:
        cleaned = URL_PATTERN.sub('[LINK]', cleaned)
        
    if remove_handles:
        cleaned = USER_HANDLE_PATTERN.sub('', cleaned)
        
    cleaned = MULTIPLE_SPACES_PATTERN.sub(' ', cleaned).strip()
    return cleaned

def is_valid_message(text: str) -> bool:
    """
    Checks if message has meaningful content (not just empty, punctuation, or just link).
    """
    if not text or len(text.strip()) < 3:
        return False
    # If it only contains [LINK] or punctuation
    stripped = re.sub(r'\[LINK\]|[^\w\s]', '', text).strip()
    return len(stripped) >= 2
