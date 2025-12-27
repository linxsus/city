/**
 * Vue de création d'état
 * Version: 1.2.0
 */
console.log('=== etat-view.js v1.2.0 chargé ===');

// Fonctions utilitaires (définies localement si non disponibles)
if (typeof showNotification === 'undefined') {
    window.showNotification = function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    };
}

if (typeof showResultModal === 'undefined') {
    window.showResultModal = function(title, content, isSuccess = true) {
        const modal = document.getElementById('result-modal');
        const titleEl = document.getElementById('result-title');
        const bodyEl = document.getElementById('result-body');
        if (modal && titleEl && bodyEl) {
            titleEl.textContent = title;
            titleEl.style.color = isSuccess ? 'var(--color-success)' : 'var(--color-error)';
            bodyEl.innerHTML = content;
            modal.classList.remove('hidden');
        }
    };
}

if (typeof closeModal === 'undefined') {
    window.closeModal = function() {
        const modal = document.getElementById('result-modal');
        if (modal) modal.classList.add('hidden');
    };
}

if (typeof formatCode === 'undefined') {
    window.formatCode = function(code) {
        return code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    };
}

let imageEditor = null;
let currentImagePath = null;
let selectedGroups = [];

document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    loadExistingGroups();
});

/**
 * Initialise le formulaire
 */
function initializeForm() {
    // Initialiser l'éditeur d'image
    imageEditor = new ImageEditor('image-canvas');

    // Upload zone
    const uploadZone = document.getElementById('upload-zone');
    const imageInput = document.getElementById('image-input');

    uploadZone.addEventListener('click', (e) => {
        // Éviter le double clic si on clique sur le bouton
        if (e.target.tagName !== 'BUTTON') {
            imageInput.click();
        }
    });
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleImageUpload(file);
    });
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleImageUpload(file);
    });

    // Méthode de vérification
    const methodeVerif = document.getElementById('methode-verif');
    methodeVerif.addEventListener('change', updateVerificationMethod);

    // Threshold slider
    const threshold = document.getElementById('threshold');
    const thresholdValue = document.getElementById('threshold-value');
    threshold.addEventListener('input', () => {
        thresholdValue.textContent = parseFloat(threshold.value).toFixed(2);
    });

    // Tags input pour les groupes
    initializeTagsInput();

    // Boutons
    document.getElementById('btn-reset-selection')?.addEventListener('click', () => {
        imageEditor.reset();
    });

    document.getElementById('btn-suggest-ia')?.addEventListener('click', requestIASuggestions);
    document.getElementById('btn-preview')?.addEventListener('click', previewCode);
    document.getElementById('btn-validate')?.addEventListener('click', validateForm);

    // Formulaire
    document.getElementById('etat-form').addEventListener('submit', handleSubmit);
}

/**
 * Gère l'upload d'image
 */
async function handleImageUpload(file) {
    const result = await API.uploadImage(file);

    if (result.success) {
        currentImagePath = result.data.path;
        document.getElementById('image-source').value = currentImagePath;

        // Afficher l'éditeur
        document.getElementById('upload-zone').classList.add('hidden');
        document.getElementById('image-preview-container').classList.remove('hidden');

        // Charger l'image dans l'éditeur
        await imageEditor.loadImage(`/api/images/serve?path=${encodeURIComponent(currentImagePath)}`);

        showNotification('Image chargée avec succès', 'success');
    } else {
        showNotification(result.error?.message || 'Erreur lors du chargement', 'error');
    }
}

/**
 * Met à jour l'affichage selon la méthode de vérification
 */
function updateVerificationMethod() {
    const methode = document.getElementById('methode-verif').value;
    const texteGroup = document.getElementById('texte-ocr-group');

    if (methode === 'texte' || methode === 'combinaison') {
        texteGroup.style.display = 'block';
    } else {
        texteGroup.style.display = 'none';
    }
}

/**
 * Charge les groupes existants
 */
async function loadExistingGroups() {
    const result = await API.getGroups();

    if (result.success) {
        const suggestions = document.getElementById('groupes-suggestions');
        const groups = result.data.groups;

        if (groups.length > 0) {
            suggestions.innerHTML = groups.map(g =>
                `<button type="button" class="btn-link" onclick="addGroup('${g}')">${g}</button>`
            ).join(', ');
        } else {
            suggestions.textContent = 'Aucun groupe existant';
        }
    }
}

/**
 * Initialise le système de tags pour les groupes
 */
function initializeTagsInput() {
    const container = document.getElementById('groupes-container');
    const input = document.getElementById('groupes-input');
    const hidden = document.getElementById('groupes');

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const value = input.value.trim();
            if (value && !selectedGroups.includes(value)) {
                addGroup(value);
            }
            input.value = '';
        }
    });

    // Mettre à jour le hidden field
    function updateHidden() {
        hidden.value = JSON.stringify(selectedGroups);
    }

    window.addGroup = function(group) {
        if (!selectedGroups.includes(group)) {
            selectedGroups.push(group);

            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.innerHTML = `${group} <button type="button" onclick="removeGroup('${group}', this)">&times;</button>`;
            container.insertBefore(tag, input);

            updateHidden();
        }
    };

    window.removeGroup = function(group, button) {
        selectedGroups = selectedGroups.filter(g => g !== group);
        button.parentElement.remove();
        updateHidden();
    };
}

/**
 * Demande des suggestions à l'IA
 */
async function requestIASuggestions() {
    if (!currentImagePath) {
        showNotification('Veuillez d\'abord charger une image', 'warning');
        return;
    }

    const btn = document.getElementById('btn-suggest-ia');
    btn.disabled = true;
    btn.textContent = '🔄 Analyse en cours...';

    const result = await API.analyzeImage(currentImagePath);

    btn.disabled = false;
    btn.textContent = '🤖 Suggestions IA';

    if (result.success) {
        const data = result.data;

        // Afficher les suggestions de régions
        if (data.regions && data.regions.length > 0) {
            imageEditor.showSuggestions(data.regions);
            showNotification(`${data.regions.length} région(s) suggérée(s)`, 'success');
        }

        // Appliquer les suggestions
        if (data.groupe_suggere) {
            addGroup(data.groupe_suggere);
        }

        if (data.priorite_suggeree !== undefined) {
            document.getElementById('priorite').value = data.priorite_suggeree;
        }

        if (data.explication) {
            console.log('Explication IA:', data.explication);
        }
    } else {
        showNotification(result.error?.message || 'Erreur IA', 'error');
    }
}

/**
 * Prévisualise le code généré
 */
async function previewCode() {
    const data = collectFormData();

    if (!data) return;

    const result = await API.previewEtat(data);

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

    const result = await API.validateEtat(data);

    if (result.success) {
        showNotification('Données valides ✓', 'success');
    } else {
        const errors = result.error?.messages || ['Erreur de validation'];
        showResultModal('Erreurs de validation', `<ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>`, false);
    }
}

/**
 * Collecte les données du formulaire
 */
function collectFormData() {
    const nom = document.getElementById('nom').value.trim();
    const methodeVerif = document.getElementById('methode-verif').value;
    const texteOcr = document.getElementById('texte-ocr').value.trim();
    const priorite = parseInt(document.getElementById('priorite').value) || 0;
    const threshold = parseFloat(document.getElementById('threshold').value) || 0.8;
    const description = document.getElementById('description').value.trim();

    const selection = imageEditor.getSelection();

    // Validation de base
    if (!nom) {
        showNotification('Veuillez entrer un nom pour l\'état', 'warning');
        return null;
    }

    if (!currentImagePath) {
        showNotification('Veuillez charger une image', 'warning');
        return null;
    }

    if ((methodeVerif === 'image' || methodeVerif === 'combinaison') && !selection) {
        showNotification('Veuillez sélectionner une région de l\'image', 'warning');
        return null;
    }

    if ((methodeVerif === 'texte' || methodeVerif === 'combinaison') && !texteOcr) {
        showNotification('Veuillez entrer le texte à détecter', 'warning');
        return null;
    }

    return {
        nom,
        groupes: selectedGroups,
        priorite,
        methode_verif: methodeVerif,
        template_region: selection,
        texte_ocr: texteOcr || null,
        threshold,
        image_source: currentImagePath,
        description: description || null,
    };
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

    const result = await API.createEtat(data);

    btn.disabled = false;
    btn.textContent = 'Générer le code';

    if (result.success) {
        showResultModal(
            '✓ État créé avec succès',
            `<p><strong>Classe:</strong> ${result.data.nom_classe}</p>
             <p><strong>Fichier:</strong> ${result.data.fichier_genere}</p>
             ${result.data.template_path ? `<p><strong>Template:</strong> ${result.data.template_path}</p>` : ''}`,
            true
        );
    } else {
        const errors = result.error?.messages || [result.error?.message || 'Erreur'];
        showResultModal('Erreur', `<ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>`, false);
    }
}
