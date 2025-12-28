/**
 * Vue de capture d'écran via scrcpy/ADB
 * Version: 2.0.0 - Avec sélection de zone pour templates
 */

(function() {
    // Éléments DOM
    const preview = document.getElementById('capture-preview');
    const placeholder = document.getElementById('placeholder');
    const editorContainer = document.getElementById('image-editor-container');
    const editorToolbar = document.getElementById('editor-toolbar');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const deviceInfo = document.getElementById('device-info');
    const selectionInfo = document.getElementById('selection-info');

    // Boutons
    const btnCapture = document.getElementById('btn-capture');
    const btnRefreshStatus = document.getElementById('btn-refresh-status');
    const btnResetSelection = document.getElementById('btn-reset-selection');
    const btnNewCapture = document.getElementById('btn-new-capture');
    const btnSaveTemplate = document.getElementById('btn-save-template');
    const btnSaveTemplatePanel = document.getElementById('btn-save-template-panel');
    const btnUseForEtat = document.getElementById('btn-use-for-etat');
    const btnUseForChemin = document.getElementById('btn-use-for-chemin');

    // Champs template
    const templateName = document.getElementById('template-name');
    const templateSubdir = document.getElementById('template-subdir');

    // État
    let isConnected = false;
    let currentCapturePath = null;
    let imageEditor = null;

    /**
     * Initialisation
     */
    async function init() {
        // Initialiser l'éditeur d'image
        imageEditor = new ImageEditor('capture-canvas');

        // Écouter les changements de sélection
        imageEditor.onSelectionChange = updateSelectionState;

        // Vérifier le statut initial
        await checkStatus();

        // Événements
        btnRefreshStatus.addEventListener('click', checkStatus);
        btnCapture.addEventListener('click', captureScreen);
        btnNewCapture.addEventListener('click', captureScreen);
        btnResetSelection.addEventListener('click', resetSelection);
        btnSaveTemplate.addEventListener('click', saveTemplate);
        btnSaveTemplatePanel.addEventListener('click', saveTemplate);

        // Vérification périodique du statut
        setInterval(checkStatus, 10000);
    }

    /**
     * Vérifie le statut de connexion ADB
     */
    async function checkStatus() {
        try {
            const result = await API.getScrcpyStatus();

            if (result.success) {
                const data = result.data;
                isConnected = data.connected;

                updateStatusDisplay(data);
                updateButtons();
            } else {
                setDisconnected('Erreur ADB');
            }
        } catch (error) {
            console.error('Erreur vérification statut:', error);
            setDisconnected('Erreur connexion');
        }
    }

    /**
     * Met à jour l'affichage du statut
     */
    function updateStatusDisplay(data) {
        if (data.connected) {
            statusIndicator.className = 'status-indicator connected';
            statusText.textContent = 'Connecté';
            preview.classList.add('connected');

            let info = '';
            if (data.device_name) {
                info += `<strong>${data.device_name}</strong><br>`;
            }
            if (data.device_serial) {
                info += `Serial: ${data.device_serial}<br>`;
            }
            if (data.screen_size) {
                info += `Écran: ${data.screen_size[0]}x${data.screen_size[1]}`;
            }
            if (data.max_size) {
                info += ` (max ${data.max_size}px)`;
            }
            deviceInfo.innerHTML = info;
        } else {
            setDisconnected('Aucun appareil');
        }
    }

    /**
     * Affiche l'état déconnecté
     */
    function setDisconnected(message) {
        isConnected = false;
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = message;
        deviceInfo.innerHTML = '<small>Connectez un appareil Android via USB avec le débogage activé</small>';
        preview.classList.remove('connected');
        updateButtons();
    }

    /**
     * Met à jour l'état des boutons
     */
    function updateButtons() {
        const hasCapture = currentCapturePath !== null;
        const hasSelection = imageEditor && imageEditor.getSelection() !== null;

        btnCapture.disabled = !isConnected;

        // Boutons de sauvegarde template
        btnSaveTemplate.disabled = !hasSelection;
        btnSaveTemplatePanel.disabled = !hasSelection;

        // Liens vers les autres pages
        if (hasCapture) {
            btnUseForEtat.href = `/etat?image=${encodeURIComponent(currentCapturePath)}`;
            btnUseForChemin.href = `/chemin?image=${encodeURIComponent(currentCapturePath)}`;
            btnUseForEtat.classList.remove('disabled');
            btnUseForChemin.classList.remove('disabled');
        } else {
            btnUseForEtat.href = '#';
            btnUseForChemin.href = '#';
            btnUseForEtat.classList.add('disabled');
            btnUseForChemin.classList.add('disabled');
        }
    }

    /**
     * Met à jour l'état de la sélection
     */
    function updateSelectionState(selection) {
        if (selection) {
            selectionInfo.innerHTML = `
                <strong>Sélection:</strong> ${selection.width} x ${selection.height} px<br>
                <small>Position: (${selection.x}, ${selection.y})</small>
            `;
        } else {
            selectionInfo.textContent = 'Cliquez-glissez sur l\'image pour sélectionner une zone.';
        }
        updateButtons();
    }

    /**
     * Capture l'écran
     */
    async function captureScreen() {
        if (!isConnected) return;

        preview.classList.add('loading');
        btnCapture.disabled = true;
        btnCapture.textContent = '⏳ Capture en cours...';

        try {
            const result = await API.captureScreen();

            if (result.success) {
                const data = result.data;
                currentCapturePath = data.path;

                // Afficher l'éditeur
                placeholder.style.display = 'none';
                editorContainer.classList.add('active');
                editorToolbar.style.display = 'flex';
                preview.classList.add('has-image');

                // Charger l'image dans l'éditeur
                const imageUrl = `/api/images/serve?path=${encodeURIComponent(data.path)}`;
                await imageEditor.loadImage(imageUrl);

                selectionInfo.textContent = `Capture: ${data.width}x${data.height} - Cliquez-glissez pour sélectionner une zone.`;

                showNotification(`Capture réussie (${data.width}x${data.height})`, 'success');
            } else {
                showNotification(result.error?.message || 'Échec de la capture', 'error');
            }
        } catch (error) {
            console.error('Erreur capture:', error);
            showNotification('Erreur lors de la capture', 'error');
        } finally {
            preview.classList.remove('loading');
            btnCapture.disabled = false;
            btnCapture.textContent = '📷 Capturer l\'écran';
            updateButtons();
        }
    }

    /**
     * Réinitialise la sélection
     */
    function resetSelection() {
        if (imageEditor) {
            imageEditor.reset();
        }
        updateButtons();
    }

    /**
     * Sauvegarde comme template
     */
    async function saveTemplate() {
        const name = templateName.value.trim();
        const subdir = templateSubdir.value.trim() || 'scrcpy';

        if (!name) {
            showNotification('Veuillez entrer un nom de template', 'warning');
            templateName.focus();
            return;
        }

        if (!/^[a-z][a-z0-9_]*$/.test(name)) {
            showNotification('Nom invalide (utilisez snake_case: lettres minuscules, chiffres, underscores)', 'warning');
            templateName.focus();
            return;
        }

        const selection = imageEditor.getSelection();
        if (!selection) {
            showNotification('Veuillez sélectionner une zone sur l\'image', 'warning');
            return;
        }

        // Désactiver les boutons pendant la sauvegarde
        btnSaveTemplate.disabled = true;
        btnSaveTemplatePanel.disabled = true;

        try {
            const params = new URLSearchParams({
                image_path: currentCapturePath,
                x: selection.x,
                y: selection.y,
                width: selection.width,
                height: selection.height,
                output_name: name,
                output_subdir: subdir,
            });

            const result = await API.request(`/images/crop?${params}`, {
                method: 'POST',
            });

            if (result.success) {
                showNotification(`Template sauvegardé: ${result.data.relative_path}`, 'success');
                // Vider le champ nom pour le prochain template
                templateName.value = '';
            } else {
                showNotification(result.error?.message || 'Échec de la sauvegarde', 'error');
            }
        } catch (error) {
            console.error('Erreur sauvegarde template:', error);
            showNotification('Erreur lors de la sauvegarde', 'error');
        } finally {
            updateButtons();
        }
    }

    /**
     * Affiche une notification
     */
    function showNotification(message, type = 'info') {
        // Utiliser la fonction globale si disponible
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            console.log(`[${type}] ${message}`);
            // Fallback simple
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 12px 24px;
                background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
                color: white;
                border-radius: 6px;
                z-index: 1000;
                animation: fadeIn 0.3s ease;
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    }

    // Initialiser au chargement
    document.addEventListener('DOMContentLoaded', init);
})();
