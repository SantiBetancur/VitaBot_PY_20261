import logging
from flask import Request, make_response, jsonify
import os
from dotenv import load_dotenv
import zcatalyst_sdk
import datetime
import json
import requests

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
CLAUDE_MODEL = 'claude-haiku-4-5'
CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'

def add_cors_headers(response):
    """Agregar headers CORS a todas las respuestas"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

def call_claude_api(user_message):
    """
    Llama a la API de Claude Haiku 4.5 y retorna la respuesta
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            'model': CLAUDE_MODEL,
            'max_tokens': 1024,
            'system': 'Eres un asistente amable, conciso y útil. Responde siempre en el idioma del usuario.',
            'messages': [
                {
                    'role': 'user',
                    'content': user_message
                }
            ]
        }
        
        response = requests.post(CLAUDE_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        # Extraer el texto de la respuesta
        bot_response = data['content'][0]['text']
        
        return bot_response
    
    except Exception as e:
        raise Exception(f'Error calling Claude API: {str(e)}')

def handler(request: Request):
    app = zcatalyst_sdk.initialize()
    logger = logging.getLogger()

    logger.info(os.getenv('CLAUDE_API_KEY'))

    # Manejar preflight CORS
    if request.method == "OPTIONS":
        response = make_response("", 200)
        return add_cors_headers(response)
    
    # Handle POST requests for messages
    if request.method == "POST":
        try:
            # Manejar tanto application/json como text/plain
            if request.content_type == 'text/plain':
                # Si es text/plain, parsear el body como JSON manualmente
                data = json.loads(request.get_data(as_text=True))
            else:
                # Si es application/json, usar get_json()
                data = request.get_json()
            
            user_message = data.get('message', '')
            
            if not user_message:
                response = make_response(jsonify({
                    'status': 'error',
                    'message': 'Message cannot be empty'
                }), 400)
                return add_cors_headers(response)
            
            logger.info(f'Received message from user: {user_message}')
            
            # Llamar a Claude API para obtener respuesta
            bot_response = call_claude_api(user_message)
            
            response_data = {
                'status': 'success',
                'message': 'Message processed successfully',
                'userMessage': user_message,
                'timestamp': datetime.datetime.now().isoformat(),
                'botResponse': bot_response
            }
            
            response = make_response(jsonify(response_data), 200)
            return add_cors_headers(response)
        
        except Exception as e:
            logger.error(f'Error processing message: {str(e)}')
            response = make_response(jsonify({
                'status': 'error',
                'message': str(e)
            }), 500)
            return add_cors_headers(response)
    
    # Handle GET requests
    if request.path == "/" or request.path == "":
        response = make_response(jsonify({
            'status': 'success',
            'message': 'Hello from VitaBot endpoint'
        }), 200)
        return add_cors_headers(response)
    
    elif request.path == "/cache":
        try:
            default_segment = app.cache().segment()
            insert_resp = default_segment.put('Name', 'DefaultName')
            logger.info('Inserted cache : ' + str(insert_resp))
            get_resp = default_segment.get('Name')
            response = make_response(jsonify(get_resp), 200)
            return add_cors_headers(response)
        except Exception as e:
            logger.error(f'Cache error: {str(e)}')
            response = make_response(jsonify({'error': str(e)}), 500)
            return add_cors_headers(response)
    
    else:
        response = make_response(jsonify({'error': 'Unknown path'}), 400)
        return add_cors_headers(response)
