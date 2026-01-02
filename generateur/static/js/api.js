/**
 * Client API pour le Générateur de Classes
 */

const API = {
    baseUrl: '/api',

    /**
     * Effectue une requête API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return {
                success: false,
                error: {
                    code: 'NETWORK_ERROR',
                    message: error.message,
                },
            };
        }
    },

    /**
     * Upload une image
     */
    async uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.baseUrl}/images/upload`, {
                method: 'POST',
                body: formData,
            });
            return await response.json();
        } catch (error) {
            console.error('Upload Error:', error);
            return {
                success: false,
                error: {
                    code: 'UPLOAD_ERROR',
                    message: error.message,
                },
            };
        }
    },

    // === États ===

    async getGroups() {
        return this.request('/etats/groups');
    },

    async getExistingStates() {
        return this.request('/etats/existing');
    },

    async validateEtat(data) {
        return this.request('/etats/validate', {
            method: 'POST',
            body: data,
        });
    },

    async previewEtat(data) {
        return this.request('/etats/preview', {
            method: 'POST',
            body: data,
        });
    },

    async createEtat(data) {
        return this.request('/etats/create', {
            method: 'POST',
            body: data,
        });
    },

    // === Chemins ===

    async getAvailableStates() {
        return this.request('/chemins/states');
    },

    async suggestExitStates(etatSortie) {
        return this.request(`/chemins/suggest-exits?etat_sortie=${encodeURIComponent(etatSortie)}`, {
            method: 'POST',
        });
    },

    async validateChemin(data) {
        return this.request('/chemins/validate', {
            method: 'POST',
            body: data,
        });
    },

    async previewChemin(data) {
        return this.request('/chemins/preview', {
            method: 'POST',
            body: data,
        });
    },

    async createChemin(data) {
        return this.request('/chemins/create', {
            method: 'POST',
            body: data,
        });
    },

    // === IA ===

    async getIAStatus() {
        return this.request('/ia/status');
    },

    async analyzeImage(imagePath, contexte = null) {
        const params = new URLSearchParams({ image_path: imagePath });
        if (contexte) {
            params.append('contexte', contexte);
        }
        return this.request(`/ia/analyze?${params}`, {
            method: 'POST',
        });
    },

    async detectButtons(imagePath) {
        return this.request(`/ia/detect-buttons?image_path=${encodeURIComponent(imagePath)}`, {
            method: 'POST',
        });
    },

    // === Images/Templates ===

    async getTemplatesList() {
        return this.request('/images/templates-list');
    },

    // === Delete (move to trash) ===

    async deleteEtat(nom) {
        return this.request(`/import/etats/${encodeURIComponent(nom)}`, {
            method: 'DELETE',
        });
    },

    async deleteChemin(nom) {
        return this.request(`/import/chemins/${encodeURIComponent(nom)}`, {
            method: 'DELETE',
        });
    },

    async deleteTemplate(path) {
        return this.request(`/import/templates?path=${encodeURIComponent(path)}`, {
            method: 'DELETE',
        });
    },

    // === Scrcpy/ADB ===

    async getScrcpyStatus() {
        return this.request('/scrcpy/status');
    },

    async captureScreen() {
        return this.request('/scrcpy/capture', {
            method: 'POST',
        });
    },

    async capturePreview() {
        return this.request('/scrcpy/capture-preview');
    },

    async saveTemplate(data) {
        return this.request('/scrcpy/save-template', {
            method: 'POST',
            body: data,
        });
    },

    async scrcpyClick(x, y) {
        return this.request('/scrcpy/click', {
            method: 'POST',
            body: { x, y },
        });
    },

    async scrcpyBack() {
        return this.request('/scrcpy/back', {
            method: 'POST',
        });
    },

    async scrcpyHome() {
        return this.request('/scrcpy/home', {
            method: 'POST',
        });
    },

    async launchScrcpy() {
        return this.request('/scrcpy/launch-scrcpy', {
            method: 'POST',
        });
    },

    async getScrcpyWindowStatus() {
        return this.request('/scrcpy/scrcpy-status');
    },

    // === Erreurs ===

    async getAllErreurs() {
        return this.request('/erreurs/');
    },

    async getErreursCategories() {
        return this.request('/erreurs/categories');
    },

    async getErreursByCategory(categorie) {
        return this.request(`/erreurs/by-category/${encodeURIComponent(categorie)}`);
    },

    async getErreursVerifApresDefaults() {
        return this.request('/erreurs/defaults/verif-apres');
    },

    async getErreursSiEchecDefaults() {
        return this.request('/erreurs/defaults/si-echec');
    },

    async getErreurByNom(nom) {
        return this.request(`/erreurs/${encodeURIComponent(nom)}`);
    },

    async refreshErreurs() {
        return this.request('/erreurs/refresh', {
            method: 'POST',
        });
    },

    async previewErreur(data) {
        return this.request('/erreurs/preview', {
            method: 'POST',
            body: data,
        });
    },

    async createErreur(data) {
        return this.request('/erreurs/create', {
            method: 'POST',
            body: data,
        });
    },

    async suggestErreurs(actionDescription) {
        return this.request('/erreurs/suggest', {
            method: 'POST',
            body: { action_description: actionDescription },
        });
    },
};
