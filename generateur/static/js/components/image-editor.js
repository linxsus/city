/**
 * Éditeur d'image pour la sélection de régions
 */

class ImageEditor {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.options = {
            minWidth: 10,
            minHeight: 10,
            selectionColor: '#22c55e',
            suggestionColor: 'rgba(59, 130, 246, 0.5)',
            ...options,
        };

        this.image = null;
        this.selection = null;
        this.suggestions = [];
        this.isDragging = false;
        this.isResizing = false;
        this.isMoving = false;
        this.dragStart = null;
        this.resizeHandle = null;
        this.scale = 1;

        this.setupEventListeners();
    }

    /**
     * Charge une image dans l'éditeur
     */
    async loadImage(src) {
        return new Promise((resolve, reject) => {
            this.image = new Image();
            this.image.onload = () => {
                // Adapter la taille du canvas
                const maxWidth = this.canvas.parentElement.clientWidth - 20;
                this.scale = Math.min(1, maxWidth / this.image.width);

                this.canvas.width = this.image.width * this.scale;
                this.canvas.height = this.image.height * this.scale;

                this.render();
                resolve();
            };
            this.image.onerror = reject;
            this.image.src = src;
        });
    }

    /**
     * Définit la sélection courante
     */
    setSelection(region) {
        this.selection = region ? { ...region } : null;
        this.render();
        this.updateHiddenInputs();
    }

    /**
     * Récupère la sélection courante (en coordonnées réelles)
     */
    getSelection() {
        if (!this.selection) return null;

        return {
            x: Math.round(this.selection.x / this.scale),
            y: Math.round(this.selection.y / this.scale),
            width: Math.round(this.selection.width / this.scale),
            height: Math.round(this.selection.height / this.scale),
        };
    }

    /**
     * Affiche les suggestions de l'IA
     */
    showSuggestions(suggestions) {
        this.suggestions = suggestions.map(s => ({
            x: s.x * this.scale,
            y: s.y * this.scale,
            width: s.width * this.scale,
            height: s.height * this.scale,
            description: s.description,
        }));
        this.render();
    }

    /**
     * Réinitialise la sélection
     */
    reset() {
        this.selection = null;
        this.suggestions = [];
        this.render();
        this.updateHiddenInputs();
    }

    /**
     * Rendu du canvas
     */
    render() {
        if (!this.image) return;

        // Effacer le canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Dessiner l'image
        this.ctx.drawImage(
            this.image,
            0, 0,
            this.canvas.width,
            this.canvas.height
        );

        // Dessiner les suggestions (en bleu pointillé)
        this.suggestions.forEach((s, i) => {
            this.ctx.strokeStyle = this.options.suggestionColor;
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);
            this.ctx.strokeRect(s.x, s.y, s.width, s.height);

            // Numéro de la suggestion
            this.ctx.fillStyle = this.options.suggestionColor;
            this.ctx.font = '14px sans-serif';
            this.ctx.fillText(`${i + 1}`, s.x + 5, s.y + 18);
        });

        this.ctx.setLineDash([]);

        // Dessiner la sélection courante (en vert)
        if (this.selection) {
            const s = this.selection;

            // Overlay semi-transparent
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

            // Découper la zone sélectionnée
            this.ctx.clearRect(s.x, s.y, s.width, s.height);
            this.ctx.drawImage(
                this.image,
                s.x / this.scale, s.y / this.scale,
                s.width / this.scale, s.height / this.scale,
                s.x, s.y, s.width, s.height
            );

            // Bordure de sélection
            this.ctx.strokeStyle = this.options.selectionColor;
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(s.x, s.y, s.width, s.height);

            // Poignées de redimensionnement
            this.drawHandles();

            // Dimensions
            const realSel = this.getSelection();
            this.ctx.fillStyle = this.options.selectionColor;
            this.ctx.font = '12px monospace';
            this.ctx.fillText(
                `${realSel.width} x ${realSel.height}`,
                s.x + s.width + 5,
                s.y + s.height / 2
            );
        }
    }

    /**
     * Dessine les poignées de redimensionnement
     */
    drawHandles() {
        if (!this.selection) return;

        const s = this.selection;
        const handleSize = 8;
        const handles = this.getHandlePositions();

        this.ctx.fillStyle = this.options.selectionColor;

        handles.forEach(h => {
            this.ctx.fillRect(
                h.x - handleSize / 2,
                h.y - handleSize / 2,
                handleSize,
                handleSize
            );
        });
    }

    /**
     * Retourne les positions des poignées
     */
    getHandlePositions() {
        if (!this.selection) return [];

        const s = this.selection;
        return [
            { x: s.x, y: s.y, cursor: 'nw-resize', type: 'nw' },
            { x: s.x + s.width / 2, y: s.y, cursor: 'n-resize', type: 'n' },
            { x: s.x + s.width, y: s.y, cursor: 'ne-resize', type: 'ne' },
            { x: s.x + s.width, y: s.y + s.height / 2, cursor: 'e-resize', type: 'e' },
            { x: s.x + s.width, y: s.y + s.height, cursor: 'se-resize', type: 'se' },
            { x: s.x + s.width / 2, y: s.y + s.height, cursor: 's-resize', type: 's' },
            { x: s.x, y: s.y + s.height, cursor: 'sw-resize', type: 'sw' },
            { x: s.x, y: s.y + s.height / 2, cursor: 'w-resize', type: 'w' },
        ];
    }

    /**
     * Vérifie si un point est sur une poignée
     */
    getHandleAt(x, y) {
        const handles = this.getHandlePositions();
        const tolerance = 10;

        for (const h of handles) {
            if (Math.abs(x - h.x) <= tolerance && Math.abs(y - h.y) <= tolerance) {
                return h;
            }
        }
        return null;
    }

    /**
     * Vérifie si un point est dans la sélection
     */
    isInSelection(x, y) {
        if (!this.selection) return false;
        const s = this.selection;
        return x >= s.x && x <= s.x + s.width && y >= s.y && y <= s.y + s.height;
    }

    /**
     * Met à jour les inputs hidden avec la sélection
     */
    updateHiddenInputs() {
        const sel = this.getSelection();

        const xInput = document.getElementById('region-x');
        const yInput = document.getElementById('region-y');
        const wInput = document.getElementById('region-width');
        const hInput = document.getElementById('region-height');

        if (xInput) xInput.value = sel ? sel.x : '';
        if (yInput) yInput.value = sel ? sel.y : '';
        if (wInput) wInput.value = sel ? sel.width : '';
        if (hInput) hInput.value = sel ? sel.height : '';
    }

    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.onMouseUp.bind(this));
    }

    onMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Vérifier si on clique sur une poignée
        const handle = this.getHandleAt(x, y);
        if (handle) {
            this.isResizing = true;
            this.resizeHandle = handle;
            return;
        }

        // Vérifier si on clique dans la sélection (pour déplacer)
        if (this.isInSelection(x, y)) {
            this.isDragging = true;
            this.isMoving = true;
            this.dragStart = { x: x - this.selection.x, y: y - this.selection.y };
            return;
        }

        // Vérifier si on clique sur une suggestion
        for (const s of this.suggestions) {
            if (x >= s.x && x <= s.x + s.width && y >= s.y && y <= s.y + s.height) {
                this.setSelection(s);
                return;
            }
        }

        // Nouvelle sélection
        this.selection = { x, y, width: 0, height: 0 };
        this.isDragging = true;
        this.isMoving = false;
        this.dragStart = { x, y };
    }

    onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Mise à jour du curseur
        const handle = this.getHandleAt(x, y);
        if (handle) {
            this.canvas.style.cursor = handle.cursor;
        } else if (this.isInSelection(x, y)) {
            this.canvas.style.cursor = 'move';
        } else {
            this.canvas.style.cursor = 'crosshair';
        }

        if (this.isResizing && this.selection) {
            this.resizeSelection(x, y);
        } else if (this.isDragging && this.selection) {
            if (this.isMoving) {
                // Déplacement de la sélection existante
                this.selection.x = x - this.dragStart.x;
                this.selection.y = y - this.dragStart.y;
            } else {
                // Nouvelle sélection (dessiner un rectangle)
                this.selection.width = x - this.dragStart.x;
                this.selection.height = y - this.dragStart.y;
            }
            this.render();
        }
    }

    onMouseUp() {
        if (this.isDragging || this.isResizing) {
            // Normaliser la sélection (width/height positifs)
            if (this.selection) {
                if (this.selection.width < 0) {
                    this.selection.x += this.selection.width;
                    this.selection.width = Math.abs(this.selection.width);
                }
                if (this.selection.height < 0) {
                    this.selection.y += this.selection.height;
                    this.selection.height = Math.abs(this.selection.height);
                }

                // Vérifier la taille minimale
                if (this.selection.width < this.options.minWidth ||
                    this.selection.height < this.options.minHeight) {
                    this.selection = null;
                }
            }

            this.render();
            this.updateHiddenInputs();
        }

        this.isDragging = false;
        this.isResizing = false;
        this.isMoving = false;
        this.resizeHandle = null;
        this.dragStart = null;
    }

    resizeSelection(x, y) {
        if (!this.selection || !this.resizeHandle) return;

        const s = this.selection;
        const type = this.resizeHandle.type;

        switch (type) {
            case 'nw':
                s.width += s.x - x;
                s.height += s.y - y;
                s.x = x;
                s.y = y;
                break;
            case 'n':
                s.height += s.y - y;
                s.y = y;
                break;
            case 'ne':
                s.width = x - s.x;
                s.height += s.y - y;
                s.y = y;
                break;
            case 'e':
                s.width = x - s.x;
                break;
            case 'se':
                s.width = x - s.x;
                s.height = y - s.y;
                break;
            case 's':
                s.height = y - s.y;
                break;
            case 'sw':
                s.width += s.x - x;
                s.x = x;
                s.height = y - s.y;
                break;
            case 'w':
                s.width += s.x - x;
                s.x = x;
                break;
        }

        this.render();
    }
}

// Export global
window.ImageEditor = ImageEditor;
