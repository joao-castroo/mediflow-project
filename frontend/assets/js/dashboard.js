// ==========================================
// DASHBOARD LOGIC (Fila de Pacientes REAL)
// ==========================================

const queueList = document.getElementById('queueList');
const statTotal = document.getElementById('statTotal');
const statCritical = document.getElementById('statCritical');
// Memória de alertas para não repetir o mesmo paciente
const notifiedTriageIds = new Set();
const emergencyOverlay = document.getElementById('emergencyOverlay');
const emergencyPatientName = document.getElementById('emergencyPatientName');
const closeEmergencyBtn = document.getElementById('closeEmergency');
const btnAttendNow = document.getElementById('btnAttendNow');

let currentEmergencyTriageId = null;

closeEmergencyBtn.addEventListener('click', () => {
    emergencyOverlay.classList.add('hidden');
    currentEmergencyTriageId = null;
});

btnAttendNow.addEventListener('click', () => {
    if (currentEmergencyTriageId) {
        emergencyOverlay.classList.add('hidden');
        callPatient(currentEmergencyTriageId);
    }
});

async function loadQueue() {
    const apiUrl = window.MEDI_CONFIG.API_URL;

    try {
        // Chamada Real para a AWS
        const response = await fetch(apiUrl + '/triage/queue');
        if (!response.ok) throw new Error("Erro ao buscar fila da AWS.");
        const queue = await response.json();
        renderQueue(queue);
    } catch (error) {
        console.error("Erro na API:", error);
    }
}

function sortQueue(a, b) {
    const riskWeights = { 'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1 };
    const weightA = riskWeights[a.urgencyLevel] || 0;
    const weightB = riskWeights[b.urgencyLevel] || 0;
    if (weightA !== weightB) return weightB - weightA;
    return new Date(a.eventTimestamp || a.timestamp) - new Date(b.eventTimestamp || b.timestamp);
}

function formatTime(isoString) {
    if (!isoString) return "--:--";
    const d = new Date(isoString);
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function renderQueue(queue) {
    queueList.innerHTML = '';
    let criticalCount = 0;

    if (queue.length === 0) {
        queueList.innerHTML = `<div class="empty-state"><i class="fa-solid fa-bed-pulse"></i><p>Fila vazia.</p></div>`;
    } else {
        queue.forEach((patient) => {
            if (patient.urgencyLevel === 'CRITICAL') {
                criticalCount++;
                // Se for um novo paciente crítico, dispara o alerta!
                if (!notifiedTriageIds.has(patient.triageId)) {
                    showEmergencyAlert(patient);
                }
            }
            const card = document.createElement('div');
            card.className = `queue-card level-${patient.urgencyLevel}`;
            card.innerHTML = `
                <div class="queue-card-left">
                    <div class="queue-time"><i class="fa-regular fa-clock"></i> ${formatTime(patient.eventTimestamp || patient.timestamp)}</div>
                    <div class="queue-patient">
                        <h3>${patient.fullName || 'CPF: ' + patient.patientId}</h3>
                        <span class="queue-score">Score: ${patient.riskScore}</span>
                    </div>
                </div>
                <div class="queue-card-right">
                    <div class="queue-urgency">${patient.urgencyLevel}</div>
                    <button class="call-btn" onclick="callPatient('${patient.triageId}')"><i class="fa-solid fa-bullhorn"></i> Atender</button>
                </div>
            `;
            queueList.appendChild(card);
        });
    }
    statTotal.innerText = queue.length;
    statCritical.innerText = criticalCount;
}

window.callPatient = async function(triageId) {
    const apiUrl = window.MEDI_CONFIG.API_URL;

    try {
        if (!confirm("Confirmar atendimento do paciente?")) return;
        
        const response = await fetch(`${apiUrl}/triage/${triageId}/attend`, { method: 'POST' });
        if (!response.ok) throw new Error("Erro ao registrar atendimento.");
        alert("Atendimento registrado e arquivado no S3!");
        loadQueue();
    } catch (error) {
        alert("Erro: " + error.message);
    }
}

document.getElementById('clearQueueBtn').addEventListener('click', () => {
    localStorage.removeItem('mediflow_queue');
    loadQueue();
});

function showEmergencyAlert(patient) {
    notifiedTriageIds.add(patient.triageId);
    currentEmergencyTriageId = patient.triageId;
    emergencyPatientName.innerText = patient.fullName || 'CPF: ' + patient.patientId;
    emergencyOverlay.classList.remove('hidden');
    
    // Tenta tocar um som de alerta (navegadores podem bloquear se não houver interação prévia)
    try {
        const audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
        audio.play();
    } catch (e) {
        console.warn("Som de alerta bloqueado pelo navegador.");
    }
}

loadQueue();
// Frequência de atualização Turbinada (2 segundos) para sensação de Real-Time
setInterval(loadQueue, 2000);

// Indicador visual de que o sistema está monitorando
const header = document.querySelector('header');
const liveIndicator = document.createElement('div');
liveIndicator.innerHTML = '<span class="live-dot"></span> LIVE MONITORING';
liveIndicator.className = 'live-indicator';
header.appendChild(liveIndicator);
