"""
MediFlow — Lambda: AsyncReports
Trigada pelo SNS. Gera relatório operacional em JSON e salva no S3.
"""

import json
import os
import datetime
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
REPORTS_BUCKET = os.environ["REPORTS_BUCKET"]


def lambda_handler(event, context):
    logger.info(f"Iniciando processamento assíncrono. RequestId: {context.aws_request_id}")
    
    # Cada registro SNS vem dentro de event["Records"]
    for record in event.get("Records", []):
        sns_message = record.get("Sns", {}).get("Message", "{}")
        data = json.loads(sns_message)

        triage_id = data.get("triageId", "unknown")
        timestamp = data.get("timestamp", datetime.datetime.utcnow().isoformat() + "Z")

        logger.info(f"Gerando relatório para TriageId: {triage_id}")

        # --- Gerar relatório operacional ---
        report = {
            "reportType": "OPERATIONAL_TRIAGE_SUMMARY",
            "generatedAt": datetime.datetime.utcnow().isoformat() + "Z",
            "source": "MediFlow-AsyncReports",
            "triageData": {
                "triageId": triage_id,
                "patientId": data.get("patientId"),
                "riskScore": data.get("riskScore"),
                "urgencyLevel": data.get("urgencyLevel"),
                "explanation": data.get("explanation", []),
                "eventTimestamp": timestamp,
            },
            "metadata": {
                "eventType": data.get("eventType"),
                "lambdaRequestId": context.aws_request_id if context else "local",
            },
        }

        # --- Upload para S3 ---
        date_prefix = datetime.datetime.utcnow().strftime("%Y/%m/%d")
        s3_key = f"reports/{date_prefix}/{triage_id}.json"

        s3.put_object(
            Bucket=REPORTS_BUCKET,
            Key=s3_key,
            Body=json.dumps(report, ensure_ascii=False, separators=(",", ":")),
            ContentType="application/json",
        )

    logger.info("Processamento assíncrono concluído com sucesso.")
    return {"statusCode": 200, "message": "Reports generated successfully"}
