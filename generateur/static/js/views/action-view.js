/**
 * Vue de création d'action simple
 */

let paramCounter = 0;

document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
});

/**
 * Initialise le formulaire
 */
function initializeForm() {
    const form = document.getElementById('action-form');
    form.addEventListener('submit', handleSubmit);

    // Mettre à jour la prévisualisation quand le nom change
    document.getElementById('nom').addEventListener('input', updateFilename);
}

/**
 * Met à jour le nom de fichier dans la prévisualisation
 */
function updateFilename() {
    const nom = document.getElementById('nom').value || '*';
    document.getElementById('preview-filename').textContent = `action_${nom}.py`;
}

/**
 * Ajoute un paramètre au constructeur
 */
function addParameter() {
    const container = document.getElementById('params-container');
    const id = paramCounter++;

    const row = document.createElement('div');
    row.className = 'param-row';
    row.id = `param-${id}`;
    row.innerHTML = `
        <input type="text" placeholder="Nom (ex: position)" data-param="name" required>
        <input type="text" placeholder="Type (ex: tuple)" data-param="type" value="Any">
        <input type="text" placeholder="Défaut (optionnel)" data-param="default">
        <button type="button" class="btn-remove" onclick="removeParameter(${id})">×</button>
    `;

    container.appendChild(row);
}

/**
 * Supprime un paramètre
 */
function removeParameter(id) {
    const row = document.getElementById(`param-${id}`);
    if (row) {
        row.remove();
    }
}

/**
 * Collecte les données du formulaire
 */
function collectFormData() {
    const nom = document.getElementById('nom').value.trim();
    const description = document.getElementById('description').value.trim();
    const conditionCode = document.getElementById('condition-code').value.trim();
    const runCode = document.getElementById('run-code').value.trim();
    const erreursApres = document.getElementById('erreurs-apres').value.trim();
    const erreursEchec = document.getElementById('erreurs-echec').value.trim();

    // Collecter les paramètres
    const parametres = [];
    document.querySelectorAll('.param-row').forEach(row => {
        const name = row.querySelector('[data-param="name"]').value.trim();
        const type = row.querySelector('[data-param="type"]').value.trim() || 'Any';
        const defaultVal = row.querySelector('[data-param="default"]').value.trim();

        if (name) {
            const param = { name, type };
            if (defaultVal) {
                // Essayer de parser comme JSON pour les valeurs numériques/booléennes
                try {
                    param.default = JSON.parse(defaultVal);
                } catch {
                    param.default = defaultVal;
                }
            }
            parametres.push(param);
        }
    });

    // Parser les erreurs
    const erreurs_verif_apres = erreursApres
        ? erreursApres.split(',').map(e => e.trim()).filter(e => e)
        : [];
    const erreurs_si_echec = erreursEchec
        ? erreursEchec.split(',').map(e => e.trim()).filter(e => e)
        : [];

    return {
        nom,
        description: description || null,
        condition_code: conditionCode || null,
        run_code: runCode,
        parametres,
        erreurs_verif_apres,
        erreurs_si_echec,
    };
}

/**
 * Prévisualise le code généré
 */
async function previewCode() {
    const data = collectFormData();

    if (!data.nom || !data.run_code) {
        showNotification('Veuillez remplir le nom et le code _run()', 'warning');
        return;
    }

    try {
        const result = await API.request('/actions/simple/preview', {
            method: 'POST',
            body: JSON.stringify(data),
        });

        if (result.success) {
            const preview = document.getElementById('code-preview');
            const filename = document.getElementById('preview-filename');

            filename.textContent = result.data.filename;
            preview.innerHTML = `<code>${formatCode(result.data.code)}</code>`;
        } else {
            showNotification(result.error?.message || 'Erreur de prévisualisation', 'error');
        }
    } catch (error) {
        console.error('Preview error:', error);
        showNotification('Erreur de prévisualisation', 'error');
    }
}

/**
 * Gère la soumission du formulaire
 */
async function handleSubmit(event) {
    event.preventDefault();

    const data = collectFormData();

    if (!data.nom || !data.run_code) {
        showNotification('Veuillez remplir le nom et le code _run()', 'warning');
        return;
    }

    try {
        const result = await API.request('/actions/simple/generate', {
            method: 'POST',
            body: JSON.stringify(data),
        });

        if (result.success) {
            showResultModal(
                'Action générée',
                `<p>L'action <strong>${result.data.class_name}</strong> a été créée avec succès.</p>
                 <p><strong>Fichier:</strong> ${result.data.filepath}</p>`,
                true
            );
        } else {
            showResultModal(
                'Erreur',
                `<p>${result.error?.message || 'Erreur lors de la génération'}</p>`,
                false
            );
        }
    } catch (error) {
        console.error('Submit error:', error);
        showResultModal('Erreur', '<p>Erreur lors de la génération</p>', false);
    }
}

/**
 * Affiche le modal de résultat
 */
function showResultModal(title, content, success) {
    document.getElementById('result-title').textContent = title;
    document.getElementById('result-body').innerHTML = content;
    document.getElementById('result-modal').classList.remove('hidden');
}

/**
 * Ferme le modal de résultat
 */
function closeResultModal() {
    document.getElementById('result-modal').classList.add('hidden');
}

/**
 * Formate le code pour l'affichage
 */
function formatCode(code) {
    return code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Affiche une notification
 */
function showNotification(message, type = 'info') {
    if (window.showNotification && typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        alert(message);
    }
}
