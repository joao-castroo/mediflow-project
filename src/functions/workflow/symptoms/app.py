"""
MediFlow — Lambda: ClassifySymptoms
Recebe lista de sintomas reportados pelo paciente,
classifica cada um por severidade e retorna dados estruturados.
"""

# Catálogo de sintomas com severidade e peso para scoring
SYMPTOM_CATALOG = {
    # --- Sintomas Críticos (peso alto) ---
    "dor_no_peito": {
        "label": "Dor no peito",
        "severity": "CRITICAL",
        "weight": 35,
        "description": "Possível evento cardíaco agudo",
    },
    "dificuldade_respiratoria": {
        "label": "Dificuldade respiratória / Dispneia",
        "severity": "CRITICAL",
        "weight": 35,
        "description": "Comprometimento da função respiratória",
    },
    "perda_consciencia": {
        "label": "Perda de consciência / Síncope",
        "severity": "CRITICAL",
        "weight": 40,
        "description": "Possível evento neurológico ou cardiovascular grave",
    },
    "convulsao": {
        "label": "Convulsão",
        "severity": "CRITICAL",
        "weight": 40,
        "description": "Atividade convulsiva requer avaliação emergencial",
    },
    "dor_abdominal_intensa": {
        "label": "Dor abdominal intensa",
        "severity": "HIGH",
        "weight": 25,
        "description": "Possível abdome agudo cirúrgico",
    },
    "paralisia_subita": {
        "label": "Paralisia ou fraqueza súbita",
        "severity": "CRITICAL",
        "weight": 40,
        "description": "Possível AVC — tempo é crítico",
    },
    "confusao_mental": {
        "label": "Confusão mental / Desorientação",
        "severity": "CRITICAL",
        "weight": 30,
        "description": "Alteração do nível de consciência",
    },

    # --- Sintomas de Alta Severidade ---
    "sangramento_ativo": {
        "label": "Sangramento ativo",
        "severity": "HIGH",
        "weight": 25,
        "description": "Hemorragia requer avaliação de volume e origem",
    },
    "vomito_persistente": {
        "label": "Vômito persistente",
        "severity": "HIGH",
        "weight": 15,
        "description": "Risco de desidratação e desequilíbrio eletrolítico",
    },
    "febre_persistente": {
        "label": "Febre persistente (>3 dias)",
        "severity": "HIGH",
        "weight": 15,
        "description": "Possível infecção sistêmica",
    },
    "dor_de_cabeca_intensa": {
        "label": "Dor de cabeça intensa / súbita",
        "severity": "HIGH",
        "weight": 20,
        "description": "Cefaleia thunderclap pode indicar hemorragia subaracnóidea",
    },
    "dor_toracica_ao_respirar": {
        "label": "Dor torácica ao respirar",
        "severity": "HIGH",
        "weight": 20,
        "description": "Possível pleurite ou embolia pulmonar",
    },
    "edema_membros": {
        "label": "Edema de membros inferiores",
        "severity": "HIGH",
        "weight": 15,
        "description": "Possível TVP ou insuficiência cardíaca",
    },

    # --- Sintomas de Média Severidade ---
    "tontura": {
        "label": "Tontura / Vertigem",
        "severity": "MEDIUM",
        "weight": 10,
        "description": "Pode indicar hipotensão, labirintite ou causa central",
    },
    "nausea": {
        "label": "Náusea",
        "severity": "MEDIUM",
        "weight": 8,
        "description": "Sintoma inespecífico, avaliar contexto",
    },
    "diarreia": {
        "label": "Diarreia",
        "severity": "MEDIUM",
        "weight": 8,
        "description": "Risco de desidratação se prolongada",
    },
    "dor_de_cabeca_leve": {
        "label": "Dor de cabeça leve",
        "severity": "MEDIUM",
        "weight": 5,
        "description": "Cefaleia tensional ou enxaqueca leve",
    },
    "dor_muscular": {
        "label": "Dor muscular / Mialgia",
        "severity": "MEDIUM",
        "weight": 5,
        "description": "Pode indicar infecção viral ou esforço",
    },
    "tosse_persistente": {
        "label": "Tosse persistente",
        "severity": "MEDIUM",
        "weight": 8,
        "description": "Avaliar possível infecção respiratória",
    },
    "palpitacoes": {
        "label": "Palpitações",
        "severity": "MEDIUM",
        "weight": 12,
        "description": "Sensação de batimento irregular, avaliar arritmia",
    },

    # --- Sintomas de Baixa Severidade ---
    "dor_de_garganta": {
        "label": "Dor de garganta",
        "severity": "LOW",
        "weight": 3,
        "description": "Faringite comum, geralmente autolimitada",
    },
    "coriza": {
        "label": "Coriza / Congestão nasal",
        "severity": "LOW",
        "weight": 2,
        "description": "Sintoma de IVAS ou alergia",
    },
    "fadiga": {
        "label": "Fadiga / Cansaço",
        "severity": "LOW",
        "weight": 3,
        "description": "Sintoma inespecífico, diversas causas possíveis",
    },
    "coceira": {
        "label": "Coceira / Prurido",
        "severity": "LOW",
        "weight": 2,
        "description": "Possível reação alérgica leve ou dermatite",
    },
    "dor_nas_costas": {
        "label": "Dor nas costas (lombalgia)",
        "severity": "LOW",
        "weight": 4,
        "description": "Causa mecânica comum, avaliar sinais de alarme",
    },
}

# Peso padrão para sintomas não catalogados
_DEFAULT_WEIGHT = 5
_DEFAULT_SEVERITY = "MEDIUM"


def lambda_handler(event, context):
    reported_symptoms = event.get("symptoms", [])

    if not isinstance(reported_symptoms, list):
        raise ValueError("Campo 'symptoms' deve ser uma lista de strings.")

    classified = []
    unknown = []

    for symptom_key in reported_symptoms:
        symptom_key = symptom_key.strip().lower()

        if symptom_key in SYMPTOM_CATALOG:
            info = SYMPTOM_CATALOG[symptom_key]
            classified.append({
                "key": symptom_key,
                "label": info["label"],
                "severity": info["severity"],
                "weight": info["weight"],
                "description": info["description"],
            })
        else:
            unknown.append({
                "key": symptom_key,
                "label": symptom_key,
                "severity": _DEFAULT_SEVERITY,
                "weight": _DEFAULT_WEIGHT,
                "description": "Sintoma não catalogado — peso padrão aplicado",
            })
            classified.append(unknown[-1])

    return {
        "reportedCount": len(reported_symptoms),
        "classifiedSymptoms": classified,
        "unknownSymptoms": [u["key"] for u in unknown],
        "hasCritical": any(s["severity"] == "CRITICAL" for s in classified),
    }
