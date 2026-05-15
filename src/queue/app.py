import os
import json
import boto3
import logging
from boto3.dynamodb.conditions import Key

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'TriageTable')

def lambda_handler(event, context):
    """
    Retorna a fila de pacientes com status WAITING, ordenados por tempo (via GSI).
    """
    logger.info("Buscando fila de espera ativa.")
    
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        # Consulta usando o GSI StatusIndex
        # Lembre-se: o GSI ordena por eventTimestamp automaticamente
        response = table.query(
            IndexName='StatusIndex',
            KeyConditionExpression=Key('status').eq('WAITING')
        )
        
        items = response.get('Items', [])
        
        # Ordenação Adicional por Score (Maior risco primeiro)
        # Se scores forem iguais, a ordem natural do GSI (tempo) prevalece
        sorted_items = sorted(items, key=lambda x: x.get('riskScore', 0), reverse=True)

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps(sorted_items, default=str)
        }

    except Exception as e:
        logger.error(f"Erro ao buscar fila: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }
