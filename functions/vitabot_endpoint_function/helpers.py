# helpers.py
# Construye el response y verifica los campos


def build_response(success, code, data=None, message=None, error=None):
    """
    Construye el diccionario de respuesta estándar.

    Parámetros:
        success → True si todo fue bien, False si hubo error
        code    → código HTTP (200, 201, 400, 404, 500)
        data    → datos a retornar (solo en GETs exitosos)
        message → texto de confirmación (en operaciones exitosas sin data)
        error   → descripción del error (solo cuando success=False)

    Retorna un diccionario, por ejemplo:

        GET exitoso:
        {"success": True, "code": 200, "data": [...]}

        POST exitoso:
        {"success": True, "code": 201, "message": "Creado correctamente"}

        Error de validación:
        {"success": False, "code": 400, "error": "El campo X es requerido"}

        Error de servidor:
        {"success": False, "code": 500, "error": "Error en la DB: ..."}
    """
    response = {
        "success": success,
        "code":    code
    }
    if data    is not None: response["data"]    = data
    if message is not None: response["message"] = message
    if error   is not None: response["error"]   = error
    return response


def validate_fields(data, required_fields):
    """
    Verifica que los campos requeridos existan y no estén vacíos.

    Parámetros:
        data            → diccionario con los datos recibidos
        required_fields → lista de campos que deben existir

    Retorna:
        (True,  None)             → todo está bien, puede continuar
        (False, "mensaje de error") → falta algún campo

    Ejemplo:
        data = {"session_id": "abc", "user_content": "hola"}
        validate_fields(data, ["session_id", "user_content", "bot_content"])
        → (False, "El campo 'bot_content' es requerido")
        porque bot_content no está en data
    """
    for field in required_fields:
        value = data.get(field)
        if value is None or str(value).strip() == "":
            return False, f"El campo '{field}' es requerido"
    return True, None

    