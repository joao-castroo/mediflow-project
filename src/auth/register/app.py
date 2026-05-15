import os
import json
import boto3
import logging

from datetime import datetime

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('USERS_TABLE', 'UsersTable')

def lambda_handler(event, context):
    """
    Cadastra um novo usuário/paciente no sistema.
    """
    try:
        # Pega o corpo da requisição e garante que não seja None ou vazio
        body_raw = event.get("body")
        if not body_raw:
            return response(400, {"message": "Corpo da requisição vazio."})
            
        body = json.loads(body_raw)
        cpf = body.get("cpf")
        password = body.get("password")
        full_name = body.get("fullName")
        
        if not cpf or not password:
            return response(400, {"message": "CPF e senha são obrigatórios."})

        table = dynamodb.Table(TABLE_NAME)
        
        # 1. Verifica se o usuário já existe
        existing = table.get_item(Key={'cpf': cpf})
        if 'Item' in existing:
            return response(400, {"message": "Este CPF já possui cadastro no MediFlow."})

        # 2. Cria o registro do usuário
        user_item = {
            "cpf": cpf,
            "password": password, 
            "fullName": full_name,
            "chronicConditions": body.get("chronicConditions", []),
            "medications": body.get("medications", []),
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        
        table.put_item(Item=user_item)
        
        logger.info(f"Novo usuário cadastrado: {cpf}")
        return response(201, {"message": "Cadastro realizado com sucesso!"})

    except Exception as e:
        logger.error(f"Erro no cadastro: {str(e)}")
        return response(500, {"error": str(e), "details": "Verifique se a tabela UsersTable existe e se a Lambda tem permissão de escrita."})

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
