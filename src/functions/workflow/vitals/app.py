"""
MediFlow — Lambda: ValidateVitals
Lê sinais vitais do input e valida intervalos lógicos.
"""


# Intervalos aceitáveis para sinais vitais
VITAL_RANGES = {
    "heartRate":   {"min": 30,   "max": 250,   "unit": "bpm"},
    "spo2":        {"min": 50,   "max": 100,   "unit": "%"},
    "temperature": {"min": 34.0, "max": 43.0,  "unit": "°C"},
    "systolicBP":  {"min": 60,   "max": 300,   "unit": "mmHg"},
}


def _validate_vital(name: str, value) -> dict:
    """Valida um sinal vital individual e retorna o resultado."""
    spec = VITAL_RANGES[name]

    if value is None:
        return {"value": None, "unit": spec["unit"], "status": "MISSING"}

    try:
        value = float(value)
    except (TypeError, ValueError):
        return {"value": value, "unit": spec["unit"], "status": "INVALID_TYPE"}

    if spec["min"] <= value <= spec["max"]:
        status = "NORMAL"
    else:
        status = "OUT_OF_RANGE"

    return {"value": value, "unit": spec["unit"], "status": status}


def lambda_handler(event, context):
    heart_rate = event.get("heartRate")
    spo2 = event.get("spo2")
    temperature = event.get("temperature")
    systolic_bp = event.get("systolicBP")

    validated = {
        "heartRate":   _validate_vital("heartRate", heart_rate),
        "spo2":        _validate_vital("spo2", spo2),
        "temperature": _validate_vital("temperature", temperature),
        "systolicBP":  _validate_vital("systolicBP", systolic_bp),
    }

    all_valid = all(v["status"] == "NORMAL" for v in validated.values())

    return {
        "vitalsValid": all_valid,
        "vitals": validated,
    }
