import logging
from flask import Request, make_response, jsonify
import os
from dotenv import load_dotenv
import zcatalyst_sdk
import datetime
import json
import requests
from openai import OpenAI
from supabase import create_client, Client
import numpy as np

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
CLAUDE_MODEL = 'claude-haiku-4-5'
CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'

# OpenAI Config
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'text-embedding-3-small'
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Supabase Config
SUPABASE_URL = os.getenv('PROJECT_DB_URL')
SUPABASE_KEY = os.getenv('SECRET_DB_API_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# RAG Config
MIN_SIMILARITY_THRESHOLD = 0.3  # Umbral mínimo de similitud para considerar un documento relevante

def add_cors_headers(response):
    """Agregar headers CORS a todas las respuestas"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

def get_embedding(text):
    """
    Genera un embedding usando OpenAI para el texto proporcionado
    """
    try:
        response = openai_client.embeddings.create(
            model=OPENAI_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f'Error generating embedding: {str(e)}')

def cosine_similarity(a, b):
    """
    Calcula la similitud coseno entre dos vectores
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def query_similar_documents(embedding, top_k=3):
    """
    Consulta Supabase para encontrar documentos similares basados en embeddings
    Usa similitud coseno para encontrar los top_k documentos más relevantes
    Solo devuelve documentos que superan el umbral de similitud mínima
    """
    try:
        # Consultar todos los documentos de la tabla 'documents' en el schema 'rag'
        response = supabase.schema('rag').table('documents').select('id, content, embedding, source').execute()
        
        if not response.data:
            return []
        
        # Convertir el embedding de entrada a array de floats
        user_embedding = np.array(embedding, dtype=np.float32)
        
        # Calcular similitud coseno con cada documento
        similarities = []
        for doc in response.data:
            if doc.get('embedding'):
                try:
                    # Si el embedding es string, parsearlo como JSON
                    doc_emb = doc['embedding']
                    if isinstance(doc_emb, str):
                        doc_emb = json.loads(doc_emb)
                    
                    # Convertir a array de floats
                    doc_embedding = np.array(doc_emb, dtype=np.float32)
                    
                    similarity = cosine_similarity(user_embedding, doc_embedding)
                    logger.info(f"Document ID {doc['id']} similarity: {similarity:.4f}")
                    
                    # Solo incluir si supera el umbral mínimo
                    if similarity >= MIN_SIMILARITY_THRESHOLD:
                        similarities.append({
                            'id': doc['id'],
                            'content': doc['content'],
                            'source': doc.get('source', 'Fuente desconocida'),
                            'similarity': float(similarity)
                        })
                except Exception as doc_error:
                    # Si hay error con este documento, skiparlo
                    logger = logging.getLogger()
                    logger.warning(f'Error processing document {doc.get("id")}: {str(doc_error)}')
                    continue
        
        # Ordenar por similitud y devolver top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    except Exception as e:
        raise Exception(f'Error querying documents: {str(e)}')

def build_context(similar_docs):
    """
    Construye un string de contexto a partir de los documentos similares
    Incluye las fuentes (sources) de los documentos
    """
    if not similar_docs:
        return None
    
    context = "Contexto relevante encontrado en la base de datos:\n\n"
    for i, doc in enumerate(similar_docs, 1):
        source = doc.get('source', 'Fuente desconocida')
        context += f"{i}. Fuente: {source} (Similitud: {doc['similarity']:.2%})\n"
        context += f"{doc['content']}\n\n"
    
    return context

def call_claude_api(user_message, context=None, sources=None):
    """
    Llama a la API de Claude Haiku 4.5 y retorna la respuesta con sources
    Si se proporciona contexto, lo incluye en el prompt del sistema
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
        }
        
        # Construir sistema con contexto si está disponible
        system_message = 'Eres un asistente amable, conciso y útil. Responde siempre en el idioma del usuario.'
        if context:
            system_message += f'\n\n{context}'
            system_message += '\n\nResponde basándote en la información del contexto proporcionado.'
        
        payload = {
            'model': CLAUDE_MODEL,
            'max_tokens': 1024,
            'system': system_message,
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
        
        # Agregar referencias a las fuentes si están disponibles
        if sources:
            bot_response += f"\n\n **Fuentes utilizadas:** {', '.join(sources)}"
        
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
            
            # ─── RAG Pipeline ─────────────────────────────────────────────
            # 1. Generar embedding del mensaje del usuario
            logger.info('Generating embedding for user message...')
            embedding = get_embedding(user_message)
            
            # 2. Consultar documentos similares en Supabase
            logger.info('Querying similar documents from database...')
            similar_docs = query_similar_documents(embedding, top_k=3)
            logger.info(f'Found {len(similar_docs)} similar documents')
            
            # 3. Verificar si hay documentos suficientemente relevantes
            if not similar_docs:
                # No hay información en la base de datos
                bot_response = "Lo siento, no tengo información suficiente en mi base de datos para responder tu pregunta. Intenta reformular tu pregunta o consulta sobre temas relacionados con mis documentos disponibles."
                
                response_data = {
                    'status': 'success',
                    'message': 'No relevant documents found',
                    'userMessage': user_message,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'botResponse': bot_response,
                    'context_docs_count': 0,
                    'has_context': False
                }
            else:
                # Hay documentos relevantes
                # 3. Construir contexto
                context = build_context(similar_docs)
                
                # Extraer los sources únicos
                sources = list(set([doc.get('source', 'Fuente desconocida') for doc in similar_docs]))
                
                # 4. Llamar a Claude con el contexto
                logger.info('Calling Claude API with context...')
                bot_response = call_claude_api(user_message, context=context, sources=sources)
                
                response_data = {
                    'status': 'success',
                    'message': 'Message processed successfully',
                    'userMessage': user_message,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'botResponse': bot_response,
                    'context_docs_count': len(similar_docs),
                    'sources': sources,
                    'has_context': True
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
