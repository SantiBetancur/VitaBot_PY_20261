from supabase_client import select, insert, update, delete_record
from helpers import build_response, validate_fields


def create_session(data):
    is_valid, error_msg = validate_fields(data, ["user_id"])
    if not is_valid:
        return build_response(False, 400, error=error_msg)

    user_id = data.get("user_id")

    try:
        nueva = insert(
            schema="app",
            table="sessions",
            data={"user_id": user_id}
        )
        return build_response(True, 201, data={
            "session_id":    nueva["id"],
            "user_id":       nueva["user_id"],
            "created_at":    nueva["created_at"],
            "last_activity": nueva["last_activity"]
        })
    except Exception as e:
        return build_response(False, 500, error=f"Error creando sesión: {str(e)}")


def update_session_activity(data):
    is_valid, error_msg = validate_fields(data, ["session_id"])
    if not is_valid:
        return build_response(False, 400, error=error_msg)

    session_id = data.get("session_id")

    try:
        from datetime import datetime, timezone
        ahora = datetime.now(timezone.utc).isoformat()

        resultado = update(
            schema="app",
            table="sessions",
            filters={"id": f"eq.{session_id}"},
            data={"last_activity": ahora}
        )

        if not resultado:
            return build_response(False, 404,
                error=f"No se encontró sesión '{session_id}'"
            )

        return build_response(True, 200, message="Actividad actualizada")

    except Exception as e:
        return build_response(False, 500, error=f"Error actualizando sesión: {str(e)}")


def delete_session(data):
    is_valid, error_msg = validate_fields(data, ["session_id"])
    if not is_valid:
        return build_response(False, 400, error=error_msg)

    session_id = data.get("session_id")

    try:
        eliminado = delete_record(
            schema="app",
            table="sessions",
            filters={"id": f"eq.{session_id}"}
        )

        if not eliminado:
            return build_response(False, 404,
                error=f"No se encontró sesión '{session_id}'"
            )

        return build_response(True, 200, message="Sesión eliminada correctamente")

    except Exception as e:
        return build_response(False, 500, error=f"Error eliminando sesión: {str(e)}")