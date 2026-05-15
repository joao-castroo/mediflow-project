import os
import json
import boto3
import logging

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn = boto3.client('stepfunctions')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def lambda_handler(event, context):
    """
    Lambda de Ponte (Proxy): Recebe a triagem do site, chama o Step Function e garante o CORS.
    """
    logger.info("Iniciando ponte para Step Function")
    
    try:
        # Pega os dados do site
        body = event.get("body", "{}")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body

        # Executa o Step Function de forma SÍNCRONA
        response = sfn.start_sync_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(payload)
        )
        
        # Verifica o status da execução
        status = response.get('status')
        output_str = response.get('output', '{}')
        
        if status != 'SUCCEEDED':
            error_msg = response.get('error', 'Unknown Error')
            cause = response.get('cause', 'No cause provided')
            logger.error(f"Fluxo FALHOU: {error_msg} - {cause}")
            return {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "error": "Erro Interno no Fluxo AWS",
                    "details": error_msg,
                    "cause": cause
                })
            }

        output = json.loads(output_str)
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps(output)
        }

    except Exception as e:
        logger.error(f"Erro na ponte: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }
