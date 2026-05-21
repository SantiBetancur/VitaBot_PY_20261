import logging

from flask import Request

from http_utils import build_json_response
from routes import (
    handle_delete_session,
    handle_get_messages,
    handle_get_sessions,
    handle_post_message,
)

logger = logging.getLogger(__name__)


def handler(request: Request):
    path   = request.path
    method = request.method
    logger.info("Method: %s  Path: %s", method, path)

    # ── Health check ──────────────────────────────────────────────────────────
    if path in ("/", ""):
        return build_json_response(
            {"status": "success", "message": "Hello from VitaBot endpoint"}, 200
        )

    # ── Rutas ─────────────────────────────────────────────────────────────────
    try:
        if path == "/sessions" and method == "GET":
            return handle_get_sessions(request)

        if path == "/messages" and method == "GET":
            return handle_get_messages(request)

        if path == "/session" and method == "DELETE":
            return handle_delete_session(request)

        if path == "/message" and method == "POST":
            return handle_post_message(request)

    except Exception as exc:
        logger.error("Unhandled error on %s %s: %s", method, path, exc)
        return build_json_response({"status": "error", "message": str(exc)}, 500)

    return build_json_response(
        {"error": f"Ruta no encontrada: {path} [{method}]"}, 404
    )