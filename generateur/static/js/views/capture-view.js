/**
 * Vue de capture d'écran via scrcpy/ADB
 */

(function() {
    // Éléments DOM
    const preview = document.getElementById('capture-preview');
    const placeholder = document.getElementById('placeholder');
    const captureImage = document.getElementById('capture-image');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const deviceInfo = document.getElementById('device-info');
    const clickCoords = document.getElementById('click-coords');

    // Boutons
    const btnCapture = document.getElementById('btn-capture');
    const btnRefreshStatus = document.getElementById('btn-refresh-status');
    const btnLaunchScrcpy = document.getElementById('btn-launch-scrcpy');
    const btnBack = document.getElementById('btn-back');
    const btnHome = document.getElementById('btn-home');
    const btnRefresh = document.getElementById('btn-refresh');
    const btnSaveTemplate = document.getElementById('btn-save-template');
    const btnUseForEtat = document.getElementById('btn-use-for-etat');
    const btnUseForChemin = document.getElementById('btn-use-for-chemin');

    // Modal
    const templateModal = document.getElementById('template-modal');
    const templateName = document.getElementById('template-name');
    const templateSubdir = document.getElementById('template-subdir');
    const btnConfirmSave = document.getElementById('btn-confirm-save');

    // État
    let isConnected = false;
    let currentCapturePath = null;
    let captureWidth = 0;
    let captureHeight = 0;

    /**
     * Initialisation
     */
    async function init() {
        // Vérifier le statut initial
        await checkStatus();

        // Événements
        btnRefreshStatus.addEventListener('click', checkStatus);
        btnCapture.addEventListener('click', captureScreen);
        btnLaunchScrcpy.addEventListener('click', launchScrcpy);
        btnBack.addEventListener('click', pressBack);
        btnHome.addEventListener('click', pressHome);
        btnRefresh.addEventListener('click', captureScreen);
        btnSaveTemplate.addEventListener('click', openTemplateModal);
        btnConfirmSave.addEventListener('click', saveTemplate);

        // Clic sur l'image pour interagir
        captureImage.addEventListener('click', handleImageClick);

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

        btnCapture.disabled = !isConnected;
        btnLaunchScrcpy.disabled = !isConnected;
        btnBack.disabled = !isConnected;
        btnHome.disabled = !isConnected;
        btnRefresh.disabled = !isConnected;
        btnSaveTemplate.disabled = !hasCapture;

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
                captureWidth = data.width;
                captureHeight = data.height;

                // Afficher l'image
                captureImage.src = `/api/images/serve?path=${encodeURIComponent(data.path)}`;
                captureImage.style.display = 'block';
                placeholder.style.display = 'none';

                clickCoords.textContent = `Capture: ${data.width}x${data.height}`;

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
     * Lance scrcpy
     */
    async function launchScrcpy() {
        if (!isConnected) return;

        try {
            const result = await API.launchScrcpy();

            if (result.success) {
                showNotification(result.message, 'success');
            } else {
                showNotification(result.error?.message || 'Échec du lancement', 'error');
            }
        } catch (error) {
            console.error('Erreur lancement scrcpy:', error);
            showNotification('Erreur lors du lancement de scrcpy', 'error');
        }
    }

    /**
     * Appuie sur Retour
     */
    async function pressBack() {
        if (!isConnected) return;

        try {
            await API.scrcpyBack();
            // Rafraîchir la capture après un court délai
            setTimeout(captureScreen, 500);
        } catch (error) {
            console.error('Erreur bouton retour:', error);
        }
    }

    /**
     * Appuie sur Home
     */
    async function pressHome() {
        if (!isConnected) return;

        try {
            await API.scrcpyHome();
            setTimeout(captureScreen, 500);
        } catch (error) {
            console.error('Erreur bouton home:', error);
        }
    }

    /**
     * Gère le clic sur l'image pour envoyer un tap sur l'appareil
     */
    async function handleImageClick(event) {
        if (!isConnected || !currentCapturePath) return;

        // Calculer les coordonnées réelles sur l'appareil
        const rect = captureImage.getBoundingClientRect();
        const scaleX = captureWidth / rect.width;
        const scaleY = captureHeight / rect.height;

        const x = Math.round((event.clientX - rect.left) * scaleX);
        const y = Math.round((event.clientY - rect.top) * scaleY);

        clickCoords.textContent = `Clic envoyé: (${x}, ${y})`;

        try {
            const result = await API.scrcpyClick(x, y);

            if (result.success) {
                // Rafraîchir la capture après le clic
                setTimeout(captureScreen, 300);
            }
        } catch (error) {
            console.error('Erreur clic:', error);
        }
    }

    /**
     * Ouvre le modal de sauvegarde template
     */
    function openTemplateModal() {
        templateModal.classList.remove('hidden');
        templateName.value = '';
        templateName.focus();
    }

    /**
     * Ferme le modal de sauvegarde template
     */
    window.closeTemplateModal = function() {
        templateModal.classList.add('hidden');
    };

    /**
     * Sauvegarde comme template
     */
    async function saveTemplate() {
        const name = templateName.value.trim();
        const subdir = templateSubdir.value.trim() || 'scrcpy';

        if (!name) {
            showNotification('Veuillez entrer un nom de template', 'warning');
            return;
        }

        if (!/^[a-z][a-z0-9_]*$/.test(name)) {
            showNotification('Nom invalide (utilisez snake_case)', 'warning');
            return;
        }

        try {
            const result = await API.saveTemplate({
                template_name: name,
                subdir: subdir,
            });

            if (result.success) {
                showNotification(`Template sauvegardé: ${result.data.relative_path}`, 'success');
                closeTemplateModal();
            } else {
                showNotification(result.error?.message || 'Échec de la sauvegarde', 'error');
            }
        } catch (error) {
            console.error('Erreur sauvegarde template:', error);
            showNotification('Erreur lors de la sauvegarde', 'error');
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
                background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
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
