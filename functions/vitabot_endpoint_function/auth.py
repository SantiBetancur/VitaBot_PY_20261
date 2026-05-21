import logging

import zcatalyst_sdk
from flask import Request

from http_utils import parse_request_data
from users import get_or_create_user
logger = logging.getLogger(__name__)


def _verify_catalyst_user(user_id: str) -> dict:
    """
    Verifica que el user_id enviado por el cliente exista y esté activo en
    Catalyst, usando el SDK admin (scope="admin").

    - Si el user_id es válido → devuelve los datos del usuario de Catalyst.
    - Si no existe o está inactivo → lanza una excepción.

    Esto resuelve el problema de que el Web SDK autentique en el browser
    pero el backend no pueda leer esa sesión directamente: en su lugar,
    el backend consulta al propio Catalyst si ese ID es legítimo.
    """
    app  = zcatalyst_sdk.initialize(scope="admin")
    auth = app.authentication()

    # get_user_details() lanza excepción si el user_id no existe en el proyecto
    user_data = auth.get_user_details(str(user_id))

    if not user_data:
        raise ValueError(f"Catalyst no devolvió datos para user_id={user_id}")

    status = user_data.get("status", "").upper()
    if status != "ACTIVE":
        raise PermissionError(
            f"Usuario {user_id} no está activo en Catalyst (status={status})"
        )

    return user_data


def resolve_optional_authenticated_user(request: Request) :
    """
    Intenta autenticar al usuario a partir del parámetro `authenticated_user_id`
    que el Web SDK envía en cada petición.

    Flujo:
      1. Lee `authenticated_user_id` del request (query string o body JSON).
      2. Verifica contra Catalyst que ese ID existe y está activo.
      3. Busca o crea el usuario interno en la BD.
      4. Devuelve { external_id, user_id } o None si es modo invitado / falla.

    Por qué este enfoque:
      El Web SDK autentica al usuario en el browser con cookies de sesión Zoho.
      El backend SDK (scope="admin") no puede leer esa sesión directamente.
      En cambio, el SDK admin sí puede consultar cualquier usuario del proyecto,
      por lo que usamos get_user_details() como mecanismo de verificación:
      si Catalyst conoce ese user_id y está ACTIVE, la identidad es válida.
    """
    try:
        data    = parse_request_data(request)
        user_id = data.get("authenticated_user_id")
    except Exception as exc:
        logger.warning("Error leyendo authenticated_user_id del request: %s", exc)
        return None

    if not user_id:
        logger.debug("No authenticated_user_id en el request — modo invitado")
        return None

    try:
        _verify_catalyst_user(user_id)
    except PermissionError as exc:
        logger.warning("Usuario inactivo rechazado: %s", exc)
        return None
    except Exception as exc:
        logger.warning(
            "authenticated_user_id=%s no pudo verificarse en Catalyst: %s",
            user_id, exc
        )
        return None

    # El user_id de Catalyst es el external_id en nuestra BD
    external_id   = str(user_id)
    user_response = get_or_create_user({"external_id": external_id})

    if not user_response["success"]:
        logger.warning(
            "No se pudo resolver usuario interno para external_id=%s: %s",
            external_id, user_response.get("error")
        )
        return None

    return {
        "external_id": external_id,
        "user_id":     user_response["data"]["user_id"],
    }