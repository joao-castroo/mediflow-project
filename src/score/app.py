"""
MediFlow — Lambda: CalculateScore (Motor White-Box)
Recebe três dimensões separadas:
  1. Sinais vitais validados
  2. Histórico de doenças crônicas
  3. Sintomas reportados e classificados
Calcula score numérico composto e classifica urgência com justificativa.
"""


# =============================================================
# 1. SCORING — SINAIS VITAIS
# =============================================================
def _score_vitals(vitals_data: dict) -> tuple[int, list[str]]:
    """Pontua sinais vitais. Retorna (pontos, justificativas)."""
    score = 0
    reasons = []

    vitals = vitals_data.get("vitals", {})

    # --- Heart Rate ---
    hr = vitals.get("heartRate", {})
    hr_val = hr.get("value")
    if hr_val is not None:
        if hr_val > 120:
            score += 30
            reasons.append(f"[VITAL] Taquicardia severa (FC={hr_val} bpm)")
        elif hr_val > 100:
            score += 15
            reasons.append(f"[VITAL] Taquicardia moderada (FC={hr_val} bpm)")
        elif hr_val < 50:
            score += 25
            reasons.append(f"[VITAL] Bradicardia (FC={hr_val} bpm)")

    # --- SpO2 ---
    spo2 = vitals.get("spo2", {})
    spo2_val = spo2.get("value")
    if spo2_val is not None:
        if spo2_val < 90:
            score += 35
            reasons.append(f"[VITAL] Hipoxemia crítica (SpO2={spo2_val}%)")
        elif spo2_val < 94:
            score += 20
            reasons.append(f"[VITAL] Hipoxemia moderada (SpO2={spo2_val}%)")

    # --- Temperature ---
    temp = vitals.get("temperature", {})
    temp_val = temp.get("value")
    if temp_val is not None:
        if temp_val >= 39.5:
            score += 25
            reasons.append(f"[VITAL] Febre alta (T={temp_val}°C)")
        elif temp_val >= 38.0:
            score += 10
            reasons.append(f"[VITAL] Febre moderada (T={temp_val}°C)")
        elif temp_val < 35.0:
            score += 20
            reasons.append(f"[VITAL] Hipotermia (T={temp_val}°C)")

    # --- Systolic BP ---
    bp = vitals.get("systolicBP", {})
    bp_val = bp.get("value")
    if bp_val is not None:
        if bp_val < 80:
            score += 35
            reasons.append(f"[VITAL] Hipotensão severa (PAS={bp_val} mmHg)")
        elif bp_val < 90:
            score += 20
            reasons.append(f"[VITAL] Hipotensão moderada (PAS={bp_val} mmHg)")
        elif bp_val > 180:
            score += 25
            reasons.append(f"[VITAL] Crise hipertensiva (PAS={bp_val} mmHg)")

    return score, reasons


# =============================================================
# 2. SCORING — DOENÇAS CRÔNICAS (HISTÓRICO)
# =============================================================
def _score_history(history_data: dict) -> tuple[int, list[str]]:
    """Pontua condições crônicas. Retorna (pontos, justificativas)."""
    score = 0
    reasons = []

    conditions = history_data.get("chronicConditions", [])

    weights = {
        "insuficiencia_cardiaca": 20,
        "diabetes_tipo_1": 15,
        "diabetes_tipo_2": 10,
        "hipertensao": 8,
        "asma": 7,
        "obesidade": 5,
        "dpoc": 12,
    }

    for condition in conditions:
        w = weights.get(condition, 5)
        score += w
        reasons.append(f"[DOENÇA] {condition} (+{w} pts)")

    return score, reasons


# =============================================================
# 3. SCORING — SINTOMAS REPORTADOS
# =============================================================
def _score_symptoms(symptoms_data: dict) -> tuple[int, list[str]]:
    """Pontua sintomas classificados. Retorna (pontos, justificativas)."""
    score = 0
    reasons = []

    classified = symptoms_data.get("classifiedSymptoms", [])

    for symptom in classified:
        w = symptom.get("weight", 5)
        label = symptom.get("label", symptom.get("key", "desconhecido"))
        severity = symptom.get("severity", "MEDIUM")
        score += w
        reasons.append(f"[SINTOMA:{severity}] {label} (+{w} pts)")

    # Bônus de correlação: sintomas críticos simultâneos amplificam risco
    critical_count = sum(1 for s in classified if s.get("severity") == "CRITICAL")
    if critical_count >= 2:
        bonus = 15 * (critical_count - 1)
        score += bonus
        reasons.append(
            f"[CORRELAÇÃO] {critical_count} sintomas críticos simultâneos (+{bonus} pts)"
        )

    return score, reasons


# =============================================================
# CLASSIFICAÇÃO FINAL
# =============================================================
def _classify(score: int) -> str:
    """Classifica urgência baseada no score numérico composto."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    else:
        return "LOW"


def lambda_handler(event, context):
    vitals_data = event.get("vitals", {})
    history_data = event.get("history", {})
    symptoms_data = event.get("symptoms", {})

    vitals_score, vitals_reasons = _score_vitals(vitals_data)
    history_score, history_reasons = _score_history(history_data)
    symptoms_score, symptoms_reasons = _score_symptoms(symptoms_data)

    total_score = vitals_score + history_score + symptoms_score
    all_reasons = vitals_reasons + history_reasons + symptoms_reasons
    urgency = _classify(total_score)

    if not all_reasons:
        all_reasons = ["Nenhum fator de risco significativo identificado."]

    return {
        "riskScore": total_score,
        "urgencyLevel": urgency,
        "breakdown": {
            "vitalsScore": vitals_score,
            "historyScore": history_score,
            "symptomsScore": symptoms_score,
        },
        "explanation": all_reasons,
    }
