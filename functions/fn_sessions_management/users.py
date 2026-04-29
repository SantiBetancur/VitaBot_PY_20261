from supabase_client import select, insert
from helpers import build_response, validate_fields


def get_user_by_external_id(external_id):
    """
    Obtiene un usuario existente por su external_id (del Catalyst).
    
    Retorna:
        - Si existe: {"success": True, "code": 200, "data": {...}}
        - Si no existe: {"success": False, "code": 404, "error": "..."}
    """
    if not external_id:
        return build_response(False, 400, error="external_id es requerido")
    
    try:
        resultados = select(
            schema="app",
            table="users",
            filters={"external_id": f"eq.{external_id}"}
        )

        if resultados:
            usuario = resultados[0]
            return build_response(True, 200, data={
                "user_id": usuario["id"],
                "external_id": usuario["external_id"],
                "created_at": usuario.get("created_at")
            })
        else:
            return build_response(False, 404, error=f"Usuario con external_id '{external_id}' no encontrado")

    except Exception as e:
        return build_response(False, 500, error=f"Error consultando usuario: {str(e)}")


def get_or_create_user(data):
    """
    Obtiene un usuario si existe, si no lo crea.
    
    Parámetros:
        data: {"external_id": "..."}
    
    Retorna:
        {"success": True, "code": 200/201, "data": {"user_id": ..., "es_nuevo": True/False}}
    """
    is_valid, error_msg = validate_fields(data, ["external_id"])
    if not is_valid:
        return build_response(False, 400, error=error_msg)

    external_id = data.get("external_id")

    try:
        resultados = select(
            schema="app",
            table="users",
            filters={"external_id": f"eq.{external_id}"}
        )

        if resultados:
            usuario = resultados[0]
            return build_response(True, 200, data={
                "user_id": usuario["id"],
                "external_id": usuario["external_id"],
                "es_nuevo": False
            })
        else:
            nuevo = insert(
                schema="app",
                table="users",
                data={"external_id": external_id}
            )
            return build_response(True, 201, data={
                "user_id": nuevo["id"],
                "external_id": nuevo["external_id"],
                "es_nuevo": True
            })

    except Exception as e:
        return build_response(False, 500, error=str(e))