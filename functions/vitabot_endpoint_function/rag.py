import logging

import numpy as np

from config import openai_client, OPENAI_MODEL, MIN_SIMILARITY_THRESHOLD
from supabase_client import rpc

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> list[float]:
    """Genera un embedding con OpenAI para el texto dado."""
    try:
        response = openai_client.embeddings.create(model=OPENAI_MODEL, input=text)
        return response.data[0].embedding
    except Exception as exc:
        raise Exception(f"Error generating embedding: {exc}") from exc


def cosine_similarity(a, b) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def query_similar_documents(embedding: list[float], top_k: int = 3) -> list[dict]:
    """Busca los documentos más similares en Supabase usando la función RPC de pgvector."""
    try:
        logger.info("Querying similar documents via pgvector RPC")
        results = rpc(
            schema="rag",
            function_name="match_documents",
            params={
                "query_embedding": embedding,
                "match_threshold":  MIN_SIMILARITY_THRESHOLD,
                "match_count":      top_k,
            },
        )

        if not results:
            logger.info("No similar documents found")
            return []

        docs = [
            {
                "id":         doc["id"],
                "content":    doc["content"],
                "source":     doc.get("source", "Fuente desconocida"),
                "similarity": float(doc.get("similarity", 0)),
            }
            for doc in results
        ]
        logger.info("Found %s similar documents", len(docs))
        return docs

    except Exception as exc:
        logger.error("Error querying documents: %s", exc)
        logger.exception("Full traceback:")
        raise Exception(f"Error querying documents: {exc}") from exc


def build_context(similar_docs: list[dict]):
    """Construye el bloque de contexto para el system prompt."""
    if not similar_docs:
        return None
    context = "Contexto relevante encontrado en la base de datos:\n\n"
    for index, doc in enumerate(similar_docs, 1):
        source = doc.get("source", "Fuente desconocida")
        context += f"{index}. Fuente: {source} (Similitud: {doc['similarity']:.2%})\n"
        context += f"{doc['content']}\n\n"
    return context
