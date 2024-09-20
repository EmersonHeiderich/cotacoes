// static/js/validation.js

document.addEventListener('DOMContentLoaded', function() {
    const identifierInput = document.getElementById('identifier');
    const invoiceValueInput = document.getElementById('invoice_value');

    // Função para remover caracteres não numéricos
    function onlyNumbers(value) {
        return value.replace(/\D/g, '');
    }

    // Função para formatar CNPJ
    function formatCNPJ(value) {
        if (value.length > 14) value = value.slice(0,14);
        let formatted = value;
        if (value.length > 12) {
            formatted = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2}).*/, "$1.$2.$3/$4-$5");
        } else if (value.length > 8) {
            formatted = value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4}).*/, "$1.$2.$3/$4");
        } else if (value.length > 5) {
            formatted = value.replace(/^(\d{2})(\d{3})(\d{3}).*/, "$1.$2.$3");
        } else if (value.length > 2) {
            formatted = value.replace(/^(\d{2})(\d{3}).*/, "$1.$2");
        }
        return formatted;
    }

    // Evento para validar e formatar o campo CNPJ
    identifierInput.addEventListener('input', function(e) {
        let value = onlyNumbers(e.target.value);
        e.target.value = formatCNPJ(value);

        // Validar o CNPJ
        if (value.length === 14) {
            if (!validateCNPJ(value)) {
                identifierInput.setCustomValidity("CNPJ inválido.");
                identifierInput.classList.add('is-invalid');
            } else {
                identifierInput.setCustomValidity("");
                identifierInput.classList.remove('is-invalid');
                identifierInput.classList.add('is-valid');
            }
        } else {
            identifierInput.setCustomValidity("");
            identifierInput.classList.remove('is-invalid');
            identifierInput.classList.remove('is-valid');
        }
    });

    // Função para validar CNPJ
    function validateCNPJ(cnpj) {
        let tamanho = cnpj.length - 2
        let numeros = cnpj.substring(0,tamanho);
        let digitos = cnpj.substring(tamanho);
        let soma = 0;
        let pos = tamanho - 7;
        for (let i = tamanho; i >= 1; i--) {
          soma += numeros.charAt(tamanho - i) * pos--;
          if (pos < 2)
                pos = 9;
        }
        let resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
        if (resultado != digitos.charAt(0))
            return false;

        tamanho = tamanho + 1;
        numeros = cnpj.substring(0,tamanho);
        soma = 0;
        pos = tamanho - 7;
        for (let i = tamanho; i >= 1; i--) {
          soma += numeros.charAt(tamanho - i) * pos--;
          if (pos < 2)
                pos = 9;
        }
        resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
        if (resultado != digitos.charAt(1))
              return false;
              
        return true;
    }

    // Função para formatar o valor da mercadoria em R$
    function formatInvoiceValue(value) {
        // Remove tudo o que não é dígito
        value = value.replace(/\D/g, '');

        // Converte para float e divide por 100 para obter as casas decimais
        let number = parseFloat(value) / 100;

        // Formata o número no padrão BR
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(number);
    }

    // Evento para formatar dinamicamente o campo "Valor da Mercadoria"
    invoiceValueInput.addEventListener('input', function(e) {
        let value = onlyNumbers(e.target.value);
        e.target.value = formatInvoiceValue(value);
    });
});