"""
Servicio de IA con OpenAI GPT-4o-mini + Knowledge Base
"""

import os
import logging
from typing import Dict, Optional, List
from openai import OpenAI
from config.database import get_supabase

logger = logging.getLogger(__name__)

class AIService:
    """Maneja chat IA con OpenAI + búsqueda en Knowledge Base"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no encontrada en .env")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.threshold = float(os.getenv("CHAT_CONFIDENCE_THRESHOLD", "0.8"))
        self.supabase = get_supabase()
        
        logger.info(f"✅ AIService inicializado con modelo {self.model}")
    
    def search_kb(self, query: str) -> Optional[Dict]:
        """
        Busca en Knowledge Base usando búsqueda por palabras clave
        
        Args:
            query: Pregunta del usuario
            
        Returns:
            Dict con respuesta encontrada o None
        """
        try:
            query_lower = query.lower()
            
            # Obtener todas las entradas activas de KB
            response = self.supabase.table("knowledge_base")\
                .select("*")\
                .eq("activa", True)\
                .execute()
            
            kb_entries = response.data
            
            if not kb_entries:
                logger.warning("⚠️ Knowledge Base vacía")
                return None
            
            # Buscar coincidencias por palabras clave
            best_match = None
            best_score = 0
            
            for entry in kb_entries:
                score = 0
                palabras_clave = entry.get('palabras_clave', [])
                
                # Contar palabras clave encontradas
                for keyword in palabras_clave:
                    if keyword.lower() in query_lower:
                        score += 1
                
                # También revisar pregunta directa
                if entry['pregunta'].lower() in query_lower or query_lower in entry['pregunta'].lower():
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_match = entry
            
            # Si encontramos match con suficiente confianza
            if best_match and best_score >= 1:
                # Actualizar contador
                kb_id = best_match['kb_id']
                self.supabase.table("knowledge_base")\
                    .update({"veces_usado": best_match['veces_usado'] + 1})\
                    .eq("kb_id", kb_id)\
                    .execute()
                
                logger.info(f"✅ Respuesta KB encontrada: {kb_id} (score: {best_score})")
                return {
                    "respuesta": best_match['respuesta'],
                    "confianza": min(best_match.get('confianza', 0.8), 1.0),
                    "fuente": "kb",
                    "kb_id": kb_id
                }
            
            logger.info(f"❌ No se encontró respuesta en KB para: '{query}'")
            return None
            
        except Exception as e:
            logger.error(f"Error buscando en KB: {e}")
            return None
    
    def ask_openai(self, query: str, chat_history: List[Dict] = None) -> Dict:
        """
        Consulta a OpenAI GPT-4o-mini con contexto del negocio
        
        Args:
            query: Pregunta del usuario
            chat_history: Historial de conversación (últimos mensajes)
            
        Returns:
            Dict con respuesta y confianza
        """
        try:
            # Obtener productos reales de la BD
            try:
                from config.database import db
                products = db.get_all_products()
                
                products_text = "NUESTROS PRODUCTOS DISPONIBLES (USAR SOLO ESTOS):\n"
                if products:
                    for p in products:
                        products_text += f"- {p.get('nombre')} (${p.get('precio', 0):,.0f}): {p.get('descripcion', '')}\n"
                else:
                    products_text += "No hay productos disponibles en este momento.\n"
                    
            except Exception as e:
                logger.error(f"Error obteniendo productos para prompt: {e}")
                products_text = "Error cargando lista de productos. Por favor sugiere ver el menú."

            # Contexto del negocio (System message)
            system_message = f"""Eres un asistente virtual de **Milhoja Dres**.
INFORMACIÓN CLAVE:
{products_text}

TU OBJETIVO:
1. Responder amablemente al usuario.
2. DETECTAR INTENCIÓN DE COMPRA. Si el usuario dice "quiero 12", ASUME que son 12 UNIDADES del producto. NO corrijas sobre "porciones" a menos que sea algo ilógico (ej. 0.5 milhojas).
3. FACILITAR LA COMPRA. Siempre muestra el botón de compra si hay una intención clara.

FORMATO DE RESPUESTA (JSON OBLIGATORIO):
Debes responder SIEMPRE con un objeto JSON válido con esta estructura:
{{
  "response": "Tu respuesta amable en texto plano aquí. Si piden 12 milhojas, confirma el precio total (12 * precio unitario) y diles que pueden agregarlas abajo.",
  "intent": "purchase" | "info" | "greeting" | "other",
  "suggested_products": [
    {{
      "product_id": 123,
      "name": "Nombre exacto del producto",
      "quantity": 12,  # Cantidad que el usuario pidió
      "price": 15000
    }}
  ]
}}

REGLAS DE NEGOCIO:
- "Caja" o "Unidad" usualmente se refieren a 1 item del inventario.
- Si el usuario pide "12 milhojas", son 12 items (product_id=...). NO las dividas por 6.
- Pedidos B2B: Aceptamos cantidades grandes.
- NO inventes productos. Si no existe, explica que no lo vendemos.
"""

            # Construir mensajes
            messages = [{"role": "system", "content": system_message}]
            
            # Agregar historial si existe
            if chat_history and len(chat_history) > 0:
                for msg in chat_history[-6:]:
                    try:
                        # Intentar parsear si el historial previo era JSON (para contexto)
                        content = msg['content']
                         # Si es output del asst y parece json, extraer solo la parte de texto para contexto
                        if msg['role'] == 'assistant' and content.strip().startswith('{'):
                             import json
                             try:
                                 data = json.loads(content)
                                 content = data.get('response', content)
                             except:
                                 pass
                        
                        messages.append({
                            "role": msg['role'],
                            "content": content
                        })
                    except:
                        pass
            
            # Agregar pregunta actual
            messages.append({"role": "user", "content": query})
            
            # Llamar a OpenAI con JSON Mode
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=0.9,
                response_format={ "type": "json_object" }
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Parsear JSON
            import json
            try:
                parsed_response = json.loads(response_content)
                respuesta_texto = parsed_response.get('response', 'Lo siento, no pude procesar la respuesta.')
                intent = parsed_response.get('intent', 'info')
                suggestions = parsed_response.get('suggested_products', [])
            except Exception as e:
                logger.error(f"Error parsing AI JSON: {e}")
                respuesta_texto = response_content
                intent = 'info'
                suggestions = []
            
            # Calcular confianza (simplificado)
            confianza = 0.9 if intent == 'purchase' else 0.8
            
            logger.info(f"✅ Respuesta OpenAI: Intent={intent}, Sugerencias={len(suggestions)}")
            
            return {
                "respuesta": respuesta_texto,
                "intent": intent,
                "suggested_products": suggestions,
                "confianza": confianza,
                "fuente": "openai",
                "raw_json": parsed_response if 'parsed_response' in locals() else {}
            }
            
        except Exception as e:
            logger.error(f"❌ Error consultando OpenAI: {e}")
            return {
                "respuesta": "Disculpa, tengo problemas técnicos en este momento. Por favor contacta vía WhatsApp al 3014170313.",
                "confianza": 0.3,
                "fuente": "error",
                "tokens_usados": 0
            }
    
    def get_response(self, query: str, user_id: int, chat_history: List[Dict] = None) -> Dict:
        """
        Obtiene respuesta: primero KB, luego OpenAI
        
        Args:
            query: Pregunta del usuario
            user_id: ID del usuario
            chat_history: Historial de chat
            
        Returns:
            Dict con respuesta, confianza y metadata
        """
        logger.info(f"Usuario {user_id} pregunta: '{query}'")
        
        # 1. Intentar Knowledge Base primero
        kb_response = self.search_kb(query)
        if kb_response:
            logger.info(f"✅ Respuesta desde KB (confianza: {kb_response['confianza']})")
            return kb_response
        
        # 2. Si no hay match en KB, usar OpenAI
        openai_response = self.ask_openai(query, chat_history)
        logger.info(f"✅ Respuesta desde OpenAI (confianza: {openai_response['confianza']})")
        
        return openai_response
