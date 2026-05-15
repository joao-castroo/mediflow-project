import json
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock do Boto3 para não precisar de conexão real no teste local
class TestMediFlowFlow(unittest.TestCase):
    
    def setUp(self):
        self.mock_dynamo = MagicMock()
        self.mock_table = MagicMock()
        self.mock_dynamo.Table.return_value = self.mock_table
        
    @patch('boto3.resource')
    def test_01_register_user_logic(self, mock_boto):
        """Testa a logica de cadastro de usuario"""
        mock_boto.return_value = self.mock_dynamo
        
        # Importa a lambda de registro usando importlib para evitar conflitos
        import importlib.util
        spec = importlib.util.spec_from_file_location("register_app", "src/auth/register/app.py")
        register_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(register_app)
        
        # Simula usuario nao existe
        self.mock_table.get_item.return_value = {}
        
        event = {
            "body": json.dumps({
                "cpf": "111.111.111-11",
                "password": "senha123",
                "fullName": "Joao Teste",
                "chronicConditions": ["Diabetes"]
            })
        }
        
        response = register_app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 201)
        print("Test de Cadastro: OK")

    @patch('boto3.resource')
    def test_02_login_logic(self, mock_boto):
        """Testa a logica de login"""
        mock_boto.return_value = self.mock_dynamo
        
        # Importa a lambda de login usando importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location("login_app", "src/auth/login/app.py")
        login_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(login_app)
        
        # Simula usuario existe
        self.mock_table.get_item.return_value = {
            'Item': {
                'cpf': '111.111.111-11',
                'password': 'senha123',
                'fullName': 'Joao Teste'
            }
        }
        
        event = {
            "body": json.dumps({
                "cpf": "111.111.111-11",
                "password": "senha123"
            })
        }
        
        response = login_app.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['fullName'], 'Joao Teste')
        print("Test de Login: OK")

    def test_03_frontend_integrity(self):
        """Verifica se os arquivos do front existem nos locais certos"""
        files = [
            'frontend/index.html',
            'frontend/login.html',
            'frontend/dashboard.html',
            'frontend/auth.js',
            'frontend/config.js'
        ]
        for f in files:
            self.assertTrue(os.path.exists(f), f"Arquivo faltando: {f}")
        print("Integridade do Frontend: OK")

if __name__ == '__main__':
    unittest.main()
