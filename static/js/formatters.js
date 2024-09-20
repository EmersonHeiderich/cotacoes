// static/js/formatters.js

document.addEventListener('DOMContentLoaded', function() {
    // Formata todos os elementos com data-frete
    const freteElements = document.querySelectorAll('[data-frete]');
    freteElements.forEach(element => {
        const frete = parseFloat(element.getAttribute('data-frete'));
        if (!isNaN(frete) && frete !== 0) {
            element.textContent = formatBRL(frete);
        }
    });

    // Formata todos os elementos com data-peso
    const pesoElements = document.querySelectorAll('[data-peso]');
    pesoElements.forEach(element => {
        const peso = parseFloat(element.getAttribute('data-peso'));
        if (!isNaN(peso)) {
            element.textContent = formatNumber(peso) + ' kg';
        }
    });

    // Formata todos os elementos com data-volume
    const volumeElements = document.querySelectorAll('[data-volume]');
    volumeElements.forEach(element => {
        const volume = parseFloat(element.getAttribute('data-volume'));
        if (!isNaN(volume)) {
            element.textContent = formatNumber(volume) + ' m³';
        }
    });

    // Formata todos os elementos com data-valor-nf (se existir)
    const valorNfElements = document.querySelectorAll('[data-valor-nf]');
    valorNfElements.forEach(element => {
        const valorNf = parseFloat(element.getAttribute('data-valor-nf'));
        if (!isNaN(valorNf)) {
            element.textContent = formatBRL(valorNf);
        }
    });

    // Formata o peso total e volume total no resumo
    const totalWeightElement = document.getElementById('total_weight');
    if (totalWeightElement) {
        const totalWeight = parseFloat(totalWeightElement.getAttribute('data-weight'));
        if (!isNaN(totalWeight)) {
            totalWeightElement.textContent = formatNumber(totalWeight) + ' kg';
        }
    }

    const totalVolumeElement = document.getElementById('total_volume');
    if (totalVolumeElement) {
        const totalVolume = parseFloat(totalVolumeElement.getAttribute('data-volume'));
        if (!isNaN(totalVolume)) {
            totalVolumeElement.textContent = formatNumber(totalVolume) + ' m³';
        }
    }
});

// Função para formatar números no padrão brasileiro de moeda
function formatBRL(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

// Função para formatar números no padrão brasileiro (sem moeda)
function formatNumber(value) {
    return new Intl.NumberFormat('pt-BR').format(value);
}