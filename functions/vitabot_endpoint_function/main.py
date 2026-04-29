import datetime
import json
import logging
import os
import sys

from flask import Request, make_response, jsonify
from dotenv import load_dotenv
import numpy as np
import requests
import zcatalyst_sdk
from openai import OpenAI
from supabase import create_client, Client

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_MANAGEMENT_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "..", "fn_sessions_management"))
if SESSIONS_MANAGEMENT_DIR not in sys.path:
    sys.path.append(SESSIONS_MANAGEMENT_DIR)

from users import get_or_create_user
from sessions import create_session, get_session_by_id, update_session_activity
from messages import get_messages, save_messages

load_dotenv()

logger = logging.getLogger(__name__)

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-haiku-4-5"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "text-embedding-3-small"
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SUPABASE_URL = os.getenv("PROJECT_DB_URL")
SUPABASE_KEY = os.getenv("SECRET_DB_API_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

MIN_SIMILARITY_THRESHOLD = 0.3
MAX_CONVERSATION_MESSAGES = 5
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


def add_cors_headers(response, request_origin=None):
    allowed_origin = request_origin or "http://localhost:3001"
    response.headers["Access-Control-Allow-Origin"] = allowed_origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "3600"
    response.headers["Vary"] = "Origin"
    return response


def build_json_response(payload, status_code, request_origin=None):
    response = make_response(jsonify(payload), status_code)
    return add_cors_headers(response, request_origin=request_origin)


def parse_request_data(request: Request):
    if request.is_json:
        return request.get_json(silent=True) or {}

    raw_body = request.get_data(as_text=True)
    if not raw_body:
        return {}

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON body: {str(exc)}")


def get_embedding(text):
    try:
        response = openai_client.embeddings.create(
            model=OPENAI_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Error generating embedding: {str(e)}")


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def query_similar_documents(embedding, top_k=3):
    try:
        response = supabase.schema("rag").table("documents").select("id, content, embedding, source").execute()

        if not response.data:
            return []

        user_embedding = np.array(embedding, dtype=np.float32)
        similarities = []

        for doc in response.data:
            if not doc.get("embedding"):
                continue

            try:
                doc_emb = doc["embedding"]
                if isinstance(doc_emb, str):
                    doc_emb = json.loads(doc_emb)

                doc_embedding = np.array(doc_emb, dtype=np.float32)
                similarity = cosine_similarity(user_embedding, doc_embedding)
                logger.info("Document ID %s similarity: %.4f", doc["id"], similarity)

                if similarity >= MIN_SIMILARITY_THRESHOLD:
                    similarities.append({
                        "id": doc["id"],
                        "content": doc["content"],
                        "source": doc.get("source", "Fuente desconocida"),
                        "similarity": float(similarity)
                    })
            except Exception as doc_error:
                logger.warning("Error processing document %s: %s", doc.get("id"), str(doc_error))

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    except Exception as e:
        raise Exception(f"Error querying documents: {str(e)}")


def build_context(similar_docs):
    if not similar_docs:
        return None

    context = "Contexto relevante encontrado en la base de datos:\n\n"
    for index, doc in enumerate(similar_docs, 1):
        source = doc.get("source", "Fuente desconocida")
        context += f"{index}. Fuente: {source} (Similitud: {doc['similarity']:.2%})\n"
        context += f"{doc['content']}\n\n"

    return context


def is_memory_question(user_message):
    normalized_message = (user_message or "").strip().lower()
    return any(marker in normalized_message for marker in MEMORY_QUESTION_MARKERS)


def build_conversation_messages(session_id, user_message):
    conversation_messages = []

    if session_id:
        previous_messages_response = get_messages({"session_id": session_id})
        if not previous_messages_response["success"]:
            raise Exception(previous_messages_response["error"])

        previous_messages = previous_messages_response.get("data", [])
        trimmed_messages = previous_messages[-MAX_CONVERSATION_MESSAGES:]

        for message in trimmed_messages:
            role = message.get("role")
            content = (message.get("content") or "").strip()
            if role not in {"user", "assistant"} or not content:
                continue

            conversation_messages.append({
                "role": role,
                "content": content
            })

    conversation_messages.append({
        "role": "user",
        "content": user_message
    })

    return conversation_messages


def call_claude_api(conversation_messages, context=None, sources=None, memory_only=False):
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }

        system_message = "Eres un asistente amable, conciso y util. Responde siempre en el idioma del usuario."
        if memory_only:
            system_message += (
                "\n\nSolo puedes responder usando el historial de esta conversacion."
                "\nSi la respuesta no aparece en el historial, di que no la sabes."
                "\nNo uses conocimiento general ni inventes informacion."
            )
        elif context:
            system_message += f"\n\n{context}"
            system_message += "\n\nResponde basandote en la informacion del contexto proporcionado."
            system_message += (
                "\nUsa tambien el historial de la conversacion si ayuda."
                "\nSi la pregunta no se puede responder con el historial o con el contexto proporcionado,"
                " di claramente que no tienes informacion suficiente."
                "\nNo respondas con conocimiento general fuera de esas fuentes."
            )

        payload = {
            "model": CLAUDE_MODEL,
            "max_tokens": 1024,
            "system": system_message,
            "messages": conversation_messages
        }

        response = requests.post(CLAUDE_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        bot_response = data["content"][0]["text"]

        if sources:
            bot_response += f"\n\nFuentes utilizadas: {', '.join(sources)}"

        return bot_response

    except Exception as e:
        raise Exception(f"Error calling Claude API: {str(e)}")


def resolve_authenticated_user(app):
    auth_user = app.authentication().get_current_user()
    if not auth_user:
        raise Exception("Catalyst no devolvio un usuario autenticado")
    if not isinstance(auth_user, dict):
        raise Exception(f"Respuesta de autenticacion inesperada: {type(auth_user).__name__}")
    if not auth_user.get("user_id"):
        raise Exception(f"Usuario autenticado sin user_id: {auth_user}")

    external_id = auth_user["user_id"]

    user_response = get_or_create_user({"external_id": external_id})
    if not user_response["success"]:
        raise Exception(user_response["error"])

    return {
        "external_id": external_id,
        "user_id": user_response["data"]["user_id"]
    }


def resolve_session(user_id, session_id):
    if session_id:
        session_response = get_session_by_id(session_id, user_id)
        if not session_response["success"]:
            raise Exception(session_response["error"])
        return session_id

    session_response = create_session({"user_id": user_id})
    if not session_response["success"]:
        raise Exception(session_response["error"])

    return session_response["data"]["session_id"]


def persist_conversation(session_id, user_message, bot_response, sources):
    save_response = save_messages({
        "session_id": session_id,
        "user_content": user_message,
        "bot_content": bot_response,
        "sources": sources
    })
    if not save_response["success"]:
        raise Exception(save_response["error"])

    activity_response = update_session_activity({"session_id": session_id})
    if not activity_response["success"]:
        raise Exception(activity_response["error"])


def handler(request: Request):
    app = zcatalyst_sdk.initialize()
    request_origin = request.headers.get("Origin")

    if request.method == "OPTIONS":
        return add_cors_headers(make_response("", 200), request_origin=request_origin)

    if request.path == "/" or request.path == "":
        return build_json_response({
            "status": "success",
            "message": "Hello from VitaBot endpoint"
        }, 200, request_origin=request_origin)

    if request.path == "/cache":
        try:
            default_segment = app.cache().segment()
            insert_resp = default_segment.put("Name", "DefaultName")
            logger.info("Inserted cache: %s", insert_resp)
            get_resp = default_segment.get("Name")
            return build_json_response(get_resp, 200, request_origin=request_origin)
        except Exception as e:
            logger.error("Cache error: %s", str(e))
            return build_json_response({"error": str(e)}, 500, request_origin=request_origin)

    if request.path != "/message" or request.method != "POST":
        return build_json_response({"error": "Unknown path"}, 400, request_origin=request_origin)

    try:
        data = parse_request_data(request)
        user_message = (data.get("message") or "").strip()
        requested_session_id = data.get("session_id")

        if not user_message:
            return build_json_response({
                "status": "error",
                "message": "Message cannot be empty"
            }, 400, request_origin=request_origin)

        try:
            user_info = resolve_authenticated_user(app)
        except Exception as auth_error:
            logger.error("Authentication error: %s", str(auth_error))
            return build_json_response({
                "status": "error",
                "message": "Usuario no autenticado en Catalyst"
            }, 401, request_origin=request_origin)

        session_id = resolve_session(user_info["user_id"], requested_session_id)
        conversation_messages = build_conversation_messages(session_id, user_message)
        memory_question = is_memory_question(user_message)

        logger.info("Received message from user %s", user_info["external_id"])
        logger.info("Generating embedding for user message")
        embedding = get_embedding(user_message)

        logger.info("Querying similar documents from database")
        similar_docs = query_similar_documents(embedding, top_k=3)
        logger.info("Found %s similar documents", len(similar_docs))

        context = build_context(similar_docs) if similar_docs else None
        sources = list(set(doc.get("source", "Fuente desconocida") for doc in similar_docs)) if similar_docs else []

        if similar_docs:
            logger.info("Calling Claude API with %s prior messages and %s context documents", len(conversation_messages) - 1, len(similar_docs))
            bot_response = call_claude_api(conversation_messages, context=context, sources=sources)
            response_message = "Message processed successfully"
        elif memory_question:
            logger.info("Calling Claude API in memory-only mode with %s prior messages", len(conversation_messages) - 1)
            bot_response = call_claude_api(conversation_messages, memory_only=True)
            response_message = "Message processed from conversation memory"
        else:
            bot_response = (
                "Lo siento, no tengo informacion suficiente para responder eso. "
                "Solo puedo responder con base en el historial de esta conversacion o en los documentos disponibles."
            )
            response_message = "Insufficient information outside allowed sources"

        response_data = {
            "status": "success",
            "message": response_message,
            "userMessage": user_message,
            "timestamp": datetime.datetime.now().isoformat(),
            "botResponse": bot_response,
            "context_docs_count": len(similar_docs),
            "sources": sources,
            "has_context": bool(similar_docs)
        }

        persist_conversation(session_id, user_message, bot_response, sources)

        response_data.update({
            "session_id": session_id,
            "user_id": user_info["user_id"],
            "external_id": user_info["external_id"]
        })

        return build_json_response(response_data, 200, request_origin=request_origin)

    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        return build_json_response({
            "status": "error",
            "message": str(e)
        }, 500, request_origin=request_origin)
