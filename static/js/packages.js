// static/js/packages.js

document.addEventListener('DOMContentLoaded', function() {
    const packageTypeSelect = document.getElementById('package_type');
    const predefinedPackagesTable = document.getElementById('predefined-packages-table');
    const customPackageFieldsDiv = document.getElementById('custom-package-fields');
    const packagesTableBody = document.querySelector('#packages-table tbody');
    const totalsParagraph = document.getElementById('totals');
    const requestQuotationsBtn = document.getElementById('request-quotations-btn');

    let packages = [];

    packageTypeSelect.addEventListener('change', function() {
        if (this.value === 'predefined') {
            predefinedPackagesTable.style.display = 'block';
            customPackageFieldsDiv.style.display = 'none';
        } else {
            predefinedPackagesTable.style.display = 'none';
            customPackageFieldsDiv.style.display = 'block';
        }
    });

    // Evento para habilitar/desabilitar o campo de novo peso
    document.querySelectorAll('.alter-weight-select').forEach(select => {
        select.addEventListener('change', function() {
            const row = this.closest('tr');
            const newWeightInput = row.querySelector('.new-weight-input');
            if (this.value === 'yes') {
                newWeightInput.disabled = false;
            } else {
                newWeightInput.disabled = true;
                newWeightInput.value = '';
            }
        });
    });

    // Botão para adicionar embalagens pré-definidas selecionadas
    const addPredefinedPackagesBtn = document.getElementById('add-predefined-packages-btn');
    addPredefinedPackagesBtn.addEventListener('click', function() {
        const quantities = document.querySelectorAll('.quantity-input');
        quantities.forEach(input => {
            const quantity = parseInt(input.value) || 0;
            if (quantity > 0) {
                const row = input.closest('tr');
                const packageId = input.name.replace('quantity_', '');
                const predefinedPackage = predefinedPackagesData[packageId];

                let peso = predefinedPackage.peso;

                const alterWeightSelect = row.querySelector('.alter-weight-select');
                if (alterWeightSelect.value === 'yes') {
                    const newWeightInput = row.querySelector('.new-weight-input');
                    const newPeso = parseFloat(newWeightInput.value);
                    if (isNaN(newPeso) || newPeso <= 0) {
                        alert('Por favor, insira um peso válido para a embalagem ' + predefinedPackage.nome);
                        return;
                    }
                    peso = newPeso;
                }

                const packageData = {
                    type: 'predefined',
                    package_id: packageId,
                    nome: predefinedPackage.nome,
                    comprimento: predefinedPackage.comprimento,
                    altura: predefinedPackage.altura,
                    largura: predefinedPackage.largura,
                    peso: peso,
                    quantidade: quantity
                };

                packages.push(packageData);
            }
        });
        updatePackagesTable();
        updateTotals();

        // Limpar os campos
        document.querySelectorAll('.quantity-input').forEach(input => input.value = '0');
        document.querySelectorAll('.alter-weight-select').forEach(select => select.value = 'no');
        document.querySelectorAll('.new-weight-input').forEach(input => {
            input.disabled = true;
            input.value = '';
        });
    });

    // Botão para adicionar embalagem personalizada
    const addCustomPackageBtn = document.getElementById('add-custom-package-btn');
    addCustomPackageBtn.addEventListener('click', function() {
        const nome = document.getElementById('custom_name').value;
        const comprimento = parseFloat(document.getElementById('custom_length').value);
        const altura = parseFloat(document.getElementById('custom_height').value);
        const largura = parseFloat(document.getElementById('custom_width').value);
        const peso = parseFloat(document.getElementById('custom_weight').value);
        const quantidade = parseInt(document.getElementById('quantity_custom').value) || 1;

        if (!nome || isNaN(comprimento) || isNaN(altura) || isNaN(largura) || isNaN(peso) ||
            comprimento <= 0 || altura <= 0 || largura <= 0 || peso <= 0 || quantidade <= 0) {
            alert('Por favor, preencha todos os campos da embalagem personalizada com valores válidos.');
            return;
        }

        const packageData = {
            type: 'custom',
            nome: nome,
            comprimento: comprimento,
            altura: altura,
            largura: largura,
            peso: peso,
            quantidade: quantidade
        };

        packages.push(packageData);
        updatePackagesTable();
        updateTotals();

        // Limpar os campos
        document.getElementById('custom_name').value = '';
        document.getElementById('custom_length').value = '';
        document.getElementById('custom_height').value = '';
        document.getElementById('custom_width').value = '';
        document.getElementById('custom_weight').value = '';
        document.getElementById('quantity_custom').value = '1';
    });

    function updatePackagesTable() {
        packagesTableBody.innerHTML = '';
        packages.forEach((pkg, index) => {
            const row = document.createElement('tr');

            const nomeCell = document.createElement('td');
            nomeCell.textContent = pkg.nome;
            row.appendChild(nomeCell);

            const dimensoesCell = document.createElement('td');
            dimensoesCell.textContent = `${pkg.comprimento} x ${pkg.altura} x ${pkg.largura}`;
            row.appendChild(dimensoesCell);

            const pesoCell = document.createElement('td');
            pesoCell.textContent = pkg.peso.toFixed(2);
            row.appendChild(pesoCell);

            const quantidadeCell = document.createElement('td');
            quantidadeCell.textContent = pkg.quantidade;
            row.appendChild(quantidadeCell);

            const actionsCell = document.createElement('td');
            const deleteBtn = document.createElement('button');
            deleteBtn.classList.add('btn', 'btn-danger', 'btn-sm');
            deleteBtn.textContent = 'Remover';
            deleteBtn.addEventListener('click', function() {
                packages.splice(index, 1);
                updatePackagesTable();
                updateTotals();
            });
            actionsCell.appendChild(deleteBtn);
            row.appendChild(actionsCell);

            packagesTableBody.appendChild(row);
        });
    }

    function updateTotals() {
        let totalWeight = 0;
        let totalVolume = 0;
        packages.forEach(pkg => {
            const quantity = pkg.quantidade;
            const weight = pkg.peso || 0;
            totalWeight += weight * quantity;

            let volume = (pkg.comprimento / 100) * (pkg.altura / 100) * (pkg.largura / 100);
            totalVolume += volume * quantity;
        });
        totalsParagraph.textContent = `Peso Total: ${totalWeight.toFixed(2)} kg | Volume Total: ${totalVolume.toFixed(4)} m³`;
    }

    // Submeter dados das embalagens e solicitar cotações
    requestQuotationsBtn.addEventListener('click', function() {
        if (packages.length === 0) {
            alert('Por favor, adicione ao menos uma embalagem.');
            return;
        }
        fetch(requestQuotationsBtn.dataset.url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(packages)
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else if (data.error) {
                alert(data.error);
            }
        })
        .catch(error => {
            console.error('Erro ao solicitar cotações:', error);
        });
    });
});
