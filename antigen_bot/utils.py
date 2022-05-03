"""utils function for AntigenBot"""
from __future__ import annotations


def remove_at_info(text: str) -> str:
    """get the clear message, remove the command prefix and at"""
    split_chars = ['\u2005', '\u0020']
    while text.startswith('@'):
        text = text.strip()
        for char in split_chars:
            tokens = text.split(char)
            if len(tokens) > 1:
                tokens = [token for token in text.split(char) if not token.startswith('@')]
                text = char.join(tokens)
            else:
                text = ''.join(tokens)
    return text
