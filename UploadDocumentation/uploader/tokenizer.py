import re
from typing import List


class TokenCounter:
    def __init__(self) -> None:
        self._encoding = None

        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoding = None

    def count(self, text: str) -> int:
        if not text:
            return 0

        if self._encoding is not None:
            return len(self._encoding.encode(text))

        return len(re.findall(r"\w+|[^\w\s]", text))

    def tail_text(self, text: str, tail_tokens: int) -> str:
        if not text or tail_tokens <= 0:
            return ""

        if self._encoding is not None:
            encoded = self._encoding.encode(text)
            tail = encoded[-tail_tokens:]
            return self._encoding.decode(tail).strip()

        words = text.split()
        return " ".join(words[-tail_tokens:]).strip()

    def split_text_by_token_limit(self, text: str, max_tokens: int) -> List[str]:
        if not text:
            return []

        if self.count(text) <= max_tokens:
            return [text.strip()]

        if self._encoding is not None:
            encoded = self._encoding.encode(text)
            parts = []

            for start in range(0, len(encoded), max_tokens):
                piece = encoded[start : start + max_tokens]
                decoded = self._encoding.decode(piece).strip()
                if decoded:
                    parts.append(decoded)

            return parts

        words = text.split()
        parts = []
        current = []

        for word in words:
            current.append(word)
            if len(current) >= max_tokens:
                parts.append(" ".join(current).strip())
                current = []

        if current:
            parts.append(" ".join(current).strip())

        return parts
