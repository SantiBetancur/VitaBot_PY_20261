import datetime
import logging

from flask import Request

from auth import resolve_optional_authenticated_user
from chat import build_conversation_messages, is_memory_question
from http_utils import build_json_response, parse_request_data
from messages import get_messages, save_messages
from rag import build_context, get_embedding, query_similar_documents
from ai import call_claude_api
from sessions import (
    create_session,
    delete_session,
    get_session_by_id,
    get_user_sessions,
    update_session_activity,
)
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


# ── /sessions GET ─────────────────────────────────────────────────────────────

def handle_get_sessions(request: Request):
    user_info = resolve_optional_authenticated_user(request)
    if not user_info:
        return build_json_response({"error": "Unauthorized"}, 401)
    result = get_user_sessions(user_info["user_id"])
    return build_json_response(result, result.get("code", 200))


# ── /messages GET ─────────────────────────────────────────────────────────────

def handle_get_messages(request: Request):
    user_info = resolve_optional_authenticated_user(request)
    if not user_info:
        return build_json_response({"error": "Unauthorized"}, 401)
    session_id = request.args.get("session_id")
    if not session_id:
        return build_json_response({"error": "session_id is required"}, 400)
    result = get_messages({"session_id": session_id})
    return build_json_response(result, result.get("code", 200))


# ── /session DELETE ───────────────────────────────────────────────────────────

def handle_delete_session(request: Request):
    user_info = resolve_optional_authenticated_user(request)
    if not user_info:
        return build_json_response({"error": "Unauthorized"}, 401)
    session_id = request.args.get("session_id")
    if not session_id:
        return build_json_response({"error": "session_id is required"}, 400)
    result = delete_session({"session_id": session_id, "user_id": user_info["user_id"]})
    return build_json_response(result, result.get("code", 200))


# ── /message POST ─────────────────────────────────────────────────────────────

def _resolve_session(user_id: str, session_id: Optional[str]) -> str:
    if session_id:
        resp = get_session_by_id(session_id, user_id)
        if not resp["success"]:
            raise Exception(resp["error"])
        return session_id

    resp = create_session({"user_id": user_id})
    if not resp["success"]:
        raise Exception(resp["error"])
    return resp["data"]["session_id"]


def _persist_conversation(session_id: str, user_message: str, bot_response: str, sources: list):
    save_resp = save_messages({
        "session_id":   session_id,
        "user_content": user_message,
        "bot_content":  bot_response,
        "sources":      sources,
    })
    if not save_resp["success"]:
        raise Exception(save_resp["error"])

    activity_resp = update_session_activity({"session_id": session_id})
    if not activity_resp["success"]:
        raise Exception(activity_resp["error"])


def handle_post_message(request: Request):
    data              = parse_request_data(request)
    user_message      = (data.get("message") or "").strip()
    requested_session = data.get("session_id")
    chat_history      = data.get("chat_history")

    if not user_message:
        return build_json_response({"status": "error", "message": "Message cannot be empty"}, 400)

    user_info = resolve_optional_authenticated_user(request)

    if user_info:
        session_id            = _resolve_session(user_info["user_id"], requested_session)
        conversation_messages = build_conversation_messages(session_id, user_message)
        logger.info("Received message from user %s", user_info["external_id"])
    else:
        session_id            = None
        conversation_messages = build_conversation_messages(None, user_message, chat_history=chat_history)
        logger.info("Guest request — no authenticated Catalyst user")

    memory_question = is_memory_question(user_message)

    logger.info("Generating embedding for user message")
    embedding = get_embedding(user_message)

    logger.info("Querying similar documents")
    try:
        similar_docs = query_similar_documents(embedding, top_k=3)
        logger.info("Found %s similar documents", len(similar_docs))
    except Exception as exc:
        logger.error("Failed to query documents: %s", exc)
        similar_docs = []

    context = build_context(similar_docs) if similar_docs else None
    sources = list({doc.get("source", "Fuente desconocida") for doc in similar_docs})

    if similar_docs:
        logger.info("Calling Claude with %s context documents", len(similar_docs))
        bot_response    = call_claude_api(conversation_messages, context=context, sources=sources)
        response_message = "Message processed successfully"
    elif memory_question:
        logger.info("Calling Claude in memory-only mode")
        bot_response    = call_claude_api(conversation_messages, memory_only=True)
        response_message = "Message processed from conversation memory"
    else:
        bot_response    = (
            "Lo siento, no tengo información suficiente para responder eso. "
            "Solo puedo responder con base en el historial de esta conversación "
            "o en los documentos disponibles."
        )
        response_message = "Insufficient information outside allowed sources"

    response_data = {
        "status":             "success",
        "message":            response_message,
        "userMessage":        user_message,
        "timestamp":          datetime.datetime.now().isoformat(),
        "botResponse":        bot_response,
        "context_docs_count": len(similar_docs),
        "sources":            sources,
        "has_context":        bool(similar_docs),
    }

    if user_info:
        _persist_conversation(session_id, user_message, bot_response, sources)
        response_data.update({
            "session_id":  session_id,
            "user_id":     user_info["user_id"],
            "external_id": user_info["external_id"],
        })
    else:
        response_data["session_id"] = None

    return build_json_response(response_data, 200)
