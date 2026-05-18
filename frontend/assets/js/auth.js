// Lógica de Autenticação MediFlow
const tabLogin = document.getElementById('tabLogin');
const tabRegister = document.getElementById('tabRegister');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const patientFields = document.getElementById('patientFields');
const doctorFields = document.getElementById('doctorFields');
const roleInputs = document.querySelectorAll('input[name="role"]');

function syncRoleFields() {
    const selectedRole = document.querySelector('input[name="role"]:checked').value;
    const isDoctor = selectedRole === 'doctor';
    patientFields.classList.toggle('hidden', isDoctor);
    doctorFields.classList.toggle('hidden', !isDoctor);
}

roleInputs.forEach((input) => {
    input.addEventListener('change', syncRoleFields);
});

syncRoleFields();

// Alternar Abas
tabLogin.addEventListener('click', () => {
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
});

tabRegister.addEventListener('click', () => {
    tabRegister.classList.add('active');
    tabLogin.classList.remove('active');
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
});

// LOGIN
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const cpf = document.getElementById('loginCpf').value;
    const password = document.getElementById('loginPassword').value;

    if (window.MEDI_CONFIG.LOCAL_MODE) {
        try {
            const data = window.MediFlowLocal.login(cpf, password);
            localStorage.setItem('mediflow_user', JSON.stringify(data));
            alert(`Bem-vindo, ${data.fullName}!`);
            redirectByRole(data);
        } catch (error) {
            alert(error.message);
        }
        return;
    }

    const targetUrl = `${window.MEDI_CONFIG.API_URL}/auth/login`;
    console.log("Tentando Login na AWS em:", targetUrl);

    try {
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cpf, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Salva a sessão localmente
            localStorage.setItem('mediflow_user', JSON.stringify(data));
            alert(`Bem-vindo, ${data.fullName}!`);
            redirectByRole(data);
        } else {
            alert(data.message || "Erro ao entrar.");
        }
    } catch (error) {
        alert("Erro de conexão com a AWS.");
    }
});

// CADASTRO
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fullName = document.getElementById('regName').value;
    const cpf = document.getElementById('regCpf').value;
    const password = document.getElementById('regPassword').value;
    const role = document.querySelector('input[name="role"]:checked').value;
    const specialty = document.getElementById('regSpecialty').value.trim();
    const crm = document.getElementById('regCrm').value.trim();
    
    // Coleta Doenças Selecionadas
    const selectedDiseases = role === 'patient'
        ? Array.from(document.querySelectorAll('input[name="disease"]:checked')).map(cb => cb.value)
        : [];
    
    // Coleta Medicamentos
    const medicationsRaw = document.getElementById('regMedications').value;
    const medications = role === 'patient'
        ? medicationsRaw.split(',').map(m => m.trim()).filter(m => m !== "")
        : [];

    const payload = {
        fullName: fullName,
        cpf: cpf,
        password: password,
        role: role,
        chronicConditions: selectedDiseases,
        medications: medications,
        specialty: role === 'doctor' ? specialty : '',
        crm: role === 'doctor' ? crm : ''
    };

    if (window.MEDI_CONFIG.LOCAL_MODE) {
        try {
            const data = window.MediFlowLocal.register(payload);
            localStorage.setItem('mediflow_user', JSON.stringify(data));
            alert(`Cadastro local realizado. Bem-vindo, ${data.fullName}!`);
            redirectByRole(data);
        } catch (error) {
            alert(error.message);
        }
        return;
    }

    const targetUrl = `${window.MEDI_CONFIG.API_URL}/auth/register`;
    console.log("Tentando Cadastro na AWS em:", targetUrl);

    try {
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            const user = {
                fullName,
                cpf,
                role,
                chronicConditions: selectedDiseases,
                medications,
                specialty: payload.specialty,
                crm: payload.crm
            };
            localStorage.setItem('mediflow_user', JSON.stringify(user));
            alert("Cadastro realizado!");
            redirectByRole(user);
        } else {
            alert(data.message || "Erro no cadastro.");
        }
    } catch (error) {
        alert("Erro de conexão com a AWS.");
    }
});

function redirectByRole(user) {
    window.location.href = user.role === 'doctor' ? 'dashboard.html' : 'index.html';
}
