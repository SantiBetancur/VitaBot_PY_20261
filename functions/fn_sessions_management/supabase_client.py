import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


SUPABASE_URL = os.environ.get("PROJECT_DB_URL")
SUPABASE_KEY = os.environ.get("SECRET_DB_API_KEY")

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
    h = {
        **BASE_HEADERS,
        "Accept-Profile":  schema,
        "Content-Profile": schema
    }
    
    return h


def select(schema, table, filters=None, order=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"

    if filters:
        for column, condition in filters.items():
            url += f"&{column}={condition}"

    if order:
        url += f"&order={order}.asc"

    headers = build_headers(schema)
    response = requests.get(url, headers=headers)

    if not response.ok:
        print(" ERROR SELECT")
        print("   URL:", url)
        print("   Response:", response.text)

    response.raise_for_status()
    return response.json()


def insert(schema, table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = build_headers(schema)

    response = requests.post(url, headers=headers, json=data)

    if not response.ok:
        print(" ERROR INSERT")
        print("   URL:", url)
        print("   Payload:", data)
        print("   Response:", response.text)
        print("   Headers enviados:", {k: v for k, v in response.request.headers.items()
                                        if k in ("Accept-Profile", "Content-Profile", "apikey")})

    response.raise_for_status()
    result = response.json()
    return result[0] if result else None


def update(schema, table, filters, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}?"
    filter_parts = [f"{col}={cond}" for col, cond in filters.items()]
    url += "&".join(filter_parts)

    headers = build_headers(schema)
    response = requests.patch(url, headers=headers, json=data)

    if not response.ok:
        print(" ERROR UPDATE")
        print("   URL:", url)
        print("   Payload:", data)
        print("   Response:", response.text)

    response.raise_for_status()
    result = response.json()
    return result[0] if result else None


def delete_record(schema, table, filters):
    url = f"{SUPABASE_URL}/rest/v1/{table}?"
    filter_parts = [f"{col}={cond}" for col, cond in filters.items()]
    url += "&".join(filter_parts)

    headers = build_headers(schema)
    response = requests.delete(url, headers=headers)

    if not response.ok:
        print(" ERROR DELETE")
        print("   URL:", url)
        print("   Response:", response.text)

    response.raise_for_status()
    result = response.json()
    return len(result) > 0
    