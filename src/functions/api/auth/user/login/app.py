import os
import json
import boto3
import logging

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('USERS_TABLE', 'UsersTable')

def lambda_handler(event, context):
    """
    Valida login do usuário e retorna dados do perfil.
    """
    try:
        # Pega o corpo da requisição e garante que não seja None ou vazio
        body_raw = event.get("body")
        if not body_raw:
            return response(400, {"message": "Corpo da requisição vazio."})
            
        body = json.loads(body_raw)
        cpf = body.get("cpf")
        password = body.get("password")

        if not cpf or not password:
            return response(400, {"message": "CPF e senha são obrigatórios."})

        table = dynamodb.Table(TABLE_NAME)
        res = table.get_item(Key={'cpf': cpf})
        
        if 'Item' not in res:
            return response(401, {"message": "Usuário não encontrado."})
        
        user = res['Item']
        
        # Validação de senha (simplificada)
        if user['password'] != password:
            return response(401, {"message": "Senha incorreta."})

        # Retorna os dados do perfil (exceto a senha por segurança)
        profile = {
            "cpf": user['cpf'],
            "fullName": user['fullName'],
            "role": user.get('role', 'patient'),
            "chronicConditions": user.get('chronicConditions', []),
            "medications": user.get('medications', []),
            "specialty": user.get('specialty', ''),
            "crm": user.get('crm', '')
        }
        
        logger.info(f"Login realizado: {cpf}")
        return response(200, profile)

    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        # Retorna o erro real para debug (remover em produção)
        return response(500, {"error": str(e), "details": "Verifique as permissões da tabela ou o nome da variável USERS_TABLE"})

def response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
