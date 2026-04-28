import logging
from flask import Request, make_response, jsonify
import zcatalyst_sdk

from users import get_or_create_user
from sessions import create_session, update_session_activity, delete_session
from messages import get_messages, save_messages


def handler(request: Request):
    app = zcatalyst_sdk.initialize()
    logger = logging.getLogger()

    try:
        data = request.get_json() if request.is_json else {}

        method = request.method
        path = request.path

        # =====================================================
        #  AUTENTICACIÓN CATALYST 
        # =====================================================
        try:
            auth_user = app.authentication().get_current_user()
            external_id = auth_user["user_id"]
        except Exception:
            return make_response(jsonify({
                "success": False,
                "code": 401,
                "error": "Usuario no autenticado en Catalyst"
            }), 401)

        
       
        
        if path == "/" and method == "GET":
            return make_response(jsonify({
                "status": "success",
                "message": "VitaBot API running"
            }), 200)

        # =====================================================
        # USUARIOS
        # =====================================================

        if path == "/user" and method == "POST":
            # 🔥 AQUÍ YA USAS EL USUARIO REAL
            data["external_id"] = external_id

            return make_response(
                jsonify(get_or_create_user(data)),
                200
            )

        # =====================================================
        # SESIONES
        # =====================================================

        if path == "/session" and method == "POST":
            return make_response(jsonify(create_session(data)), 200)

        if path == "/session" and method == "PUT":
            return make_response(jsonify(update_session_activity(data)), 200)

        if path == "/session" and method == "DELETE":
            return make_response(jsonify(delete_session(data)), 200)

        # =====================================================
        # MENSAJES
        # =====================================================

        if path == "/messages" and method == "GET":
            return make_response(jsonify(get_messages(data)), 200)

        if path == "/messages" and method == "POST":
            return make_response(jsonify(save_messages(data)), 200)

        # =====================================================
        # ERROR
        # =====================================================
        return make_response(jsonify({
            "success": False,
            "code": 404,
            "error": f"Ruta no encontrada: {path} [{method}]"
        }), 404)

    except Exception as e:
        logger.error(str(e))
        return make_response(jsonify({
            "success": False,
            "code": 500,
            "error": str(e)
        }), 500)

        