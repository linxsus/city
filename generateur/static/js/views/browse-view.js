/**
 * Vue de navigation des éléments existants
 */

// State
let currentData = {
    etats: [],
    chemins: [],
    templates: [],
    groupes: [],
};
let currentTab = 'etats';
let currentFilter = '';
let searchQuery = '';
let showOrphans = false;
let showMissing = false;

// DOM Elements
const elements = {
    countEtats: document.getElementById('count-etats'),
    countChemins: document.getElementById('count-chemins'),
    countTemplates: document.getElementById('count-templates'),
    countGroupes: document.getElementById('count-groupes'),
    gridEtats: document.getElementById('grid-etats'),
    gridChemins: document.getElementById('grid-chemins'),
    gridTemplates: document.getElementById('grid-templates'),
    listGroupes: document.getElementById('list-groupes'),
    searchInput: document.getElementById('search-input'),
    filterGroup: document.getElementById('filter-group'),
    btnRefresh: document.getElementById('btn-refresh'),
    btnOrphans: document.getElementById('btn-orphans'),
    btnMissing: document.getElementById('btn-missing'),
    detailModal: document.getElementById('detail-modal'),
    detailTitle: document.getElementById('detail-title'),
    detailBody: document.getElementById('detail-body'),
    codeModal: document.getElementById('code-modal'),
    codeTitle: document.getElementById('code-title'),
    codeContent: document.getElementById('code-content'),
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSearch();
    initToolbar();
    loadData();
});

function initTabs() {
    // Summary cards clickable
    document.querySelectorAll('.summary-card').forEach(card => {
        card.addEventListener('click', () => {
            const tab = card.dataset.tab;
            switchTab(tab);
        });
    });

    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tab}`);
    });

    // Render current tab
    renderCurrentTab();
}

function initSearch() {
    elements.searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase();
        renderCurrentTab();
    });

    elements.filterGroup.addEventListener('change', (e) => {
        currentFilter = e.target.value;
        renderCurrentTab();
    });

    elements.btnRefresh.addEventListener('click', () => {
        loadData();
    });
}

function initToolbar() {
    elements.btnOrphans.addEventListener('click', () => {
        showOrphans = !showOrphans;
        showMissing = false;
        elements.btnOrphans.classList.toggle('active', showOrphans);
        elements.btnMissing.classList.remove('active');
        if (showOrphans) {
            loadOrphanTemplates();
        } else {
            renderTemplates();
        }
    });

    elements.btnMissing.addEventListener('click', () => {
        showMissing = !showMissing;
        showOrphans = false;
        elements.btnMissing.classList.toggle('active', showMissing);
        elements.btnOrphans.classList.remove('active');
        if (showMissing) {
            loadMissingTemplates();
        } else {
            renderTemplates();
        }
    });
}

async function loadData() {
    try {
        const response = await API.request('/import/summary');

        if (response.success) {
            currentData.etats = response.data.etats.items || [];
            currentData.chemins = response.data.chemins.items || [];
            currentData.templates = response.data.templates.items || [];
            currentData.groupes = response.data.groupes || [];

            updateCounts();
            updateGroupFilter();
            renderCurrentTab();
        } else {
            showError('Erreur lors du chargement des données');
        }
    } catch (error) {
        console.error('Load error:', error);
        showError('Erreur de connexion au serveur');
    }
}

async function loadOrphanTemplates() {
    try {
        const response = await API.request('/import/templates/orphans');
        if (response.success) {
            renderTemplates(response.data.orphans, true);
        }
    } catch (error) {
        console.error('Error loading orphans:', error);
    }
}

async function loadMissingTemplates() {
    try {
        const response = await API.request('/import/templates/missing');
        if (response.success) {
            renderMissingTemplates(response.data.missing);
        }
    } catch (error) {
        console.error('Error loading missing:', error);
    }
}

function updateCounts() {
    elements.countEtats.textContent = currentData.etats.length;
    elements.countChemins.textContent = currentData.chemins.length;
    elements.countTemplates.textContent = currentData.templates.length;
    elements.countGroupes.textContent = currentData.groupes.length;
}

function updateGroupFilter() {
    const select = elements.filterGroup;
    select.innerHTML = '<option value="">Tous les groupes</option>';

    currentData.groupes.forEach(groupe => {
        const option = document.createElement('option');
        option.value = groupe;
        option.textContent = groupe;
        select.appendChild(option);
    });
}

function renderCurrentTab() {
    switch (currentTab) {
        case 'etats':
            renderEtats();
            break;
        case 'chemins':
            renderChemins();
            break;
        case 'templates':
            if (!showOrphans && !showMissing) {
                renderTemplates();
            }
            break;
        case 'groupes':
            renderGroupes();
            break;
    }
}

function renderEtats() {
    const filtered = filterItems(currentData.etats, 'etat');

    if (filtered.length === 0) {
        elements.gridEtats.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <p>Aucun état trouvé</p>
            </div>
        `;
        return;
    }

    elements.gridEtats.innerHTML = filtered.map(etat => `
        <div class="element-card" onclick="showEtatDetail('${escapeHtml(etat.nom)}')">
            <div class="element-header">
                <span class="element-name">${escapeHtml(etat.nom)}</span>
                <span class="element-type type-etat ${etat.priorite >= 80 ? 'type-popup' : ''}">
                    ${etat.priorite >= 80 ? 'Popup' : 'État'}
                </span>
            </div>
            <div class="element-meta">
                ${etat.groupes.map(g => `<span class="meta-badge">${escapeHtml(g)}</span>`).join('')}
                ${etat.priorite !== 0 ? `<span class="meta-badge priority-high">P:${etat.priorite}</span>` : ''}
            </div>
            <div class="element-details">
                <p>Vérification: ${etat.methode_verif}</p>
                <p>Templates: ${etat.templates.length} | Textes: ${etat.textes.length}</p>
            </div>
        </div>
    `).join('');
}

function renderChemins() {
    const filtered = filterItems(currentData.chemins, 'chemin');

    if (filtered.length === 0) {
        elements.gridChemins.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔀</div>
                <p>Aucun chemin trouvé</p>
            </div>
        `;
        return;
    }

    elements.gridChemins.innerHTML = filtered.map(chemin => `
        <div class="element-card" onclick="showCheminDetail('${escapeHtml(chemin.nom)}')">
            <div class="element-header">
                <span class="element-name">${escapeHtml(chemin.nom)}</span>
                <span class="element-type type-chemin">Chemin</span>
            </div>
            <div class="element-details">
                <p>${escapeHtml(chemin.etat_initial)} → ${escapeHtml(chemin.etat_sortie)}</p>
                <p>Templates: ${chemin.templates.length}</p>
            </div>
        </div>
    `).join('');
}

function renderTemplates(templatesList = null, isOrphans = false) {
    const templates = templatesList || currentData.templates;
    const filtered = templates.filter(t => {
        if (!searchQuery) return true;
        return t.name.toLowerCase().includes(searchQuery) ||
               t.path.toLowerCase().includes(searchQuery);
    });

    if (filtered.length === 0) {
        elements.gridTemplates.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🖼️</div>
                <p>${isOrphans ? 'Aucun template orphelin' : 'Aucun template trouvé'}</p>
            </div>
        `;
        return;
    }

    elements.gridTemplates.innerHTML = filtered.map(template => `
        <div class="template-card ${isOrphans ? 'orphan' : ''}" onclick="showTemplateDetail('${escapeHtml(template.path)}')">
            <div class="template-preview">
                <img src="/api/images/templates/${encodeURIComponent(template.path)}"
                     alt="${escapeHtml(template.name)}"
                     onerror="this.parentElement.innerHTML='<span class=\\'placeholder\\'>🖼️</span>'">
            </div>
            <div class="template-info">
                <div class="template-name">${escapeHtml(template.name)}</div>
                <div class="template-path">${escapeHtml(template.path)}</div>
            </div>
        </div>
    `).join('');
}

function renderMissingTemplates(missing) {
    if (missing.length === 0) {
        elements.gridTemplates.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <p>Aucun template manquant</p>
            </div>
        `;
        return;
    }

    elements.gridTemplates.innerHTML = missing.map(item => `
        <div class="template-card" style="border-color: #ef4444;">
            <div class="template-preview">
                <span class="placeholder" style="color: #ef4444;">❌</span>
            </div>
            <div class="template-info">
                <div class="template-name" style="color: #ef4444;">${escapeHtml(item.template)}</div>
                <div class="template-path">Utilisé dans: ${escapeHtml(item.used_in)} (${item.type})</div>
            </div>
        </div>
    `).join('');
}

function renderGroupes() {
    if (currentData.groupes.length === 0) {
        elements.listGroupes.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🏷️</div>
                <p>Aucun groupe trouvé</p>
            </div>
        `;
        return;
    }

    // Count etats per group
    const groupCounts = {};
    currentData.groupes.forEach(g => groupCounts[g] = 0);
    currentData.etats.forEach(etat => {
        etat.groupes.forEach(g => {
            if (groupCounts[g] !== undefined) {
                groupCounts[g]++;
            }
        });
    });

    const filtered = currentData.groupes.filter(g =>
        !searchQuery || g.toLowerCase().includes(searchQuery)
    );

    elements.listGroupes.innerHTML = filtered.map(groupe => `
        <div class="groupe-item" onclick="filterByGroup('${escapeHtml(groupe)}')">
            <span class="groupe-name">${escapeHtml(groupe)}</span>
            <span class="groupe-count">${groupCounts[groupe]} états</span>
        </div>
    `).join('');
}

function filterItems(items, type) {
    return items.filter(item => {
        // Search filter
        if (searchQuery) {
            const searchable = item.nom.toLowerCase();
            if (!searchable.includes(searchQuery)) return false;
        }

        // Group filter (only for etats)
        if (currentFilter && type === 'etat') {
            if (!item.groupes.includes(currentFilter)) return false;
        }

        return true;
    });
}

function filterByGroup(groupe) {
    elements.filterGroup.value = groupe;
    currentFilter = groupe;
    switchTab('etats');
}

// Detail views
async function showEtatDetail(nom) {
    const etat = currentData.etats.find(e => e.nom === nom);
    if (!etat) return;

    elements.detailTitle.textContent = `État: ${etat.nom}`;
    elements.detailBody.innerHTML = `
        <div class="detail-section">
            <h4>Informations générales</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Nom</div>
                    <div class="detail-value">${escapeHtml(etat.nom)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Classe</div>
                    <div class="detail-value">${escapeHtml(etat.nom_classe)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Priorité</div>
                    <div class="detail-value">${etat.priorite}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Méthode</div>
                    <div class="detail-value">${etat.methode_verif}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>Groupes</h4>
            <div class="detail-tags">
                ${etat.groupes.map(g => `<span class="detail-tag">${escapeHtml(g)}</span>`).join('') || '<em>Aucun groupe</em>'}
            </div>
        </div>

        <div class="detail-section">
            <h4>Templates utilisés</h4>
            <div class="detail-tags">
                ${etat.templates.map(t => `<span class="detail-tag">${escapeHtml(t)}</span>`).join('') || '<em>Aucun template</em>'}
            </div>
        </div>

        <div class="detail-section">
            <h4>Textes OCR</h4>
            <div class="detail-tags">
                ${etat.textes.map(t => `<span class="detail-tag">${escapeHtml(t)}</span>`).join('') || '<em>Aucun texte</em>'}
            </div>
        </div>

        <div class="detail-section">
            <h4>Fichier source</h4>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">${escapeHtml(etat.fichier)}</p>
        </div>

        <div class="detail-section">
            <h4>Code source</h4>
            <div class="detail-code">
                <pre><code>${escapeHtml(etat.code_source)}</code></pre>
            </div>
        </div>
    `;

    document.getElementById('btn-edit-element').textContent = '📋 Dupliquer';
    document.getElementById('btn-edit-element').onclick = () => {
        // Store complete data in sessionStorage (URL has size limits)
        const duplicateData = {
            nom: etat.nom + '_copie',
            groupes: etat.groupes,
            priorite: etat.priorite,
            methode_verif: etat.methode_verif,
            templates: etat.templates,
            textes: etat.textes,
            source: etat.nom,
        };
        sessionStorage.setItem('duplicate_etat', JSON.stringify(duplicateData));
        window.location.href = '/etat?duplicate=' + encodeURIComponent(etat.nom);
    };

    // Delete button
    const deleteBtn = document.getElementById('btn-delete-element');
    deleteBtn.style.display = '';
    deleteBtn.onclick = () => deleteEtat(etat.nom);

    elements.detailModal.classList.remove('hidden');
}

async function showCheminDetail(nom) {
    const chemin = currentData.chemins.find(c => c.nom === nom);
    if (!chemin) return;

    elements.detailTitle.textContent = `Chemin: ${chemin.nom}`;
    elements.detailBody.innerHTML = `
        <div class="detail-section">
            <h4>Informations générales</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Nom</div>
                    <div class="detail-value">${escapeHtml(chemin.nom)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Classe</div>
                    <div class="detail-value">${escapeHtml(chemin.nom_classe)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">État initial</div>
                    <div class="detail-value">${escapeHtml(chemin.etat_initial)}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">État de sortie</div>
                    <div class="detail-value">${escapeHtml(chemin.etat_sortie)}</div>
                </div>
            </div>
        </div>

        <div class="detail-section">
            <h4>Templates utilisés</h4>
            <div class="detail-tags">
                ${chemin.templates.map(t => `<span class="detail-tag">${escapeHtml(t)}</span>`).join('') || '<em>Aucun template</em>'}
            </div>
        </div>

        <div class="detail-section">
            <h4>Fichier source</h4>
            <p style="color: var(--text-secondary); font-size: 0.875rem;">${escapeHtml(chemin.fichier)}</p>
        </div>

        <div class="detail-section">
            <h4>Code source</h4>
            <div class="detail-code">
                <pre><code>${escapeHtml(chemin.code_source)}</code></pre>
            </div>
        </div>
    `;

    document.getElementById('btn-edit-element').textContent = '📋 Dupliquer';
    document.getElementById('btn-edit-element').onclick = () => {
        // Store complete data in sessionStorage
        const duplicateData = {
            nom: chemin.nom + '_copie',
            etat_initial: chemin.etat_initial,
            etat_sortie: chemin.etat_sortie,
            templates: chemin.templates,
            code_source: chemin.code_source,
            source: chemin.nom,
        };
        sessionStorage.setItem('duplicate_chemin', JSON.stringify(duplicateData));
        window.location.href = '/chemin?duplicate=' + encodeURIComponent(chemin.nom);
    };

    // Delete button
    const deleteBtn = document.getElementById('btn-delete-element');
    deleteBtn.style.display = '';
    deleteBtn.onclick = () => deleteChemin(chemin.nom);

    elements.detailModal.classList.remove('hidden');
}

async function showTemplateDetail(path) {
    try {
        const response = await API.request(`/import/templates/usage?path=${encodeURIComponent(path)}`);

        elements.detailTitle.textContent = `Template: ${path}`;
        elements.detailBody.innerHTML = `
            <div class="detail-section" style="text-align: center;">
                <img src="/api/images/templates/${encodeURIComponent(path)}"
                     style="max-width: 100%; max-height: 300px; border-radius: 8px;"
                     alt="${escapeHtml(path)}">
            </div>

            <div class="detail-section">
                <h4>Chemin</h4>
                <p style="color: var(--text-secondary);">${escapeHtml(path)}</p>
            </div>

            ${response.success ? `
            <div class="detail-section">
                <h4>Utilisé dans les états</h4>
                <div class="detail-tags">
                    ${response.data.etats.map(e => `<span class="detail-tag">${escapeHtml(e)}</span>`).join('') || '<em>Aucun état</em>'}
                </div>
            </div>

            <div class="detail-section">
                <h4>Utilisé dans les chemins</h4>
                <div class="detail-tags">
                    ${response.data.chemins.map(c => `<span class="detail-tag">${escapeHtml(c)}</span>`).join('') || '<em>Aucun chemin</em>'}
                </div>
            </div>
            ` : ''}
        `;

        document.getElementById('btn-edit-element').style.display = 'none';

        // Delete button for template
        const deleteBtn = document.getElementById('btn-delete-element');
        deleteBtn.style.display = '';
        deleteBtn.onclick = () => deleteTemplate(path);

        elements.detailModal.classList.remove('hidden');
    } catch (error) {
        console.error('Error showing template detail:', error);
    }
}

function closeDetailModal() {
    elements.detailModal.classList.add('hidden');
    document.getElementById('btn-edit-element').style.display = '';
    document.getElementById('btn-delete-element').style.display = '';
}

function closeCodeModal() {
    elements.codeModal.classList.add('hidden');
}

function showError(message) {
    // Simple error display
    alert(message);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Delete functions
async function deleteEtat(nom) {
    if (!confirm(`Supprimer l'état "${nom}" ?\n\nLe fichier sera déplacé vers la corbeille.`)) {
        return;
    }

    const result = await API.deleteEtat(nom);

    if (result.success) {
        showNotification(`État "${nom}" déplacé vers la corbeille`, 'success');
        closeDetailModal();
        loadData(); // Refresh
    } else {
        showError(result.error?.message || 'Erreur lors de la suppression');
    }
}

async function deleteChemin(nom) {
    if (!confirm(`Supprimer le chemin "${nom}" ?\n\nLe fichier sera déplacé vers la corbeille.`)) {
        return;
    }

    const result = await API.deleteChemin(nom);

    if (result.success) {
        showNotification(`Chemin "${nom}" déplacé vers la corbeille`, 'success');
        closeDetailModal();
        loadData(); // Refresh
    } else {
        showError(result.error?.message || 'Erreur lors de la suppression');
    }
}

async function deleteTemplate(path) {
    if (!confirm(`Supprimer le template "${path}" ?\n\nLe fichier sera déplacé vers la corbeille.`)) {
        return;
    }

    const result = await API.deleteTemplate(path);

    if (result.success) {
        showNotification(`Template "${path}" déplacé vers la corbeille`, 'success');
        closeDetailModal();
        loadData(); // Refresh
    } else {
        showError(result.error?.message || 'Erreur lors de la suppression');
    }
}

function showNotification(message, type = 'info') {
    // Use global showNotification if available, otherwise create simple one
    if (window.showNotification && typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        alert(message);
    }
}

// Global functions for onclick handlers
window.showEtatDetail = showEtatDetail;
window.showCheminDetail = showCheminDetail;
window.showTemplateDetail = showTemplateDetail;
window.closeDetailModal = closeDetailModal;
window.closeCodeModal = closeCodeModal;
window.filterByGroup = filterByGroup;
