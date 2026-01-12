import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock environment variables before importing anything that uses them
os.environ['OPENAI_API_KEY'] = 'fake-key'
os.environ['SUPABASE_URL'] = 'https://fake.supabase.co'
os.environ['SUPABASE_KEY'] = 'fake-key'

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock imports that we don't want to actually run
sys.modules['openai'] = MagicMock()
sys.modules['supabase'] = MagicMock()

# Import the service to test
# We need to ensure config.database is accessible
from app.services.ai_service import AIService

class TestAIService(unittest.TestCase):
    
    def setUp(self):
        self.ai_service = AIService()
        # Mock the real OpenAI client inside the instance
        self.ai_service.client = MagicMock()

    @patch('config.database.db')
    def test_ask_openai_includes_products(self, mock_db):
        # Setup mock products
        mock_products = [
            {'nombre': 'Milhoja Clásica', 'precio': 5000, 'descripcion': 'Deliciosa', 'categoria': 'Milhojas'},
            {'nombre': 'Café', 'precio': 3000, 'descripcion': 'Tinto', 'categoria': 'Bebidas'}
        ]
        mock_db.get_all_products.return_value = mock_products
        
        # Call the method
        query = "Qué venden?"
        self.ai_service.ask_openai(query)
        
        # Verify get_all_products was called
        mock_db.get_all_products.assert_called_once()
        
        # Verify the system message sent to OpenAI contains the products
        call_args = self.ai_service.client.chat.completions.create.call_args
        _, kwargs = call_args
        messages = kwargs['messages']
        system_msg = messages[0]['content']
        
        self.assertIn("Milhoja Clásica", system_msg)
        self.assertIn("5,000", system_msg)
        self.assertIn("Café", system_msg)
        self.assertIn("NUESTROS PRODUCTOS DISPONIBLES", system_msg)

    @patch('config.database.db')
    def test_ask_openai_handles_empty_products(self, mock_db):
        # Setup empty products
        mock_db.get_all_products.return_value = []
        
        self.ai_service.ask_openai("Qué hay?")
        
        call_args = self.ai_service.client.chat.completions.create.call_args
        _, kwargs = call_args
        system_msg = kwargs['messages'][0]['content']
        
        self.assertIn("No hay productos disponibles", system_msg)

if __name__ == '__main__':
    unittest.main()
