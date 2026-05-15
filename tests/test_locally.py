import json
import sys
import os
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tests"))
from support.fake_boto3 import install_if_missing

install_if_missing()

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Mock do Boto3
from unittest.mock import MagicMock
import boto3
boto3.resource = MagicMock()
boto3.client = MagicMock()

# Variáveis de Ambiente Mock para o teste
os.environ["TABLE_NAME"] = "TriageTable"
os.environ["TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:MediFlowTopic"
os.environ["PATIENTS_TABLE"] = "PatientsTable"

def test_full_flow():
    print("=== INICIANDO TESTE DE LOGICA LOCAL (REFORMULADO) ===")
    
    # 1. Teste Identify
    print("\n[1] Testando Identify...")
    identify_path = PROJECT_ROOT / 'src' / 'functions' / 'workflow' / 'identify' / 'app.py'
    identify_app = load_module('identify_app', identify_path)
    
    event_id = {"patientId": "12345"}
    identify_app.dynamodb.Table().get_item.return_value = {
        'Item': {'patientId': '12345', 'fullName': 'Joao Silva'}
    }
    identify_res = identify_app.lambda_handler(event_id, None)
    print(f"Identify Output: {identify_res}")

    # 2. Teste Score
    print("\n[2] Testando Score...")
    score_path = PROJECT_ROOT / 'src' / 'functions' / 'workflow' / 'score' / 'app.py'
    score_app = load_module('score_app', score_path)
    
    score_event = {
        "patient": identify_res,
        "vitals": {"heartRate": {"value": 130}, "spo2": {"value": 85}},
        "history": {"chronicConditions": ["diabetes"]},
        "symptoms": {"reportedCount": 2}
    }
    score_res = score_app.lambda_handler(score_event, None)
    print(f"Score Output: Score={score_res['riskScore']}, Urgency={score_res['urgencyLevel']}")

    # 3. Teste Persist (Onde estava o erro de undefined)
    print("\n[3] Testando Persist...")
    persist_path = PROJECT_ROOT / 'src' / 'functions' / 'workflow' / 'persist' / 'app.py'
    persist_app = load_module('persist_app', persist_path)
    
    # Simulando EXATAMENTE como o Step Functions envia os dados (dentro de identifyResult e parallelResults)
    persist_event = {
        "identifyResult": {"patient": identify_res},
        "parallelResults": [
            {"vitals": {"heartRate": 130}},
            {"history": {"chronicConditions": ["diabetes"]}},
            {"symptoms": {"reportedCount": 2}}
        ],
        "scoreResult": {"scoring": score_res}
    }
    
    class MockContext:
        aws_request_id = "test-id-123"
    
    persist_res = persist_app.lambda_handler(persist_event, MockContext())
    print(f"Persist Final Output: {json.dumps(persist_res, indent=2)}")

    # 4. Teste Alerta Crítico (SNS Trigger)
    print("\n[4] Testando Alerta Crítico (SNS)...")
    alerts_path = PROJECT_ROOT / 'src' / 'functions' / 'async' / 'alerts' / 'app.py'
    alerts_app = load_module('alerts_app', alerts_path)
    
    sns_event = {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps({
                        "triageId": "T-123",
                        "patientId": "999.999.999-99",
                        "urgencyLevel": "CRITICAL",
                        "explanation": ["Emergência Cardíaca", "Saturação Baixa"]
                    })
                }
            }
        ]
    }
    
    alerts_res = alerts_app.lambda_handler(sns_event, None)
    print(f"Alert Output: {alerts_res}")

    # Verificacao
    print("\n=== RESULTADO DO TESTE ===")
    if all(k in persist_res for k in ["triageId", "riskScore", "urgencyLevel", "explanation"]):
        print("SUCESSO: Todos os campos estao presentes!")
    else:
        missing = [k for k in ["triageId", "riskScore", "urgencyLevel", "explanation"] if k not in persist_res]
        print(f"FALHA: Campos faltando: {missing}")

if __name__ == "__main__":
    test_full_flow()
