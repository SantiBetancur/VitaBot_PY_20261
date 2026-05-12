from typing import List
import logging

from openai import OpenAI


LOGGER = logging.getLogger(__name__)


class OpenAIEmbeddingClient:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        expected_dimension: int,
    ) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.expected_dimension = expected_dimension

        LOGGER.info(
            "OpenAI embedding client ready | model=%s | expected_dim=%s",
            self.model_name,
            self.expected_dimension,
        )

    def embed_passages(self, texts: List[str], batch_size: int) -> List[List[float]]:
        if not texts:
            return []

        vectors: List[List[float]] = []

        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch,
            )

            for item in response.data:
                vector = item.embedding
                if len(vector) != self.expected_dimension:
                    raise ValueError(
                        "Unexpected embedding dimension from OpenAI. "
                        f"Expected {self.expected_dimension}, got {len(vector)}"
                    )
                vectors.append(vector)

        if len(vectors) != len(texts):
            raise RuntimeError(
                "OpenAI embeddings count mismatch. "
                f"Expected {len(texts)} vectors, got {len(vectors)}"
            )

        return vectors
