import json

from flask import Request, make_response, jsonify


def parse_request_data(request: Request) -> dict:
    """Lee parámetros del request según el método HTTP."""
    if request.method in ("GET", "DELETE"):
        return request.args.to_dict()
    if request.is_json:
        return request.get_json(silent=True) or {}
    raw = request.get_data(as_text=True)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON body: {exc}") from exc


def build_json_response(payload: dict, status_code: int):
    """Construye una respuesta JSON con el código HTTP indicado."""
    return make_response(jsonify(payload), status_code)
