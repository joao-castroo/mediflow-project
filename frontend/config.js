// Configurações Globais do MediFlow
const CONFIG = {
    // URL da sua API AWS (Obtida no Output do SAM Deploy)
    // IMPORTANTE: Deixe apenas até o /Prod (sem o /triage no final)
    API_URL: 'https://c79cspmegc.execute-api.us-east-1.amazonaws.com/Prod'
};

// Exporta para uso em outros arquivos
window.MEDI_CONFIG = CONFIG;
