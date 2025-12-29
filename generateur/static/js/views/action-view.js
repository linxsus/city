/**
 * Vue de création d'action simple
 */

let paramCounter = 0;
let allErreurs = [];
let selectedErreursApres = new Set();
let selectedErreursEchec = new Set();

document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    loadErreurs();
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
 * Charge les erreurs depuis l'API
 */
async function loadErreurs() {
    try {
        const result = await API.getAllErreurs();
        if (result.success) {
            allErreurs = result.data.erreurs;
            renderErreurSelectors();
        } else {
            console.error('Erreur chargement erreurs:', result.error);
            showErreurLoadError();
        }
    } catch (error) {
        console.error('Erreur:', error);
        showErreurLoadError();
    }
}

/**
 * Affiche une erreur de chargement
 */
function showErreurLoadError() {
    const msg = '<p class="help-text" style="padding: var(--spacing-sm); color: var(--color-error);">Impossible de charger les erreurs</p>';
    document.getElementById('erreurs-apres-selector').innerHTML = msg;
    document.getElementById('erreurs-echec-selector').innerHTML = msg;
}

/**
 * Groupe les erreurs par catégorie
 */
function groupErreursByCategory(erreurs) {
    const grouped = {};
    const categoryLabels = {
        'connexion': 'Connexion',
        'jeu': 'Jeu',
        'popup': 'Popups / Publicités',
        'systeme': 'Système / BlueStacks',
        'autre': 'Autres'
    };

    erreurs.forEach(erreur => {
        const cat = erreur.categorie || 'autre';
        if (!grouped[cat]) {
            grouped[cat] = {
                label: categoryLabels[cat] || cat,
                erreurs: []
            };
        }
        grouped[cat].erreurs.push(erreur);
    });

    return grouped;
}

/**
 * Rend les sélecteurs d'erreurs
 */
function renderErreurSelectors() {
    const grouped = groupErreursByCategory(allErreurs);

    document.getElementById('erreurs-apres-selector').innerHTML = renderErreurSelector(grouped, 'apres');
    document.getElementById('erreurs-echec-selector').innerHTML = renderErreurSelector(grouped, 'echec');
}

/**
 * Rend un sélecteur d'erreurs
 */
function renderErreurSelector(grouped, type) {
    const categories = Object.entries(grouped);
    if (categories.length === 0) {
        return '<p class="help-text" style="padding: var(--spacing-sm);">Aucune erreur disponible</p>';
    }

    return categories.map(([cat, data]) => `
        <div class="erreur-category" data-category="${cat}">
            <div class="erreur-category-header" onclick="toggleCategory(this)">
                <span>${data.label} (${data.erreurs.length})</span>
                <span class="toggle-icon">▼</span>
            </div>
            <div class="erreur-list">
                ${data.erreurs.map(erreur => renderErreurItem(erreur, type)).join('')}
            </div>
        </div>
    `).join('');
}

/**
 * Rend un item d'erreur
 */
function renderErreurItem(erreur, type) {
    const checkboxId = `erreur-${type}-${erreur.nom}`;
    const badges = [];

    if (erreur.retry_action_originale) {
        badges.push('<span class="erreur-badge retry">retry</span>');
    }
    if (erreur.priorite >= 80) {
        badges.push(`<span class="erreur-badge">P${erreur.priorite}</span>`);
    }

    return `
        <div class="erreur-item">
            <input type="checkbox" id="${checkboxId}"
                   data-erreur="${erreur.nom}"
                   data-type="${type}"
                   onchange="toggleErreurSelection('${erreur.nom}', '${type}', this.checked)">
            <label for="${checkboxId}" class="erreur-info">
                <div class="erreur-name">${erreur.nom} ${badges.join('')}</div>
                <div class="erreur-message">${erreur.message}</div>
            </label>
        </div>
    `;
}

/**
 * Toggle une catégorie
 */
function toggleCategory(header) {
    const category = header.parentElement;
    category.classList.toggle('collapsed');
}

/**
 * Toggle la sélection d'une erreur
 */
function toggleErreurSelection(nom, type, checked) {
    const set = type === 'apres' ? selectedErreursApres : selectedErreursEchec;

    if (checked) {
        set.add(nom);
    } else {
        set.delete(nom);
    }

    updateSelectedTags(type);
}

/**
 * Met à jour les tags des erreurs sélectionnées
 */
function updateSelectedTags(type) {
    const set = type === 'apres' ? selectedErreursApres : selectedErreursEchec;
    const container = document.getElementById(`erreurs-${type}-selected`);

    if (set.size === 0) {
        container.innerHTML = '';
        return;
    }

    container.innerHTML = Array.from(set).map(nom => `
        <span class="selected-tag">
            ${nom}
            <span class="remove-tag" onclick="removeErreurSelection('${nom}', '${type}')">&times;</span>
        </span>
    `).join('');
}

/**
 * Supprime une erreur de la sélection
 */
function removeErreurSelection(nom, type) {
    const set = type === 'apres' ? selectedErreursApres : selectedErreursEchec;
    set.delete(nom);

    // Décocher la checkbox
    const checkbox = document.getElementById(`erreur-${type}-${nom}`);
    if (checkbox) {
        checkbox.checked = false;
    }

    updateSelectedTags(type);
}

/**
 * Charge les erreurs par défaut pour "après succès"
 */
async function loadDefaultErreursApres() {
    try {
        const result = await API.getErreursVerifApresDefaults();
        if (result.success) {
            result.data.erreurs.forEach(nom => {
                selectedErreursApres.add(nom);
                const checkbox = document.getElementById(`erreur-apres-${nom}`);
                if (checkbox) checkbox.checked = true;
            });
            updateSelectedTags('apres');
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

/**
 * Charge les erreurs par défaut pour "si échec"
 */
async function loadDefaultErreursEchec() {
    try {
        const result = await API.getErreursSiEchecDefaults();
        if (result.success) {
            result.data.erreurs.forEach(nom => {
                selectedErreursEchec.add(nom);
                const checkbox = document.getElementById(`erreur-echec-${nom}`);
                if (checkbox) checkbox.checked = true;
            });
            updateSelectedTags('echec');
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

/**
 * Efface les erreurs "après succès"
 */
function clearErreursApres() {
    selectedErreursApres.clear();
    document.querySelectorAll('[data-type="apres"]').forEach(cb => cb.checked = false);
    updateSelectedTags('apres');
}

/**
 * Efface les erreurs "si échec"
 */
function clearErreursEchec() {
    selectedErreursEchec.clear();
    document.querySelectorAll('[data-type="echec"]').forEach(cb => cb.checked = false);
    updateSelectedTags('echec');
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
    const retrySiErreurNonIdentifiee = document.getElementById('retry-si-erreur-non-identifiee')?.checked || false;

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

    return {
        nom,
        description: description || null,
        condition_code: conditionCode || null,
        run_code: runCode,
        parametres,
        erreurs_verif_apres: Array.from(selectedErreursApres),
        erreurs_si_echec: Array.from(selectedErreursEchec),
        retry_si_erreur_non_identifiee: retrySiErreurNonIdentifiee,
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
