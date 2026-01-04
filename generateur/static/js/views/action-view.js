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

// =====================================================
// Gestion de la modale de création d'erreur
// =====================================================

/**
 * Ouvre la modale de création d'erreur
 */
function openCreateErreurModal() {
    document.getElementById('create-erreur-modal').classList.remove('hidden');
    document.getElementById('create-erreur-form').reset();
    toggleErreurTypeFields();
}

/**
 * Ferme la modale de création d'erreur
 */
function closeCreateErreurModal() {
    document.getElementById('create-erreur-modal').classList.add('hidden');
}

/**
 * Toggle les champs selon le type d'erreur sélectionné
 */
function toggleErreurTypeFields() {
    const type = document.getElementById('erreur-type').value;
    const imageGroup = document.getElementById('erreur-image-group');
    const texteGroup = document.getElementById('erreur-texte-group');

    if (type === 'image') {
        imageGroup.classList.remove('hidden');
        texteGroup.classList.add('hidden');
        document.getElementById('erreur-image').required = true;
        document.getElementById('erreur-texte').required = false;
    } else {
        imageGroup.classList.add('hidden');
        texteGroup.classList.remove('hidden');
        document.getElementById('erreur-image').required = false;
        document.getElementById('erreur-texte').required = true;
    }
}

/**
 * Soumet le formulaire de création d'erreur
 */
async function submitCreateErreur(event) {
    event.preventDefault();

    const type = document.getElementById('erreur-type').value;
    const data = {
        nom: document.getElementById('erreur-nom').value.trim(),
        type: type,
        message: document.getElementById('erreur-message').value.trim(),
        categorie: document.getElementById('erreur-categorie').value,
        priorite: parseInt(document.getElementById('erreur-priorite').value) || 50,
        retry_action_originale: document.getElementById('erreur-retry').checked,
        exclure_fenetre: 0,
    };

    // Ajouter image ou texte selon le type
    if (type === 'image') {
        data.image = document.getElementById('erreur-image').value.trim();
    } else {
        data.texte = document.getElementById('erreur-texte').value.trim();
    }

    // Ajouter l'action de correction si sélectionnée
    const action = document.getElementById('erreur-action').value;
    if (action) {
        data.action_correction = action;
    }

    try {
        const result = await API.createErreur(data);

        if (result.success) {
            closeCreateErreurModal();
            showNotification(`Erreur '${data.nom}' créée avec succès`, 'success');

            // Recharger les erreurs
            await loadErreurs();
        } else {
            showNotification(result.error?.message || 'Erreur lors de la création', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur lors de la création', 'error');
    }
}

/**
 * Suggère des erreurs pertinentes via l'IA Claude
 */
async function suggestErreursIA() {
    // Construire la description de l'action à partir du formulaire
    const nom = document.getElementById('nom').value.trim();
    const description = document.getElementById('description').value.trim();
    const runCode = document.getElementById('run-code').value.trim();

    if (!nom && !description && !runCode) {
        showNotification('Veuillez remplir au moins le nom ou la description de l\'action', 'warning');
        return;
    }

    // Construire la description pour l'IA
    let actionDescription = '';
    if (nom) actionDescription += `Nom: ${nom}\n`;
    if (description) actionDescription += `Description: ${description}\n`;
    if (runCode) actionDescription += `Code:\n${runCode}\n`;

    showNotification('Analyse en cours...', 'info');

    try {
        const result = await API.suggestErreurs(actionDescription);

        if (result.success && result.data) {
            // Appliquer les suggestions
            const { erreurs_verif_apres, erreurs_si_echec, explication } = result.data;

            // Sélectionner les erreurs suggérées pour "après"
            if (erreurs_verif_apres && erreurs_verif_apres.length > 0) {
                clearErreursApres();
                erreurs_verif_apres.forEach(nom => {
                    selectedErreursApres.add(nom);
                    const checkbox = document.getElementById(`erreur-apres-${nom}`);
                    if (checkbox) checkbox.checked = true;
                });
                updateSelectedTags('apres');
            }

            // Sélectionner les erreurs suggérées pour "si échec"
            if (erreurs_si_echec && erreurs_si_echec.length > 0) {
                clearErreursEchec();
                erreurs_si_echec.forEach(nom => {
                    selectedErreursEchec.add(nom);
                    const checkbox = document.getElementById(`erreur-echec-${nom}`);
                    if (checkbox) checkbox.checked = true;
                });
                updateSelectedTags('echec');
            }

            // Afficher l'explication
            if (explication) {
                showNotification(`IA: ${explication}`, 'success');
            } else {
                showNotification('Suggestions appliquées', 'success');
            }
        } else {
            showNotification(result.error?.message || 'Erreur lors de la suggestion', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur lors de la suggestion', 'error');
    }
}
