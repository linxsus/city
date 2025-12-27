/**
 * Vue de création d'ActionLongue avec Blockly
 */

let workspace = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeBlockly();
    initializeForm();
    loadAvailableStates();
});

/**
 * Initialise l'espace de travail Blockly
 */
function initializeBlockly() {
    const blocklyDiv = document.getElementById('blockly-div');

    // Options Blockly
    const options = {
        toolbox: BLOCKLY_TOOLBOX,
        grid: {
            spacing: 20,
            length: 3,
            colour: '#444',
            snap: true
        },
        zoom: {
            controls: true,
            wheel: true,
            startScale: 1.0,
            maxScale: 3,
            minScale: 0.3,
            scaleSpeed: 1.2
        },
        trashcan: true,
        move: {
            scrollbars: true,
            drag: true,
            wheel: true
        },
        theme: Blockly.Theme.defineTheme('darkTheme', {
            base: Blockly.Themes.Classic,
            componentStyles: {
                workspaceBackgroundColour: '#1e293b',
                toolboxBackgroundColour: '#0f172a',
                toolboxForegroundColour: '#f1f5f9',
                flyoutBackgroundColour: '#1e293b',
                flyoutForegroundColour: '#f1f5f9',
                flyoutOpacity: 0.9,
                scrollbarColour: '#475569',
                insertionMarkerColour: '#fff',
                insertionMarkerOpacity: 0.3,
            }
        }),
        renderer: 'zelos',
    };

    // Créer l'espace de travail
    workspace = Blockly.inject(blocklyDiv, options);

    // Redimensionner quand la fenêtre change
    window.addEventListener('resize', () => {
        Blockly.svgResize(workspace);
    });

    // Mettre à jour la prévisualisation quand les blocs changent
    workspace.addChangeListener((event) => {
        if (event.type === Blockly.Events.BLOCK_CHANGE ||
            event.type === Blockly.Events.BLOCK_CREATE ||
            event.type === Blockly.Events.BLOCK_DELETE ||
            event.type === Blockly.Events.BLOCK_MOVE) {
            // Délai pour éviter trop de mises à jour
            clearTimeout(window.previewTimeout);
            window.previewTimeout = setTimeout(updatePreview, 500);
        }
    });

    // Forcer le redimensionnement initial
    setTimeout(() => Blockly.svgResize(workspace), 100);
}

/**
 * Initialise les contrôles du formulaire
 */
function initializeForm() {
    // Bouton effacer
    document.getElementById('btn-clear').addEventListener('click', () => {
        if (confirm('Êtes-vous sûr de vouloir effacer tous les blocs ?')) {
            workspace.clear();
        }
    });

    // Bouton annuler
    document.getElementById('btn-undo').addEventListener('click', () => {
        workspace.undo(false);
    });

    // Bouton refaire
    document.getElementById('btn-redo').addEventListener('click', () => {
        workspace.undo(true);
    });

    // Bouton prévisualisation
    document.getElementById('btn-preview').addEventListener('click', updatePreview);

    // Bouton générer
    document.getElementById('btn-generate').addEventListener('click', generateAndSave);
}

/**
 * Charge les états disponibles
 */
async function loadAvailableStates() {
    const result = await API.getAvailableStates();

    if (result.success) {
        const select = document.getElementById('etat-requis');
        const states = result.data.states;

        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            select.appendChild(option);
        });
    }
}

/**
 * Met à jour la prévisualisation du code
 */
function updatePreview() {
    const nom = document.getElementById('nom').value || 'mon_action';
    const etatRequis = document.getElementById('etat-requis').value;

    try {
        const code = generateActionLongueCode(workspace, nom, etatRequis);
        document.getElementById('code-preview').innerHTML = `<code>${formatCode(code)}</code>`;
    } catch (error) {
        document.getElementById('code-preview').innerHTML = `<code>// Erreur: ${error.message}</code>`;
    }
}

/**
 * Génère et sauvegarde l'ActionLongue
 */
async function generateAndSave() {
    const nom = document.getElementById('nom').value.trim();
    const etatRequis = document.getElementById('etat-requis').value;
    const description = document.getElementById('description').value.trim();

    // Validation
    if (!nom) {
        showNotification('Veuillez entrer un nom pour l\'action', 'warning');
        return;
    }

    if (!nom.match(/^[a-z][a-z0-9_]*$/)) {
        showNotification('Le nom doit être en snake_case (lettres minuscules, chiffres, underscores)', 'warning');
        return;
    }

    // Vérifier qu'il y a des blocs
    const topBlocks = workspace.getTopBlocks(true);
    if (topBlocks.length === 0) {
        showNotification('Veuillez ajouter au moins une action', 'warning');
        return;
    }

    try {
        // Générer le code
        const code = generateActionLongueCode(workspace, nom, etatRequis);

        // Sauvegarder le workspace Blockly (pour pouvoir le recharger plus tard)
        const workspaceXml = Blockly.Xml.workspaceToDom(workspace);
        const workspaceText = Blockly.Xml.domToText(workspaceXml);

        // Envoyer au serveur
        const result = await API.request('/actions/longue/create', {
            method: 'POST',
            body: {
                nom,
                etat_requis: etatRequis || null,
                description: description || null,
                code_genere: code,
                blockly_workspace: workspaceText,
            }
        });

        if (result.success) {
            showResultModal(
                '✓ ActionLongue créée avec succès',
                `<p><strong>Nom:</strong> ${nom}</p>
                 <p><strong>Fichier:</strong> ${result.data.fichier_genere}</p>
                 <h4>Code généré:</h4>
                 <pre><code>${formatCode(code)}</code></pre>`,
                true
            );
        } else {
            const errors = result.error?.messages || [result.error?.message || 'Erreur'];
            showResultModal('Erreur', `<ul>${errors.map(e => `<li>${e}</li>`).join('')}</ul>`, false);
        }

    } catch (error) {
        showResultModal('Erreur', `<p>${error.message}</p>`, false);
    }
}

/**
 * Sauvegarde le workspace actuel en localStorage
 */
function saveWorkspaceToLocal() {
    const xml = Blockly.Xml.workspaceToDom(workspace);
    const xmlText = Blockly.Xml.domToText(xml);
    localStorage.setItem('blockly_workspace_backup', xmlText);
}

/**
 * Restaure le workspace depuis localStorage
 */
function loadWorkspaceFromLocal() {
    const xmlText = localStorage.getItem('blockly_workspace_backup');
    if (xmlText) {
        try {
            const xml = Blockly.utils.xml.textToDom(xmlText);
            Blockly.Xml.domToWorkspace(xml, workspace);
        } catch (error) {
            console.error('Erreur lors du chargement du workspace:', error);
        }
    }
}

// Sauvegarder automatiquement toutes les 30 secondes
setInterval(saveWorkspaceToLocal, 30000);

// Sauvegarder avant de quitter la page
window.addEventListener('beforeunload', saveWorkspaceToLocal);
