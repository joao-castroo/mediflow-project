import os
import boto3
import logging

# Configuração de Logs
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
PATIENTS_TABLE = os.environ.get('PATIENTS_TABLE', 'PatientsTable')

def lambda_handler(event, context):
    """
    Busca o histórico clínico real do paciente no DynamoDB.
    """
    patient_id = (
        event.get("patientId")
        or event.get("identifyResult", {}).get("patient", {}).get("patientId")
    )

    if not patient_id:
        logger.error("patientId não fornecido no evento.")
        raise ValueError("Campo 'patientId' não encontrado no evento.")

    logger.info(f"Buscando histórico para o paciente: {patient_id}")
    
    try:
        table = dynamodb.Table(PATIENTS_TABLE)
        response = table.get_item(Key={'patientId': patient_id})
        
        patient_data = response.get('Item', {})
        
        # Extrai condições e medicamentos (ou lista vazia se não existir)
        chronic_conditions = patient_data.get('chronicConditions', [])
        medications = patient_data.get('medications', [])
        full_name = patient_data.get('fullName', 'Paciente Desconhecido')

        logger.info(f"Histórico encontrado: {len(chronic_conditions)} condições.")

        return {
            "patientId": patient_id,
            "fullName": full_name,
            "chronicConditions": chronic_conditions,
            "medications": medications,
            "conditionsCount": len(chronic_conditions),
            "foundInDatabase": 'Item' in response
        }
        
    except Exception as e:
        logger.error(f"Erro ao acessar DynamoDB: {str(e)}")
        # Em caso de erro, retornamos lista vazia para não travar o fluxo de triagem
        return {
            "patientId": patient_id,
            "chronicConditions": [],
            "medications": [],
            "conditionsCount": 0,
            "error": str(e)
        }
