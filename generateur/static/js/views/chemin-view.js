/**
 * Vue de création de chemin
 */

// Fonction utilitaire fallback
if (typeof formatCode === 'undefined') {
    window.formatCode = function(code) {
        return code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    };
}

let actions = [];
let availableStates = [];
let availableActions = { base: [], simples: [], longues: [] };

document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    loadAvailableActions();
    loadAvailableStates().then(() => {
        loadFromUrlParams();
    });
});

/**
 * Charge les données depuis sessionStorage (pour duplication)
 */
function loadFromUrlParams() {
    const params = new URLSearchParams(window.location.search);

    if (!params.has('duplicate')) return;

    // Récupérer les données de duplication depuis sessionStorage
    const stored = sessionStorage.getItem('duplicate_chemin');
    if (!stored) {
        if (typeof showNotification !== 'undefined') {
            showNotification('Données de duplication non trouvées', 'warning');
        }
        return;
    }

    try {
        const data = JSON.parse(stored);
        sessionStorage.removeItem('duplicate_chemin'); // Nettoyer après lecture

        if (typeof showNotification !== 'undefined') {
            showNotification(`Duplication du chemin "${data.source}"`, 'info');
        }

        // Pré-remplir le nom
        if (data.nom) {
            document.getElementById('nom-chemin').value = data.nom;
        }

        // Pré-remplir l'état initial
        if (data.etat_initial) {
            document.getElementById('etat-initial').value = data.etat_initial;
        }

        // Pré-remplir l'état de sortie
        if (data.etat_sortie) {
            document.getElementById('etat-sortie').value = data.etat_sortie;
            loadExitSuggestions();
        }

        // Afficher le code source original dans la prévisualisation
        if (data.code_source) {
            setTimeout(() => {
                const preview = document.getElementById('code-preview');
                const filename = document.getElementById('preview-filename');
                if (preview && filename) {
                    filename.textContent = `Code original: ${data.source}`;
                    preview.innerHTML = `<code>${formatCode(data.code_source)}</code>`;
                }
            }, 100);
        }

        // Afficher info sur les templates utilisés
        if (data.templates && data.templates.length > 0) {
            console.log('Templates du chemin source:', data.templates);
        }

    } catch (e) {
        console.error('Erreur parsing données duplication:', e);
        if (typeof showNotification !== 'undefined') {
            showNotification('Erreur lors de la duplication', 'error');
        }
    }
}

/**
 * Initialise le formulaire
 */
function initializeForm() {
    // Boutons d'ajout d'action
    document.querySelectorAll('.add-action-bar button').forEach(btn => {
        btn.addEventListener('click', () => {
            const actionType = btn.dataset.action;
            openActionModal(actionType);
        });
    });

    // État de sortie -> suggestions
    document.getElementById('etat-sortie').addEventListener('change', loadExitSuggestions);

    // Boutons
    document.getElementById('btn-preview')?.addEventListener('click', previewCode);
    document.getElementById('btn-validate')?.addEventListener('click', validateForm);
    document.getElementById('btn-save-action')?.addEventListener('click', saveAction);

    // Formulaire
    document.getElementById('chemin-form').addEventListener('submit', handleSubmit);
}

/**
 * Charge les états disponibles
 */
async function loadAvailableStates() {
    const result = await API.getAvailableStates();

    if (result.success) {
        availableStates = result.data.states;
        populateStateSelects();
    }
}

/**
 * Charge les actions disponibles
 */
async function loadAvailableActions() {
    try {
        const result = await API.request('/actions/available');

        if (result.success) {
            availableActions = result.data;
            populateActionsDropdown();
        }
    } catch (error) {
        console.error('Error loading available actions:', error);
    }
}

/**
 * Remplit le dropdown des actions personnalisées
 */
function populateActionsDropdown() {
    const optgroupBase = document.getElementById('optgroup-base');
    const optgroupCustom = document.getElementById('optgroup-custom');

    if (!optgroupBase || !optgroupCustom) return;

    // Actions de base (sauf celles déjà en boutons)
    const baseActionsFiltered = availableActions.base.filter(
        a => !['ActionBouton', 'ActionAttendre', 'ActionTexte'].includes(a.nom_classe)
    );

    optgroupBase.innerHTML = baseActionsFiltered.map(a =>
        `<option value="${a.nom_classe}" data-type="base">${a.nom_classe} - ${a.description || ''}</option>`
    ).join('');

    // Actions personnalisées (simples)
    const customOptions = availableActions.simples.map(a =>
        `<option value="${a.nom_classe}" data-type="simple">${a.nom_classe}</option>`
    ).join('');

    optgroupCustom.innerHTML = customOptions || '<option disabled>Aucune action personnalisée</option>';
}

/**
 * Ajoute une action personnalisée depuis le dropdown
 */
function addCustomAction() {
    const select = document.getElementById('custom-action-select');
    const actionClass = select.value;

    if (!actionClass) return;

    // Trouver l'action dans les listes
    let actionInfo = availableActions.base.find(a => a.nom_classe === actionClass);
    if (!actionInfo) {
        actionInfo = availableActions.simples.find(a => a.nom_classe === actionClass);
    }

    if (actionInfo) {
        openCustomActionModal(actionInfo);
    }

    // Réinitialiser le select
    select.value = '';
}

/**
 * Ouvre le modal pour une action personnalisée
 */
function openCustomActionModal(actionInfo) {
    const modal = document.getElementById('action-modal');
    const title = document.getElementById('action-modal-title');
    const body = document.getElementById('action-modal-body');

    title.textContent = `Ajouter: ${actionInfo.nom_classe}`;

    // Formulaire générique pour les actions personnalisées
    let formHtml = `
        <input type="hidden" id="action-type" value="${actionInfo.nom_classe}">
        <input type="hidden" id="action-custom" value="true">
        <div class="form-group">
            <p class="help-text">${actionInfo.description || 'Action personnalisée'}</p>
        </div>
    `;

    // Pour ActionLog, ajouter un champ message
    if (actionInfo.nom_classe === 'ActionLog') {
        formHtml += `
            <div class="form-group">
                <label for="action-message">Message *</label>
                <input type="text" id="action-message" required placeholder="Message à logger">
            </div>
        `;
    }

    body.innerHTML = formHtml;
    modal.classList.remove('hidden');
}

/**
 * Remplit les listes déroulantes d'états
 */
function populateStateSelects() {
    const etatInitial = document.getElementById('etat-initial');
    const etatSortie = document.getElementById('etat-sortie');

    const options = availableStates.map(s => `<option value="${s}">${s}</option>`).join('');

    etatInitial.innerHTML = `<option value="">Sélectionner...</option>${options}`;
    etatSortie.innerHTML = `<option value="">Sélectionner...</option>${options}`;
}

/**
 * Charge les suggestions d'états de sortie
 */
async function loadExitSuggestions() {
    const etatSortie = document.getElementById('etat-sortie').value;
    const container = document.getElementById('etats-sortie-possibles');

    if (!etatSortie) {
        container.innerHTML = '<p class="text-muted">Sélectionnez d\'abord l\'état de sortie</p>';
        return;
    }

    const result = await API.suggestExitStates(etatSortie);

    if (result.success) {
        const suggestions = result.data.suggestions;

        if (suggestions.length > 0) {
            container.innerHTML = suggestions.map(s => `
                <label>
                    <input type="checkbox" name="etats_sortie_possibles" value="${s}">
                    ${s}
                </label>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">Aucun popup/erreur suggéré</p>';
        }
    }
}

/**
 * Ouvre le modal d'ajout d'action
 */
async function openActionModal(actionType) {
    const modal = document.getElementById('action-modal');
    const title = document.getElementById('action-modal-title');
    const body = document.getElementById('action-modal-body');

    title.textContent = `Ajouter: ${actionType}`;

    let formHtml = '';

    switch (actionType) {
        case 'ActionBouton':
            formHtml = `
                <input type="hidden" id="action-type" value="ActionBouton">
                <div class="form-group">
                    <label for="action-template-select">Sélectionner un template existant</label>
                    <select id="action-template-select" onchange="onTemplateSelect()">
                        <option value="">Chargement...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="action-template">Ou entrer le chemin manuellement *</label>
                    <input type="text" id="action-template" placeholder="ex: boutons/ok.png">
                </div>
                <div id="template-preview" class="template-preview hidden">
                    <img id="template-preview-img" alt="Aperçu du template" />
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="action-offset-x">Décalage X</label>
                        <input type="number" id="action-offset-x" value="0">
                    </div>
                    <div class="form-group">
                        <label for="action-offset-y">Décalage Y</label>
                        <input type="number" id="action-offset-y" value="0">
                    </div>
                </div>
                <div class="form-group">
                    <label for="action-threshold">Seuil de détection</label>
                    <input type="number" id="action-threshold" value="0.8" min="0.5" max="1" step="0.05">
                </div>
            `;
            break;

        case 'ActionAttendre':
            formHtml = `
                <input type="hidden" id="action-type" value="ActionAttendre">
                <div class="form-group">
                    <label for="action-duree">Durée (secondes) *</label>
                    <input type="number" id="action-duree" required value="1" min="0.1" max="300" step="0.1">
                </div>
            `;
            break;

        case 'ActionTexte':
            formHtml = `
                <input type="hidden" id="action-type" value="ActionTexte">
                <div class="form-group">
                    <label for="action-texte">Texte à cliquer *</label>
                    <input type="text" id="action-texte" required placeholder="ex: Confirmer">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="action-offset-x">Décalage X</label>
                        <input type="number" id="action-offset-x" value="0">
                    </div>
                    <div class="form-group">
                        <label for="action-offset-y">Décalage Y</label>
                        <input type="number" id="action-offset-y" value="0">
                    </div>
                </div>
            `;
            break;
    }

    body.innerHTML = formHtml;
    modal.classList.remove('hidden');

    // Charger les templates si c'est un ActionBouton
    if (actionType === 'ActionBouton') {
        loadTemplatesList();
    }
}

/**
 * Charge la liste des templates disponibles
 */
async function loadTemplatesList() {
    const select = document.getElementById('action-template-select');
    if (!select) return;

    const result = await API.getTemplatesList();

    if (result.success) {
        const templates = result.data.templates;

        // Grouper par dossier
        const grouped = {};
        templates.forEach(t => {
            const folder = t.folder || '(racine)';
            if (!grouped[folder]) grouped[folder] = [];
            grouped[folder].push(t);
        });

        // Construire les options avec optgroup
        let html = '<option value="">-- Sélectionner un template --</option>';

        Object.keys(grouped).sort().forEach(folder => {
            html += `<optgroup label="${folder}">`;
            grouped[folder].forEach(t => {
                html += `<option value="${t.path}">${t.name}</option>`;
            });
            html += '</optgroup>';
        });

        select.innerHTML = html;
    } else {
        select.innerHTML = '<option value="">Erreur de chargement</option>';
    }
}

/**
 * Gère la sélection d'un template dans la liste
 */
function onTemplateSelect() {
    const select = document.getElementById('action-template-select');
    const input = document.getElementById('action-template');
    const preview = document.getElementById('template-preview');
    const previewImg = document.getElementById('template-preview-img');

    if (select.value) {
        input.value = select.value;

        // Afficher la prévisualisation
        previewImg.src = `/api/images/templates/${encodeURIComponent(select.value)}`;
        preview.classList.remove('hidden');
    } else {
        preview.classList.add('hidden');
    }
}

/**
 * Ferme le modal d'action
 */
function closeActionModal() {
    document.getElementById('action-modal').classList.add('hidden');
}

/**
 * Sauvegarde l'action du modal
 */
function saveAction() {
    const type = document.getElementById('action-type').value;
    const isCustom = document.getElementById('action-custom')?.value === 'true';
    let action = { type, parametres: {}, ordre: actions.length };

    switch (type) {
        case 'ActionBouton':
            const template = document.getElementById('action-template').value.trim();
            if (!template) {
                showNotification('Le chemin du template est requis', 'warning');
                return;
            }
            action.parametres = {
                template_path: template,
                offset_x: parseInt(document.getElementById('action-offset-x').value) || 0,
                offset_y: parseInt(document.getElementById('action-offset-y').value) || 0,
                threshold: parseFloat(document.getElementById('action-threshold').value) || 0.8,
            };
            break;

        case 'ActionAttendre':
            const duree = parseFloat(document.getElementById('action-duree').value);
            if (!duree || duree <= 0) {
                showNotification('La durée doit être positive', 'warning');
                return;
            }
            action.parametres = { duree };
            break;

        case 'ActionTexte':
            const texte = document.getElementById('action-texte').value.trim();
            if (!texte) {
                showNotification('Le texte est requis', 'warning');
                return;
            }
            action.parametres = {
                texte_recherche: texte,
                offset_x: parseInt(document.getElementById('action-offset-x').value) || 0,
                offset_y: parseInt(document.getElementById('action-offset-y').value) || 0,
            };
            break;

        case 'ActionLog':
            const message = document.getElementById('action-message')?.value.trim();
            if (!message) {
                showNotification('Le message est requis', 'warning');
                return;
            }
            action.parametres = { message };
            break;

        default:
            // Actions personnalisées - ajouter sans paramètres spécifiques
            if (isCustom) {
                action.parametres = { custom: true };
            }
            break;
    }

    actions.push(action);
    renderActionsList();
    closeActionModal();
}

/**
 * Affiche la liste des actions
 */
function renderActionsList() {
    const container = document.getElementById('actions-list');

    if (actions.length === 0) {
        container.innerHTML = '<p class="text-muted" style="text-align: center; padding: 20px;">Aucune action. Utilisez les boutons ci-dessous pour en ajouter.</p>';
        return;
    }

    container.innerHTML = actions.map((action, index) => {
        let icon = '⚡';
        let details = '';

        switch (action.type) {
            case 'ActionBouton':
                icon = '🖱️';
                details = `Clic sur "${action.parametres.template_path}"`;
                break;
            case 'ActionAttendre':
                icon = '⏱️';
                details = `Attendre ${action.parametres.duree}s`;
                break;
            case 'ActionTexte':
                icon = '📝';
                details = `Clic sur texte "${action.parametres.texte_recherche}"`;
                break;
        }

        return `
            <div class="action-item" data-index="${index}">
                <span class="action-icon">${icon}</span>
                <div class="action-info">
                    <div class="action-type">${action.type}</div>
                    <div class="action-details">${details}</div>
                </div>
                <div class="action-controls">
                    <button type="button" class="btn btn-icon btn-secondary" onclick="moveAction(${index}, -1)" ${index === 0 ? 'disabled' : ''}>↑</button>
                    <button type="button" class="btn btn-icon btn-secondary" onclick="moveAction(${index}, 1)" ${index === actions.length - 1 ? 'disabled' : ''}>↓</button>
                    <button type="button" class="btn btn-icon btn-secondary" onclick="removeAction(${index})">✕</button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Déplace une action
 */
function moveAction(index, direction) {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= actions.length) return;

    const temp = actions[index];
    actions[index] = actions[newIndex];
    actions[newIndex] = temp;

    // Mettre à jour les ordres
    actions.forEach((a, i) => a.ordre = i);

    renderActionsList();
}

/**
 * Supprime une action
 */
function removeAction(index) {
    actions.splice(index, 1);
    actions.forEach((a, i) => a.ordre = i);
    renderActionsList();
}

/**
 * Collecte les données du formulaire
 */
function collectFormData() {
    const nom = document.getElementById('nom-chemin').value.trim();
    const etatInitial = document.getElementById('etat-initial').value;
    const etatSortie = document.getElementById('etat-sortie').value;
    const description = document.getElementById('description-chemin').value.trim();

    // États de sortie possibles (checkboxes cochées)
    const etatsCheckboxes = document.querySelectorAll('input[name="etats_sortie_possibles"]:checked');
    const etatsSortiePossibles = Array.from(etatsCheckboxes).map(cb => cb.value);

    // Validation
    if (!etatInitial) {
        showNotification('Veuillez sélectionner l\'état initial', 'warning');
        return null;
    }

    if (!etatSortie) {
        showNotification('Veuillez sélectionner l\'état de sortie', 'warning');
        return null;
    }

    if (actions.length === 0) {
        showNotification('Veuillez ajouter au moins une action', 'warning');
        return null;
    }

    return {
        nom: nom || `${etatInitial}_vers_${etatSortie}`,
        etat_initial: etatInitial,
        etat_sortie: etatSortie,
        etats_sortie_possibles: etatsSortiePossibles,
        actions,
        description: description || null,
    };
}

/**
 * Prévisualise le code généré
 */
async function previewCode() {
    const data = collectFormData();
    if (!data) return;

    const result = await API.previewChemin(data);

    if (result.success) {
        document.getElementById('preview-filename').textContent = result.data.filename;
        document.getElementById('code-preview').innerHTML =
            `<code>${formatCode(result.data.code)}</code>`;
    } else {
        const errors = result.error?.messages || ['Erreur de prévisualisation'];
        showNotification(errors[0], 'error');
    }
}

/**
 * Valide le formulaire
 */
async function validateForm() {
    const data = collectFormData();
    if (!data) return;

    const result = await API.validateChemin(data);

    if (result.success) {
        showNotification('Données valides ✓', 'success');
    } else {
        const errors = result.error?.messages || ['Erreur de validation'];
        showResultModal('Erreurs de validation', `<ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>`, false);
    }
}

/**
 * Gère la soumission du formulaire
 */
async function handleSubmit(e) {
    e.preventDefault();

    const data = collectFormData();
    if (!data) return;

    const btn = document.getElementById('btn-generate');
    btn.disabled = true;
    btn.textContent = 'Génération...';

    const result = await API.createChemin(data);

    btn.disabled = false;
    btn.textContent = 'Générer le code';

    if (result.success) {
        showResultModal(
            '✓ Chemin créé avec succès',
            `<p><strong>Classe:</strong> ${result.data.nom_classe}</p>
             <p><strong>Fichier:</strong> ${result.data.fichier_genere}</p>
             <p><strong>Transition:</strong> ${result.data.etat_initial} → ${result.data.etat_sortie}</p>`,
            true
        );
    } else {
        const errors = result.error?.messages || [result.error?.message || 'Erreur'];
        showResultModal('Erreur', `<ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>`, false);
    }
}

// Initialiser la liste vide
document.addEventListener('DOMContentLoaded', renderActionsList);


// Global functions for onclick handlers
window.addCustomAction = addCustomAction;
