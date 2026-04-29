from supabase_client import select, insert
from helpers import build_response, validate_fields


def get_messages(data):
    """
    Obtiene todos los mensajes de una sesion especifica.
    """
    is_valid, error_msg = validate_fields(data, ["session_id"])
    if not is_valid:
        return build_response(False, 400, error=error_msg)

    session_id = data.get("session_id")

    try:
        mensajes = select(
            schema="app",
            table="messages",
            filters={"session_id": f"eq.{session_id}"},
            order="created_at"
        )
        return build_response(True, 200, data=mensajes)
    except Exception as e:
        return build_response(False, 500, error=f"Error recuperando mensajes: {str(e)}")


def get_user_messages(user_id):
    """
    Obtiene todo el historial de mensajes de un usuario usando sus sesiones.
    """
    if not user_id:
        return build_response(False, 400, error="user_id es requerido")

    try:
        sesiones = select(
            schema="app",
            table="sessions",
            filters={"user_id": f"eq.{user_id}"},
            order="created_at"
        )

        if not sesiones:
            return build_response(True, 200, data=[])

        session_ids = [sesion["id"] for sesion in sesiones if sesion.get("id")]
        if not session_ids:
            return build_response(True, 200, data=[])

        mensajes = select(
            schema="app",
            table="messages",
            filters={"session_id": f"in.({','.join(session_ids)})"},
            order="created_at"
        )
        return build_response(True, 200, data=mensajes)
    except Exception as e:
        return build_response(False, 500, error=f"Error recuperando historial: {str(e)}")


def save_messages(data):
    """
    Guarda un par de mensajes (usuario y bot) en una sesion.
    """
    required = ["session_id", "user_content", "bot_content"]
    is_valid, error_msg = validate_fields(data, required)
    if not is_valid:
        return build_response(False, 400, error=error_msg)

    session_id = data.get("session_id")
    user_content = data.get("user_content")
    bot_content = data.get("bot_content")
    sources = data.get("sources", [])

    try:
        insert(
            schema="app",
            table="messages",
            data={
                "session_id": session_id,
                "role": "user",
                "content": user_content,
                "sources": None
            }
        )

        insert(
            schema="app",
            table="messages",
            data={
                "session_id": session_id,
                "role": "assistant",
                "content": bot_content,
                "sources": sources
            }
        )

        return build_response(True, 201, message="Mensajes guardados correctamente")
    except Exception as e:
        return build_response(False, 500, error=f"Error guardando mensajes: {str(e)}")
