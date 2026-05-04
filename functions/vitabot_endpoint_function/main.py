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

load_dotenv()
logger = logging.getLogger(__name__)

SESSIONS_API_URL = "https://vitabotproject-920088613.development.catalystserverless.com/server/fn_sessions_management"

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-haiku-4-5"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "text-embedding-3-small"
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SUPABASE_URL = os.getenv("PROJECT_DB_URL")
SUPABASE_KEY = os.getenv("SECRET_DB_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("Supabase credentials not fully configured")
    logger.warning("PROJECT_DB_URL: %s", "SET" if SUPABASE_URL else "NOT SET")
    logger.warning("SECRET_DB_API_KEY: %s", "SET" if SUPABASE_KEY else "NOT SET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info("Supabase client initialized")

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


def call_sessions_api(method, path, data=None, request=None):
    url = f"{SESSIONS_API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    cookies = {}

    if request:
        # Extraer cookies del request original para autenticación
        cookie_header = request.headers.get("Cookie", "")
        if cookie_header:
            # Parsear cookies simples
            for cookie in cookie_header.split(";"):
                if "=" in cookie:
                    key, value = cookie.strip().split("=", 1)
                    cookies[key] = value

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data, cookies=cookies, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, cookies=cookies, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, cookies=cookies, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error calling {method} {url}: {str(e)}")
        raise Exception(f"Failed to call sessions API: {str(e)}")


def get_or_create_user(data, request):
    return call_sessions_api("POST", "/user", data, request)


def get_user_by_external_id(external_id, request):
    return call_sessions_api("GET", "/user", {"external_id": external_id}, request)


def create_session(data, request):
    return call_sessions_api("POST", "/session", data, request)


def get_session_by_id(session_id, user_id, request):
    return call_sessions_api("GET", "/session", {"session_id": session_id, "user_id": user_id}, request)


def update_session_activity(data, request):
    return call_sessions_api("PUT", "/session", data, request)


def get_messages(data, request):
    return call_sessions_api("GET", "/messages", data, request)


def save_messages(data, request):
    return call_sessions_api("POST", "/messages", data, request)


def get_user_sessions(user_id, request):
    return call_sessions_api("GET", "/sessions", {"user_id": user_id}, request)
APP_DOMAIN = "https://vitabotclientapp-ycwjmrpr.onslate.com"

def add_cors_headers(response, request_origin=None):
    allowed_origins = {
        "http://localhost:3001",
        "https://vitabotclientapp-ycwjmrpr.onslate.com",
    }
    allowed_origin = request_origin if request_origin in allowed_origins else "http://localhost:3001"

    response.headers["Access-Control-Allow-Origin"] = allowed_origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
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
        logger.info("Starting query to Supabase schema 'rag', table 'documents'")
        logger.info("Supabase URL: %s", SUPABASE_URL[:20] + "..." if SUPABASE_URL else "NOT SET")
        
        response = supabase.schema("rag").table("documents").select("id, content, embedding, source").execute()
        logger.info("Supabase response received successfully")

        if not response.data:
            logger.info("No documents found in database")
            return []

        user_embedding = np.array(embedding, dtype=np.float32)
        similarities = []

        for doc in response.data:
            if not doc.get("embedding"):
                logger.warning("Document ID %s has no embedding, skipping", doc.get("id"))
                continue

            try:
                doc_emb = doc["embedding"]
                if isinstance(doc_emb, str):
                    doc_emb = json.loads(doc_emb)

                doc_embedding = np.array(doc_emb, dtype=np.float32)
                similarity = cosine_similarity(user_embedding, doc_embedding)
                logger.debug("Document ID %s similarity: %.4f", doc["id"], similarity)

                if similarity >= MIN_SIMILARITY_THRESHOLD:
                    similarities.append({
                        "id": doc["id"],
                        "content": doc["content"],
                        "source": doc.get("source", "Fuente desconocida"),
                        "similarity": float(similarity)
                    })
            except Exception as doc_error:
                logger.warning("Error processing document %s: %s", doc.get("id"), str(doc_error))
                logger.exception("Full traceback for document error:")

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        logger.info("Returning %s similar documents out of %s total", len(similarities[:top_k]), len(similarities))
        return similarities[:top_k]

    except Exception as e:
        logger.error("Error querying documents: %s", str(e))
        logger.exception("Full traceback for query_similar_documents:")
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


def build_conversation_messages(session_id, user_message, request):
    conversation_messages = []

    if session_id:
        previous_messages_response = get_messages({"session_id": session_id}, request)
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

        BASE_ROLE = """Eres un experto en el lenguaje de scripting Deluge y el ecosistema Zoho (CRM, Desk, Creator, Cliq, Flow, etc.).
Tu misión principal es ayudar a los desarrolladores a escribir, corregir y entender código Deluge de forma precisa y completa.

Reglas generales:
- Responde siempre en el idioma del usuario.
- Cuando generes código: hazlo completo (nunca fragmentos sin contexto), con comentarios explicativos en línea, y usando nombres de variables/módulos realistas según la información provista (Para variables y estructura general del código puedes ser creativo siempre que NO INVENTES LA SINTAXIS DE DELUGE).
- Si el usuario da detalles de su entorno (nombre de módulos, campos, conexiones), úsalos directamente en el código; no uses placeholders genéricos como "YOUR_MODULE".
- Indica siempre si una función, método o comportamiento depende de una versión específica de Zoho o Deluge, o si puede variar entre productos Zoho (CRM vs Creator, por ejemplo).
- Ante ambigüedad técnica, pregunta lo mínimo necesario antes de generar código.
- Sé conciso en las explicaciones; prioriza el código funcional sobre la prosa."""


        system_message = BASE_ROLE
        if memory_only:
            system_message += """--- MODO: SOLO HISTORIAL ---
                    En este momento solo puedes responder usando el historial de esta conversación.
                    - Si hay fragmentos de código previos en el historial, mantenlos consistentes: no cambies nombres de variables, módulos ni estructuras ya definidas.
                    - Si la respuesta no aparece en el historial, indícalo claramente: "No tengo esa información en nuestra conversación."
                    - No uses conocimiento general, no extrapoles ni inventes funciones o parámetros."""
        elif context:
            system_message += """--- CONTEXTO DE DOCUMENTACIÓN OFICIAL ---
                        {context}
                        --- FIN DEL CONTEXTO ---

                        Instrucciones para usar el contexto:
                        1. El contexto anterior proviene de la documentación oficial de Zoho. Es tu fuente primaria y más confiable.
                        2. Usa también el historial de la conversación para mantener consistencia con lo ya desarrollado.
                        3. Jerarquía de fuentes: documentación oficial > historial de conversación > tu conocimiento interno.
                        4. Cuando generes código basado en el contexto:
                        - Usa exactamente los nombres de funciones, parámetros y sintaxis que aparecen en la documentación.
                        - Incorpora los datos reales que el usuario haya proporcionado (campos, módulos, conexiones).
                        - Genera el código completo, no solo el fragmento relevante.
                        5. Si el contexto menciona limitaciones, deprecaciones o diferencias por producto Zoho, adviértelo explícitamente al usuario.
                        6. Si la pregunta no puede responderse con el contexto ni con el historial, dilo claramente:
                        "No encontré información suficiente en la documentación disponible para responder esto con certeza."
                        No respondas con conocimiento general como sustituto de la documentación oficial."""

        payload = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "system": system_message,
            "messages": conversation_messages
        }

        response = requests.post(CLAUDE_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        bot_response = data["content"][0]["text"]

        if sources:
            formatted_sources = "\n".join(f"| `{source}` |" for source in sources)
            bot_response += (
                "\n\n## Fuentes utilizadas\n\n"
                "| Fuente |\n"
                "| --- |\n"
                f"{formatted_sources}"
            )

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


def resolve_optional_authenticated_user(app, request):
    try:
        auth_user = app.authentication().get_current_user()
    except Exception as exc:
        logger.warning("Error checking authentication: %s", str(exc))
        return None

    if not auth_user or not isinstance(auth_user, dict) or not auth_user.get("user_id"):
        return None

    external_id = auth_user["user_id"]
    user_response = get_user_by_external_id(external_id, request)
    if not user_response["success"] and user_response.get("code") == 404:
        user_response = get_or_create_user({"external_id": external_id}, request)

    if not user_response["success"]:
        logger.warning("Unable to resolve authenticated user: %s", user_response.get("error"))
        return None

    return {
        "external_id": external_id,
        "user_id": user_response["data"]["user_id"]
    }


def resolve_session(user_id, session_id, request):
    if session_id:
        session_response = get_session_by_id(session_id, user_id, request)
        if not session_response["success"]:
            raise Exception(session_response["error"])
        return session_id

    session_response = create_session({"user_id": user_id}, request)
    if not session_response["success"]:
        raise Exception(session_response["error"])

    return session_response["data"]["session_id"]


def persist_conversation(session_id, user_message, bot_response, sources, request):
    save_response = save_messages({
        "session_id": session_id,
        "user_content": user_message,
        "bot_content": bot_response,
        "sources": sources
    }, request)
    if not save_response["success"]:
        raise Exception(save_response["error"])

    activity_response = update_session_activity({"session_id": session_id}, request)
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

        user_info = resolve_optional_authenticated_user(app, request)
        if user_info:
            session_id = resolve_session(user_info["user_id"], requested_session_id, request)
            conversation_messages = build_conversation_messages(session_id, user_message, request)
        else:
            logger.info("Guest request received: no authenticated Catalyst user")
            session_id = None
            conversation_messages = build_conversation_messages(None, user_message, request)

        memory_question = is_memory_question(user_message)

        if user_info:
            logger.info("Received message from user %s", user_info["external_id"])
        else:
            logger.info("Received guest request without authenticated Catalyst user")

        logger.info("Generating embedding for user message")
        embedding = get_embedding(user_message)

        logger.info("Querying similar documents from database")
        try:
            similar_docs = query_similar_documents(embedding, top_k=3)
            logger.info("Found %s similar documents", len(similar_docs))
        except Exception as query_error:
            logger.error("Failed to query documents: %s", str(query_error))
            logger.exception("Full traceback for document query error:")
            similar_docs = []

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

        if user_info:
            persist_conversation(session_id, user_message, bot_response, sources, request)
            response_data.update({
                "session_id": session_id,
                "user_id": user_info["user_id"],
                "external_id": user_info["external_id"]
            })
        else:
            response_data.update({
                "session_id": None
            })

        return build_json_response(response_data, 200, request_origin=request_origin)

    except Exception as e:
        logger.error("Error processing message: %s", str(e))
        return build_json_response({
            "status": "error",
            "message": str(e)
        }, 500, request_origin=request_origin)
