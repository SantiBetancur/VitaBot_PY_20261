import logging
from flask import Request, make_response, jsonify
import zcatalyst_sdk

from users import get_or_create_user, get_user_by_external_id
from sessions import create_session, update_session_activity, delete_session, get_user_sessions
from messages import get_messages, save_messages, get_user_messages


def add_cors_headers(response, request_origin=None):
    allowed_origin = request_origin or "http://localhost:3001"
    response.headers["Access-Control-Allow-Origin"] = allowed_origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "3600"
    response.headers["Vary"] = "Origin"
    return response


def parse_request_data(request: Request):
    if request.method in ["GET", "DELETE"]:
        return request.args.to_dict()
    if request.is_json:
        return request.get_json(silent=True) or {}
    return {}


def respond(payload, request_origin=None):
    response = make_response(jsonify(payload), payload.get("code", 200))
    return add_cors_headers(response, request_origin=request_origin)


def handler(request: Request):
    request_origin = request.headers.get("Origin")

    if request.method == "OPTIONS":
        return add_cors_headers(make_response("", 200), request_origin=request_origin)

    app = zcatalyst_sdk.initialize()
    logger = logging.getLogger()

    try:
        data = parse_request_data(request)
        method = request.method
        path = request.path

        external_id = None
        db_user_id = None

        if not (path == "/" and method == "GET"):
            try:
                auth_user = app.authentication().get_current_user()
                if not auth_user or not auth_user.get("user_id"):
                    raise Exception("Catalyst no devolvio un usuario autenticado")
                external_id = auth_user["user_id"]

                user_response = get_user_by_external_id(external_id)
                if not user_response["success"] and user_response["code"] == 404:
                    user_response = get_or_create_user({"external_id": external_id})

                if user_response["success"]:
                    db_user_id = user_response["data"]["user_id"]
                else:
                    return respond(user_response, request_origin=request_origin)

            except Exception as e:
                logger.error(f"Error en autenticacion: {str(e)}")
                response = make_response(jsonify({
                    "success": False,
                    "code": 401,
                    "error": "Usuario no autenticado en Catalyst"
                }), 401)
                return add_cors_headers(response, request_origin=request_origin)

        if path == "/" and method == "GET":
            response = make_response(jsonify({
                "status": "success",
                "message": "VitaBot API running"
            }), 200)
            return add_cors_headers(response, request_origin=request_origin)

        if path == "/user/profile" and method == "GET":
            response = make_response(jsonify({
                "success": True,
                "code": 200,
                "data": {
                    "user_id": db_user_id,
                    "external_id": external_id
                }
            }), 200)
            return add_cors_headers(response, request_origin=request_origin)

        if path == "/session" and method == "POST":
            return respond(create_session({"user_id": db_user_id}), request_origin=request_origin)

        if path == "/session" and method == "PUT":
            return respond(update_session_activity(data), request_origin=request_origin)

        if path == "/session" and method == "DELETE":
            return respond(delete_session(data), request_origin=request_origin)

        if path == "/sessions" and method == "GET":
            return respond(get_user_sessions(db_user_id), request_origin=request_origin)

        if path == "/messages" and method == "GET":
            return respond(get_messages(data), request_origin=request_origin)

        if path == "/messages" and method == "POST":
            return respond(save_messages(data), request_origin=request_origin)

        if path == "/messages/history" and method == "GET":
            return respond(get_user_messages(db_user_id), request_origin=request_origin)

        response = make_response(jsonify({
            "success": False,
            "code": 404,
            "error": f"Ruta no encontrada: {path} [{method}]"
        }), 404)
        return add_cors_headers(response, request_origin=request_origin)

    except Exception as e:
        logger.error(str(e))
        response = make_response(jsonify({
            "success": False,
            "code": 500,
            "error": str(e)
        }), 500)
        return add_cors_headers(response, request_origin=request_origin)