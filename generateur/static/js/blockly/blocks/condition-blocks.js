/**
 * Blocs Blockly pour les conditions
 */

// Image présente
Blockly.Blocks['condition_image_presente'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('🖼️ image présente')
            .appendField(new Blockly.FieldTextInput('template.png'), 'TEMPLATE');
        this.appendDummyInput()
            .appendField('seuil')
            .appendField(new Blockly.FieldNumber(0.8, 0.5, 1.0, 0.05), 'THRESHOLD');
        this.setOutput(true, 'Boolean');
        this.setColour(330);
        this.setTooltip('Vrai si l\'image est présente à l\'écran');
        this.setHelpUrl('');
    }
};

// Image absente
Blockly.Blocks['condition_image_absente'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('🖼️ image absente')
            .appendField(new Blockly.FieldTextInput('template.png'), 'TEMPLATE');
        this.appendDummyInput()
            .appendField('seuil')
            .appendField(new Blockly.FieldNumber(0.8, 0.5, 1.0, 0.05), 'THRESHOLD');
        this.setOutput(true, 'Boolean');
        this.setColour(330);
        this.setTooltip('Vrai si l\'image n\'est PAS présente à l\'écran');
        this.setHelpUrl('');
    }
};

// Texte présent
Blockly.Blocks['condition_texte_present'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📝 texte présent')
            .appendField(new Blockly.FieldTextInput('texte'), 'TEXTE');
        this.setOutput(true, 'Boolean');
        this.setColour(330);
        this.setTooltip('Vrai si le texte est visible à l\'écran (OCR)');
        this.setHelpUrl('');
    }
};

// Texte absent
Blockly.Blocks['condition_texte_absent'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📝 texte absent')
            .appendField(new Blockly.FieldTextInput('texte'), 'TEXTE');
        this.setOutput(true, 'Boolean');
        this.setColour(330);
        this.setTooltip('Vrai si le texte n\'est PAS visible à l\'écran');
        this.setHelpUrl('');
    }
};

// Condition sur variable
Blockly.Blocks['condition_variable'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📊 variable')
            .appendField(new Blockly.FieldTextInput('compteur'), 'VARIABLE')
            .appendField(new Blockly.FieldDropdown([
                ['=', 'EGAL'],
                ['≠', 'DIFFERENT'],
                ['>', 'SUPERIEUR'],
                ['<', 'INFERIEUR'],
                ['≥', 'SUPERIEUR_EGAL'],
                ['≤', 'INFERIEUR_EGAL']
            ]), 'OPERATEUR')
            .appendField(new Blockly.FieldNumber(0), 'VALEUR');
        this.setOutput(true, 'Boolean');
        this.setColour(330);
        this.setTooltip('Compare une variable à une valeur');
        this.setHelpUrl('');
    }
};

// ET logique
Blockly.Blocks['logique_et'] = {
    init: function() {
        this.appendValueInput('A')
            .setCheck('Boolean');
        this.appendValueInput('B')
            .setCheck('Boolean')
            .appendField('ET');
        this.setInputsInline(true);
        this.setOutput(true, 'Boolean');
        this.setColour(230);
        this.setTooltip('Vrai si les deux conditions sont vraies');
        this.setHelpUrl('');
    }
};

// OU logique
Blockly.Blocks['logique_ou'] = {
    init: function() {
        this.appendValueInput('A')
            .setCheck('Boolean');
        this.appendValueInput('B')
            .setCheck('Boolean')
            .appendField('OU');
        this.setInputsInline(true);
        this.setOutput(true, 'Boolean');
        this.setColour(230);
        this.setTooltip('Vrai si au moins une des conditions est vraie');
        this.setHelpUrl('');
    }
};

// NON logique
Blockly.Blocks['logique_non'] = {
    init: function() {
        this.appendValueInput('CONDITION')
            .setCheck('Boolean')
            .appendField('NON');
        this.setOutput(true, 'Boolean');
        this.setColour(230);
        this.setTooltip('Inverse la condition (vrai devient faux et vice-versa)');
        this.setHelpUrl('');
    }
};
