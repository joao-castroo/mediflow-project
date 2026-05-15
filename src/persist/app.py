import os
import json
import boto3
import logging
import datetime
import time
from decimal import Decimal

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def float_to_decimal(obj):
    """
    Converte recursivamente floats para Decimals para compatibilidade com DynamoDB.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, (int, Decimal)):
        return obj
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [float_to_decimal(v) for v in obj]
    return obj

# Clientes AWS
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ.get("TABLE_NAME", "TriageTable")
TOPIC_ARN = os.environ.get("TOPIC_ARN", "")

def lambda_handler(event, context):
    """
    Persiste o resultado da triagem no DynamoDB e notifica via SNS.
    """
    triage_id = f"T-{int(time.time())}"
    now = datetime.datetime.utcnow()
    timestamp = now.isoformat() + "Z"
    
    # Retenção LGPD: expurgo em 90 dias
    expires_at = int((now + datetime.timedelta(days=90)).timestamp())

    # Logging seguro (sem PII)
    logger.info(f"Processando triagem. RequestId: {context.aws_request_id}, TriageId: {triage_id}")

    # Tenta pegar do nível raiz ou dos caminhos do Step Functions
    patient = event.get("patient") or event.get("identifyResult", {}).get("patient", {})
    vitals = event.get("vitals") or event.get("parallelResults", [{}])[0].get("vitals", {})
    history = event.get("history") or event.get("parallelResults", [{}, {}])[1].get("history", {})
    symptoms = event.get("symptoms") or event.get("parallelResults", [{}, {}, {}])[2].get("symptoms", {})
    scoring = event.get("scoring") or event.get("scoreResult", {}).get("scoring", {}) or event.get("scoreResult", {})

    risk_score = scoring.get("riskScore", 0)
    urgency_level = scoring.get("urgencyLevel", "UNKNOWN")

    # --- Persistir no DynamoDB ---
    table = dynamodb.Table(TABLE_NAME)
    item = {
        "triageId": triage_id,
        "patientId": patient.get("patientId", "N/A"),
        "fullName": patient.get("fullName", "N/A"),
        "riskScore": risk_score,
        "urgencyLevel": urgency_level,
        "scoreBreakdown": scoring.get("breakdown", {}),
        "explanation": scoring.get("explanation", []),
        "vitals": vitals,
        "chronicConditions": history.get("chronicConditions", []),
        "reportedSymptoms": symptoms.get("classifiedSymptoms", []),
        "createdAt": timestamp,
        "eventTimestamp": timestamp,
        "expiresAt": expires_at,
        "status": "WAITING"
    }
    
    # Converte floats para Decimals antes de salvar
    table.put_item(Item=float_to_decimal(item))

    # --- Publicar evento no SNS ---
    if TOPIC_ARN:
        sns_message = {
            "eventType": "triage.completed",
            "triageId": triage_id,
            "patientId": patient.get("patientId"),
            "riskScore": risk_score,
            "urgencyLevel": urgency_level,
            "explanation": scoring.get("explanation", []),
            "timestamp": timestamp,
        }
        try:
            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject="MediFlow - Triagem Concluída",
                Message=json.dumps(sns_message, ensure_ascii=False),
                MessageAttributes={
                    'urgencyLevel': {
                        'DataType': 'String',
                        'StringValue': urgency_level
                    }
                }
            )
        except Exception as e:
            logger.error(f"Erro ao publicar no SNS: {str(e)}")

    # --- Retorno final para o site ---
    return {
        "triageId": triage_id,
        "riskScore": risk_score,
        "urgencyLevel": urgency_level,
        "explanation": scoring.get("explanation", [])
    }
