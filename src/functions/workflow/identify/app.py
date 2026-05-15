import os
import boto3
import logging
from datetime import datetime

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
PATIENTS_TABLE = os.environ.get('PATIENTS_TABLE', 'PatientsTable')

def lambda_handler(event, context):
    """
    Identifica o paciente no banco de dados real.
    """
    patient_id = event.get("patientId")

    if not patient_id:
        logger.error("patientId não fornecido.")
        raise ValueError("Campo 'patientId' é obrigatório.")

    logger.info(f"Identificando paciente: {patient_id}")
    
    try:
        table = dynamodb.Table(PATIENTS_TABLE)
        # Ajuste: A chave primária na tabela de usuários é 'cpf'
        response = table.get_item(Key={'cpf': patient_id})
        
        if 'Item' in response:
            patient_data = response['Item']
            return {
                "patientId": patient_id,
                "fullName": patient_data.get("fullName", "Paciente sem Nome"),
                "chronicConditions": patient_data.get("chronicConditions", []),
                "medications": patient_data.get("medications", []),
                "found": True,
                "identifiedAt": datetime.utcnow().isoformat() + "Z"
            }
        else:
            return {
                "patientId": patient_id,
                "fullName": "Paciente Não Cadastrado",
                "found": False,
                "identifiedAt": datetime.utcnow().isoformat() + "Z"
            }
            
    except Exception as e:
        logger.error(f"Erro ao acessar banco: {str(e)}")
        return {
            "patientId": patient_id,
            "fullName": "Erro na Identificação",
            "found": False,
            "error": str(e)
        }
