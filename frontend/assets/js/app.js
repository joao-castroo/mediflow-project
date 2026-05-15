// Motor de Triagem MediFlow - Integrado com Sessão
const triageForm = document.getElementById('triageForm');
const loader = document.getElementById('loader');
const resultModal = document.getElementById('resultModal');
const closeResult = document.getElementById('closeResult');
const btnLogout = document.getElementById('btnLogout');
const welcomeMsg = document.getElementById('welcomeMsg');

// Carrega dados do usuário logado
const activeUser = JSON.parse(localStorage.getItem('mediflow_user'));
if (activeUser) {
    welcomeMsg.innerHTML = `Olá, <strong>${activeUser.fullName.split(' ')[0]}</strong>`;
}

// LOGOUT
btnLogout.addEventListener('click', () => {
    localStorage.removeItem('mediflow_user');
    window.location.href = 'login.html';
});

// Seleção de Sintomas (Chips)
const symptomsGrid = document.getElementById('symptomsGrid');
const selectedSymptoms = new Set();

symptomsGrid.addEventListener('click', (e) => {
    const chip = e.target.closest('.symptom-chip');
    if (chip) {
        const key = chip.dataset.key;
        if (selectedSymptoms.has(key)) {
            selectedSymptoms.delete(key);
            chip.classList.remove('active');
        } else {
            selectedSymptoms.add(key);
            chip.classList.add('active');
        }
    }
});

// ENVIO DA TRIAGEM
triageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    loader.classList.remove('hidden');

    const payload = {
        patientId: activeUser.cpf,
        heartRate: parseFloat(document.getElementById('heartRate').value),
        spo2: parseFloat(document.getElementById('spo2').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        systolicBP: parseFloat(document.getElementById('systolicBP').value),
        symptoms: Array.from(selectedSymptoms),
        // O histórico vem do cadastro automático
        chronicConditions: activeUser.chronicConditions || [],
        medications: activeUser.medications || []
    };

    try {
        const response = await fetch(`${window.MEDI_CONFIG.API_URL}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            showResult(data);
        } else {
            alert(data.details || "Erro ao processar triagem na AWS.");
        }
    } catch (error) {
        alert("Erro de conexão: verifique sua internet ou a URL da API.");
    } finally {
        loader.classList.add('hidden');
    }
});

function showResult(data) {
    document.getElementById('urgencyTitle').innerText = data.urgencyLevel;
    document.getElementById('scoreValue').innerText = data.riskScore;
    
    const list = document.getElementById('explanationList');
    list.innerHTML = '';
    
    if (data.explanation && data.explanation.length > 0) {
        data.explanation.forEach(exp => {
            const li = document.createElement('li');
            li.innerText = exp;
            list.appendChild(li);
        });
    } else {
        list.innerHTML = '<li>Processamento concluído pela AWS.</li>';
    }

    const badge = document.getElementById('urgencyBadge');
    badge.className = `urgency-badge level-${data.urgencyLevel}`;
    
    resultModal.classList.remove('hidden');
}

closeResult.addEventListener('click', () => {
    resultModal.classList.add('hidden');
    // Agora o usuário permanece na página de triagem
});
