// Lógica de Autenticação MediFlow
const tabLogin = document.getElementById('tabLogin');
const tabRegister = document.getElementById('tabRegister');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

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
            window.location.href = 'index.html';
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
    
    // Coleta Doenças Selecionadas
    const selectedDiseases = Array.from(document.querySelectorAll('input[name="disease"]:checked')).map(cb => cb.value);
    
    // Coleta Medicamentos
    const medicationsRaw = document.getElementById('regMedications').value;
    const medications = medicationsRaw.split(',').map(m => m.trim()).filter(m => m !== "");

    const payload = {
        fullName: fullName,
        cpf: cpf,
        password: password,
        chronicConditions: selectedDiseases,
        medications: medications
    };

    const targetUrl = `${window.MEDI_CONFIG.API_URL}/auth/register`;
    console.log("Tentando Cadastro na AWS em:", targetUrl);

    try {
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cpf, password, fullName, chronicConditions: conditions })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Cadastro realizado! Agora faça login.");
            tabLogin.click();
        } else {
            alert(data.message || "Erro no cadastro.");
        }
    } catch (error) {
        alert("Erro de conexão com a AWS.");
    }
});
