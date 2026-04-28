from supabase_client import select, insert
from helpers import build_response, validate_fields
 
 
def get_messages(data):
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
 
 
def save_messages(data):
    required = ["session_id", "user_content", "bot_content"]
    is_valid, error_msg = validate_fields(data, required)
    if not is_valid:
        return build_response(False, 400, error=error_msg)
 
    session_id   = data.get("session_id")
    user_content = data.get("user_content")
    bot_content  = data.get("bot_content")
    sources      = data.get("sources", [])
 
    try:
        insert(
            schema="app",
            table="messages",
            data={
                "session_id": session_id,
                "role":       "user",
                "content":    user_content,
                "sources":    None
            }
        )
 
        insert(
            schema="app",
            table="messages",
            data={
                "session_id": session_id,
                "role":       "assistant",
                "content":    bot_content,
                "sources":    sources
            }
        )
 
        return build_response(True, 201, message="Mensajes guardados correctamente")
 
    except Exception as e:
        return build_response(False, 500, error=f"Error guardando mensajes: {str(e)}")