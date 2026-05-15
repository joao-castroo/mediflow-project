import json
import sys
import os
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Mock do Boto3
from unittest.mock import MagicMock
import boto3
boto3.resource = MagicMock()
boto3.client = MagicMock()

# Mock de Ambiente
os.environ["USERS_TABLE"] = "UsersTable"
os.environ["TABLE_NAME"] = "TriageTable"

def test_auth_flow():
    print("=== TESTANDO SISTEMA DE AUTENTICACAO ===")
    
    # 1. Carregar Módulos
    reg_path = os.path.join(os.getcwd(), 'src', 'auth', 'register', 'app.py')
    login_path = os.path.join(os.getcwd(), 'src', 'auth', 'login', 'app.py')
    
    reg_app = load_module('reg_app', reg_path)
    login_app = load_module('login_app', login_path)

    # Mock do Banco de Dados para Usuários
    mock_db = {}
    
    def mock_put_item(Item):
        mock_db[Item['cpf']] = Item
        return {}

    def mock_get_item(Key):
        cpf = Key['cpf']
        if cpf in mock_db:
            return {'Item': mock_db[cpf]}
        return {}

    reg_app.dynamodb.Table().put_item.side_effect = mock_put_item
    reg_app.dynamodb.Table().get_item.side_effect = mock_get_item
    login_app.dynamodb.Table().get_item.side_effect = mock_get_item

    # TESTE 1: Cadastro Novo
    print("\n[T1] Cadastrando novo usuario (Joao)...")
    event_reg = {
        "body": json.dumps({
            "cpf": "111",
            "password": "123",
            "fullName": "Joao Silva",
            "chronicConditions": ["diabetes"]
        })
    }
    res_reg = reg_app.lambda_handler(event_reg, None)
    print(f"Resultado: {res_reg['statusCode']} - {res_reg['body']}")

    # TESTE 2: Cadastro Duplicado (Deve dar erro 400)
    print("\n[T2] Tentando cadastrar o mesmo CPF novamente...")
    res_dup = reg_app.lambda_handler(event_reg, None)
    print(f"Resultado: {res_dup['statusCode']} - {res_dup['body']}")

    # TESTE 3: Login Correto
    print("\n[T3] Testando Login com credenciais corretas...")
    event_login = {
        "body": json.dumps({"cpf": "111", "password": "123"})
    }
    res_login = login_app.lambda_handler(event_login, None)
    print(f"Resultado: {res_login['statusCode']} - {res_login['body']}")

    # TESTE 4: Login Errado (Deve dar erro 401)
    print("\n[T4] Testando Login com senha errada...")
    event_wrong = {
        "body": json.dumps({"cpf": "111", "password": "999"})
    }
    res_wrong = login_app.lambda_handler(event_wrong, None)
    print(f"Resultado: {res_wrong['statusCode']} - {res_wrong['body']}")

    print("\n=== FIM DOS TESTES DE AUTH ===")

if __name__ == "__main__":
    test_auth_flow()
