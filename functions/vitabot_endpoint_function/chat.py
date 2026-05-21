import logging

from config import MAX_CONVERSATION_MESSAGES
from messages import get_messages
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

MEMORY_QUESTION_MARKERS = (
    "que te dije",
    "qué te dije",
    "que te pregunte",
    "que te pregunté",
    "qué te pregunté",
    "que pregunté al iniciar",
    "qué te pregunté al iniciar",
    "recuerdas",
    "te acuerdas",
    "historial del chat",
    "inicio del chat",
    "mensaje anterior",
    "mensajes anteriores",
    "what did i ask",
    "what did i say",
    "do you remember",
    "earlier in this chat",
    "previous message",
)


def is_memory_question(user_message: str) -> bool:
    normalized = (user_message or "").strip().lower()
    return any(marker in normalized for marker in MEMORY_QUESTION_MARKERS)


def build_conversation_messages(
    session_id: Optional[str],
    user_message: str,
    chat_history: List[Dict] = None,
) -> List[Dict]:
    """
    Construye la lista de mensajes para enviar a Claude, incluyendo
    el historial previo de la sesión (o el chat_history del cliente invitado).
    """
    if session_id:
        previous_response = get_messages({"session_id": session_id})
        if not previous_response["success"]:
            raise Exception(previous_response["error"])
        previous_messages = previous_response.get("data", [])
    elif chat_history:
        previous_messages = chat_history
    else:
        previous_messages = []

    trimmed = previous_messages[-MAX_CONVERSATION_MESSAGES:]

    conversation = []
    for msg in trimmed:
        role    = msg.get("role")
        content = (msg.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        conversation.append({"role": role, "content": content})

    conversation.append({"role": "user", "content": user_message})
    logger.info("Conversation sent to AI: %s", conversation)
    return conversation
