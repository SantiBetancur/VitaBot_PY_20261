from supabase_client import select, insert
from helpers import build_response, validate_fields

def get_or_create_user(data):
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
        