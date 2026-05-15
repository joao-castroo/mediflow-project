import json
import logging

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda disparada APENAS para pacientes CRÍTICOS (via Filtro SNS).
    """
    for record in event.get('Records', []):
        try:
            # Pega a mensagem do SNS
            sns_message = json.loads(record['Sns']['Message'])
            
            triage_id = sns_message.get('triageId')
            patient_id = sns_message.get('patientId')
            urgency = sns_message.get('urgencyLevel')
            reasons = sns_message.get('explanation', [])

            # REGISTRO DE ALERTA MÁXIMO
            logger.info("==========================================")
            logger.info("🚨 ALERTA DE EMERGÊNCIA CRÍTICA DETECTADA 🚨")
            logger.info(f"PACIENTE: {patient_id}")
            logger.info(f"TRIAGEM: {triage_id}")
            logger.info(f"MOTIVOS: {', '.join(reasons)}")
            logger.info("AÇÃO: Notificar equipe médica imediatamente!")
            logger.info("==========================================")
            
            # Aqui poderíamos adicionar envio de SMS via AWS SNS ou E-mail via AWS SES
            
        except Exception as e:
            logger.error(f"Erro ao processar alerta: {str(e)}")

    return {"status": "Alert Processed"}
