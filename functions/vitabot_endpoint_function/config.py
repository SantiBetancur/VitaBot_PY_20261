import logging
import os

from openai import OpenAI

logger = logging.getLogger(__name__)

# ── Entorno ───────────────────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "development":
    APP_DOMAIN = os.getenv("APP_DOMAIN_DEV", "http://localhost:3001")
else:
    APP_DOMAIN = os.getenv("APP_DOMAIN_PRODUCTION")

# ── Claude ────────────────────────────────────────────────────────────────────
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL   = "claude-haiku-4-5"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# ── OpenAI embeddings ─────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL   = "text-embedding-3-small"
openai_client  = OpenAI(api_key=OPENAI_API_KEY)

# ── RAG tunables ──────────────────────────────────────────────────────────────
# La conexión a Supabase la gestiona supabase_client.py mediante la REST API.
MIN_SIMILARITY_THRESHOLD  = 0.3
MAX_CONVERSATION_MESSAGES = 5
