import os
import logging
import requests


logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("PROJECT_DB_URL")
SUPABASE_KEY = os.getenv("SECRET_DB_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Faltan variables de entorno: PROJECT_DB_URL o SECRET_DB_API_KEY")


BASE_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
    "Accept":        "application/json"
}


def build_headers(schema: str):
    """Construye headers con el schema especificado para Supabase REST API."""
    h = {
        **BASE_HEADERS,
        "Accept-Profile":  schema,
        "Content-Profile": schema
    }
    return h


def select(schema, table, filters=None, order=None):
    """
    SELECT: Obtiene registros de una tabla.
    
    Parámetros:
        schema: nombre del schema en Supabase (ej: "app")
        table: nombre de la tabla
        filters: dict con filtros, ej: {"user_id": "eq.123", "status": "eq.active"}
        order: campo por el cual ordenar, ordenará ASC por defecto
    
    Retorna:
        Lista de registros encontrados
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"

    if filters:
        for column, condition in filters.items():
            url += f"&{column}={condition}"

    if order:
        url += f"&order={order}.asc"

    headers = build_headers(schema)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en SELECT {table}: {str(e)}")
        logger.error(f"Response: {response.text if response else 'No response'}")
        raise


def insert(schema, table, data):
    """
    INSERT: Inserta un nuevo registro en una tabla.
    
    Parámetros:
        schema: nombre del schema en Supabase
        table: nombre de la tabla
        data: diccionario con los datos a insertar
    
    Retorna:
        El registro insertado (con IDs generados, timestamps, etc.)
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = build_headers(schema)

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en INSERT {table}: {str(e)}")
        logger.error(f"Datos: {data}")
        logger.error(f"Response: {response.text if response else 'No response'}")
        raise


def update(schema, table, filters, data):
    """
    UPDATE: Actualiza registros en una tabla.
    
    Parámetros:
        schema: nombre del schema en Supabase
        table: nombre de la tabla
        filters: dict con los filtros para identificar qué registros actualizar
        data: diccionario con los nuevos valores
    
    Retorna:
        El registro actualizado
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}?"
    filter_parts = [f"{col}={cond}" for col, cond in filters.items()]
    url += "&".join(filter_parts)

    headers = build_headers(schema)
    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result[0] if result else None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en UPDATE {table}: {str(e)}")
        logger.error(f"Filtros: {filters}, Datos: {data}")
        logger.error(f"Response: {response.text if response else 'No response'}")
        raise


def delete_record(schema, table, filters):
    """
    DELETE: Elimina registros de una tabla.
    
    Parámetros:
        schema: nombre del schema en Supabase
        table: nombre de la tabla
        filters: dict con los filtros para identificar qué registros eliminar
    
    Retorna:
        True si se eliminó algún registro, False en caso contrario
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}?"
    filter_parts = [f"{col}={cond}" for col, cond in filters.items()]
    url += "&".join(filter_parts)

    headers = build_headers(schema)
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        return len(result) > 0
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en DELETE {table}: {str(e)}")
        logger.error(f"Filtros: {filters}")
        logger.error(f"Response: {response.text if response else 'No response'}")
        raise