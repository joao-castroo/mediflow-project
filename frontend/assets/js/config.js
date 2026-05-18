// Configurações Globais do MediFlow
const CONFIG = {
    // true = roda tudo localmente com localStorage, sem chamar AWS.
    // false = usa API Gateway em API_URL.
    LOCAL_MODE: false,

    // URL da sua API AWS (Obtida no Output do SAM Deploy)
    // IMPORTANTE: Deixe apenas até o /Prod (sem o /triage no final)
    API_URL: 'https://bn51l4hc7g.execute-api.us-east-1.amazonaws.com/Prod'
};

// Exporta para uso em outros arquivos
window.MEDI_CONFIG = CONFIG;

const DOCTOR_CPFS = ['22222222222'];

const SYMPTOM_CATALOG = {
    dor_no_peito: { label: 'Dor no peito', severity: 'CRITICAL', weight: 35 },
    dificuldade_respiratoria: { label: 'Dificuldade respiratória', severity: 'CRITICAL', weight: 35 },
    perda_consciencia: { label: 'Perda de consciência', severity: 'CRITICAL', weight: 40 },
    paralisia_subita: { label: 'Paralisia súbita', severity: 'CRITICAL', weight: 40 },
    dor_abdominal_intensa: { label: 'Dor abdominal intensa', severity: 'HIGH', weight: 25 },
    sangramento_ativo: { label: 'Sangramento ativo', severity: 'HIGH', weight: 25 },
    febre_persistente: { label: 'Febre persistente', severity: 'HIGH', weight: 15 },
    tontura: { label: 'Tontura', severity: 'MEDIUM', weight: 10 },
    nausea: { label: 'Náusea / vômito', severity: 'MEDIUM', weight: 8 },
    dor_de_cabeca_leve: { label: 'Dor de cabeça leve', severity: 'MEDIUM', weight: 5 },
    dor_muscular: { label: 'Dor muscular', severity: 'MEDIUM', weight: 5 },
    dor_de_garganta: { label: 'Dor de garganta', severity: 'LOW', weight: 3 }
};

const CONDITION_WEIGHTS = {
    insuficiencia_cardiaca: 20,
    doenca_cardiaca: 20,
    diabetes_tipo_1: 15,
    diabetes_tipo_2: 10,
    diabetes: 10,
    hipertensao: 8,
    asma: 7,
    obesidade: 5,
    dpoc: 12
};

function readLocalUsers() {
    return JSON.parse(localStorage.getItem('mediflow_users') || '[]');
}

function normalizeCpf(cpf) {
    return String(cpf || '').replace(/\D/g, '');
}

function getRoleForCpf(cpf) {
    return DOCTOR_CPFS.includes(normalizeCpf(cpf)) ? 'doctor' : 'patient';
}

function resolveUserRole(user) {
    const cpfRole = getRoleForCpf(user.cpf);
    return cpfRole === 'doctor' ? 'doctor' : (user.role || 'patient');
}

function writeLocalUsers(users) {
    localStorage.setItem('mediflow_users', JSON.stringify(users));
}

function seedLocalUser() {
    const users = readLocalUsers();
    const seedUsers = [{
        fullName: 'Joao Paciente Teste',
        cpf: '11111111111',
        password: '123456',
        role: 'patient',
        chronicConditions: ['diabetes', 'hipertensao'],
        medications: ['Metformina', 'Losartana']
    }, {
        fullName: 'Dra. Ana Medica',
        cpf: '22222222222',
        password: '123456',
        role: 'doctor',
        chronicConditions: [],
        medications: []
    }];

    seedUsers.forEach((seed) => {
        const existing = users.find((user) => normalizeCpf(user.cpf) === seed.cpf);
        if (existing) {
            existing.role = resolveUserRole(existing);
            return;
        }
        users.push(seed);
    });

    writeLocalUsers(users);
}

function readLocalQueue() {
    return JSON.parse(localStorage.getItem('mediflow_queue') || '[]');
}

function writeLocalQueue(queue) {
    localStorage.setItem('mediflow_queue', JSON.stringify(queue));
}

function classifyScore(score) {
    if (score >= 80) return 'CRITICAL';
    if (score >= 50) return 'HIGH';
    if (score >= 25) return 'MEDIUM';
    return 'LOW';
}

function calculateLocalTriage(payload) {
    let score = 0;
    const explanation = [];

    if (payload.heartRate > 120) {
        score += 30;
        explanation.push(`[VITAL] Taquicardia severa (FC=${payload.heartRate} bpm)`);
    } else if (payload.heartRate > 100) {
        score += 15;
        explanation.push(`[VITAL] Taquicardia moderada (FC=${payload.heartRate} bpm)`);
    } else if (payload.heartRate < 50) {
        score += 25;
        explanation.push(`[VITAL] Bradicardia (FC=${payload.heartRate} bpm)`);
    }

    if (payload.spo2 < 90) {
        score += 35;
        explanation.push(`[VITAL] Hipoxemia crítica (SpO2=${payload.spo2}%)`);
    } else if (payload.spo2 < 94) {
        score += 20;
        explanation.push(`[VITAL] Hipoxemia moderada (SpO2=${payload.spo2}%)`);
    }

    if (payload.temperature >= 39.5) {
        score += 25;
        explanation.push(`[VITAL] Febre alta (T=${payload.temperature}°C)`);
    } else if (payload.temperature >= 38) {
        score += 10;
        explanation.push(`[VITAL] Febre moderada (T=${payload.temperature}°C)`);
    } else if (payload.temperature < 35) {
        score += 20;
        explanation.push(`[VITAL] Hipotermia (T=${payload.temperature}°C)`);
    }

    if (payload.systolicBP < 80) {
        score += 35;
        explanation.push(`[VITAL] Hipotensão severa (PAS=${payload.systolicBP} mmHg)`);
    } else if (payload.systolicBP < 90) {
        score += 20;
        explanation.push(`[VITAL] Hipotensão moderada (PAS=${payload.systolicBP} mmHg)`);
    } else if (payload.systolicBP > 180) {
        score += 25;
        explanation.push(`[VITAL] Crise hipertensiva (PAS=${payload.systolicBP} mmHg)`);
    }

    (payload.chronicConditions || []).forEach((condition) => {
        const points = CONDITION_WEIGHTS[condition] || 5;
        score += points;
        explanation.push(`[DOENÇA] ${condition} (+${points} pts)`);
    });

    const criticalSymptoms = [];
    (payload.symptoms || []).forEach((key) => {
        const symptom = SYMPTOM_CATALOG[key] || { label: key, severity: 'MEDIUM', weight: 5 };
        score += symptom.weight;
        explanation.push(`[SINTOMA:${symptom.severity}] ${symptom.label} (+${symptom.weight} pts)`);
        if (symptom.severity === 'CRITICAL') criticalSymptoms.push(symptom);
    });

    if (criticalSymptoms.length >= 2) {
        const bonus = 15 * (criticalSymptoms.length - 1);
        score += bonus;
        explanation.push(`[CORRELAÇÃO] ${criticalSymptoms.length} sintomas críticos simultâneos (+${bonus} pts)`);
    }

    if (explanation.length === 0) {
        explanation.push('Nenhum fator de risco significativo identificado.');
    }

    const now = new Date().toISOString();
    return {
        triageId: `LOCAL-${Date.now()}`,
        patientId: payload.patientId,
        fullName: payload.fullName,
        riskScore: score,
        urgencyLevel: classifyScore(score),
        explanation,
        eventTimestamp: now,
        status: 'WAITING'
    };
}

function sortQueueByPriority(queue) {
    const riskWeights = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
    return [...queue].sort((a, b) => {
        const weightDiff = (riskWeights[b.urgencyLevel] || 0) - (riskWeights[a.urgencyLevel] || 0);
        if (weightDiff !== 0) return weightDiff;
        return new Date(a.eventTimestamp || a.timestamp) - new Date(b.eventTimestamp || b.timestamp);
    });
}

function estimateWaitMinutes(urgencyLevel, peopleAhead) {
    const baseMinutes = {
        CRITICAL: 5,
        HIGH: 15,
        MEDIUM: 35,
        LOW: 60
    };
    const perPatientMinutes = {
        CRITICAL: 5,
        HIGH: 8,
        MEDIUM: 10,
        LOW: 12
    };

    return (baseMinutes[urgencyLevel] || 45) + (peopleAhead * (perPatientMinutes[urgencyLevel] || 10));
}

function buildWaitInfo(triageId) {
    const orderedQueue = sortQueueByPriority(readLocalQueue().filter((item) => item.status !== 'ATTENDED'));
    const index = orderedQueue.findIndex((item) => item.triageId === triageId);
    if (index < 0) return null;

    const triage = orderedQueue[index];
    const peopleAhead = index;
    const estimatedMinutes = estimateWaitMinutes(triage.urgencyLevel, peopleAhead);

    return {
        position: index + 1,
        peopleAhead,
        estimatedMinutes,
        message: peopleAhead === 0
            ? 'Você é o próximo da fila.'
            : `${peopleAhead} paciente${peopleAhead > 1 ? 's' : ''} à sua frente.`
    };
}

window.MediFlowLocal = {
    login(cpf, password) {
        seedLocalUser();
        const normalizedCpf = normalizeCpf(cpf);
        const user = readLocalUsers().find((item) => normalizeCpf(item.cpf) === normalizedCpf);
        if (!user) throw new Error('Usuário não encontrado. Cadastre-se primeiro.');
        if (user.password !== password) throw new Error('Senha incorreta.');
        const { password: _password, ...profile } = {
            ...user,
            cpf: normalizedCpf,
            role: resolveUserRole({ ...user, cpf: normalizedCpf })
        };
        return profile;
    },

    register(payload) {
        const users = readLocalUsers();
        const normalizedCpf = normalizeCpf(payload.cpf);
        if (users.some((item) => normalizeCpf(item.cpf) === normalizedCpf)) {
            throw new Error('Este CPF já possui cadastro local.');
        }
        const user = {
            ...payload,
            cpf: normalizedCpf,
            role: payload.role === 'doctor' ? 'doctor' : 'patient'
        };
        users.push(user);
        writeLocalUsers(users);
        const { password: _password, ...profile } = user;
        return profile;
    },

    submitTriage(payload) {
        const triage = calculateLocalTriage(payload);
        const queue = readLocalQueue();
        queue.push(triage);
        writeLocalQueue(queue);
        return triage;
    },

    getQueue() {
        return sortQueueByPriority(readLocalQueue().filter((item) => item.status !== 'ATTENDED'));
    },

    getWaitInfo(triageId) {
        return buildWaitInfo(triageId);
    },

    attend(triageId) {
        const queue = readLocalQueue().map((item) => (
            item.triageId === triageId
                ? { ...item, status: 'ATTENDED', attendedAt: new Date().toISOString() }
                : item
        ));
        writeLocalQueue(queue);
    },

    clearQueue() {
        localStorage.removeItem('mediflow_queue');
    }
};

if (CONFIG.LOCAL_MODE) {
    seedLocalUser();
}
