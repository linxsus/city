/**
 * Application principale - Générateur de Classes
 */

// Fonctions utilitaires globales

/**
 * Affiche une notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Ferme le modal de résultat
 */
function closeModal() {
    const modal = document.getElementById('result-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Affiche le modal de résultat
 */
function showResultModal(title, content, isSuccess = true) {
    const modal = document.getElementById('result-modal');
    const titleEl = document.getElementById('result-title');
    const bodyEl = document.getElementById('result-body');

    if (modal && titleEl && bodyEl) {
        titleEl.textContent = title;
        titleEl.style.color = isSuccess ? 'var(--color-success)' : 'var(--color-error)';
        bodyEl.innerHTML = content;
        modal.classList.remove('hidden');
    }
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

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    console.log('Générateur de Classes - Application chargée');
});
