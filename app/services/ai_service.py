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
            # Contexto del negocio (System message)
            system_message = """Eres un asistente virtual de **Milhoja Dres**, una pastelería artesanal en Bogotá, Colombia.

INFORMACIÓN CLAVE:
- Productos: Milhojas artesanales, postres y bebidas
- Puntos de recogida:
  • Calle 96b #20d-70
  • Cra 81b #19b-80
- Horarios: Lunes a Viernes 8:00 AM - 6:00 PM, Sábados 9:00 AM - 5:00 PM, Domingos cerrado
- NO hacemos domicilios directos (el cliente puede enviar su domiciliario)
- Métodos de pago: Nequi, Daviplata (3014170313)
- Se requiere anticipo del 50% para pedidos grandes
- Pedidos grandes: 2 días de anticipación
- WhatsApp contacto: 3014170313

INSTRUCCIONES:
- Responde de forma amigable, clara y breve (máximo 3-4 líneas)
- Si la pregunta es sobre pedidos o productos específicos, sugiere usar el menú del bot
- Si no sabes algo con certeza, indica que pueden contactar vía WhatsApp
- Usa emojis ocasionalmente (pero sin abusar)
- Siempre habla en español colombiano natural"""

            # Construir mensajes
            messages = [{"role": "system", "content": system_message}]
            
            # Agregar historial si existe (últimos 6 mensajes = 3 intercambios)
            if chat_history and len(chat_history) > 0:
                for msg in chat_history[-6:]:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # Agregar pregunta actual
            messages.append({"role": "user", "content": query})
            
            # Llamar a OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
                top_p=0.9
            )
            
            respuesta_texto = response.choices[0].message.content.strip()
            
            # Calcular confianza basada en finish_reason
            confianza = 0.75  # Por defecto
            
            # Si la respuesta se completó correctamente
            if response.choices[0].finish_reason == "stop":
                confianza = 0.85
            
            # Aumentar si respuesta tiene info específica del negocio
            if any(keyword in respuesta_texto.lower() for keyword in 
                   ['milhoja', 'bogotá', '3014170313', 'calle 96', 'cra 81', 'nequi', 'daviplata']):
                confianza = min(confianza + 0.1, 0.95)
            
            # Disminuir si la respuesta es vaga o indica desconocimiento
            if any(phrase in respuesta_texto.lower() for phrase in 
                   ['no sé', 'no estoy seguro', 'no tengo información', 'no puedo', 'disculpa']):
                confianza = 0.5
            
            logger.info(f"✅ Respuesta OpenAI generada (confianza: {confianza})")
            
            return {
                "respuesta": respuesta_texto,
                "confianza": confianza,
                "fuente": "openai",
                "tokens_usados": response.usage.total_tokens
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
