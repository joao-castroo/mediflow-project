import os
import json
import boto3
import logging
from datetime import datetime

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

TABLE_NAME = os.environ.get('TABLE_NAME', 'TriageTable')
REPORTS_BUCKET = os.environ.get('REPORTS_BUCKET')

def lambda_handler(event, context):
    """
    Marca um paciente como atendido, remove da fila ativa e salva registro no S3.
    """
    try:
        # Pega triageId do path parameter do API Gateway
        triage_id = event.get("pathParameters", {}).get("triageId")
        
        if not triage_id:
            return {"statusCode": 400, "body": json.dumps({"message": "triageId obrigatório."})}

        table = dynamodb.Table(TABLE_NAME)
        
        # 1. Busca os dados atuais para salvar no histórico do S3
        response = table.get_item(Key={'triageId': triage_id})
        triage_data = response.get('Item')
        
        if not triage_data:
            return {"statusCode": 404, "body": json.dumps({"message": "Triagem não encontrada."})}

        # 2. Atualiza o status para ATTENDED (remove da fila do GSI)
        table.update_item(
            Key={'triageId': triage_id},
            UpdateExpression="SET #s = :val, attendedAt = :time",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":val": "ATTENDED",
                ":time": datetime.utcnow().isoformat() + "Z"
            }
        )

        # 3. Salva o registro de atendimento no S3 (Dossiê final)
        attendance_record = {
            "triageId": triage_id,
            "patientId": triage_data.get("patientId"),
            "fullName": triage_data.get("fullName"),
            "riskScore": triage_data.get("riskScore"),
            "urgencyLevel": triage_data.get("urgencyLevel"),
            "attendedAt": datetime.utcnow().isoformat() + "Z",
            "originalTriageData": triage_data
        }

        s3_key = f"attended/{datetime.now().strftime('%Y/%m/%d')}/{triage_id}.json"
        
        s3.put_object(
            Bucket=REPORTS_BUCKET,
            Key=s3_key,
            Body=json.dumps(attendance_record, default=str),
            ContentType='application/json'
        )

        logger.info(f"Paciente {triage_id} atendido e arquivado no S3.")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Atendimento registrado com sucesso!",
                "s3Key": s3_key
            })
        }

    except Exception as e:
        logger.error(f"Erro ao processar atendimento: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }
