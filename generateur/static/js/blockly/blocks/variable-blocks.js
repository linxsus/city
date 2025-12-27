/**
 * Blocs Blockly pour les variables et valeurs
 */

// Obtenir une variable
Blockly.Blocks['variable_get'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📦 obtenir')
            .appendField(new Blockly.FieldTextInput('ma_variable'), 'VARIABLE');
        this.setOutput(true, null);
        this.setColour(45);
        this.setTooltip('Récupère la valeur d\'une variable du manoir');
        this.setHelpUrl('');
    }
};

// Définir une variable
Blockly.Blocks['variable_set'] = {
    init: function() {
        this.appendValueInput('VALEUR')
            .appendField('📦 définir')
            .appendField(new Blockly.FieldTextInput('ma_variable'), 'VARIABLE')
            .appendField('à');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(45);
        this.setTooltip('Définit la valeur d\'une variable du manoir');
        this.setHelpUrl('');
    }
};

// Incrémenter une variable
Blockly.Blocks['variable_incrementer'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📦 incrémenter')
            .appendField(new Blockly.FieldTextInput('compteur'), 'VARIABLE')
            .appendField('de')
            .appendField(new Blockly.FieldNumber(1), 'INCREMENT');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(45);
        this.setTooltip('Ajoute une valeur à une variable numérique');
        this.setHelpUrl('');
    }
};

// Valeur nombre
Blockly.Blocks['valeur_nombre'] = {
    init: function() {
        this.appendDummyInput()
            .appendField(new Blockly.FieldNumber(0), 'NOMBRE');
        this.setOutput(true, 'Number');
        this.setColour(270);
        this.setTooltip('Un nombre');
        this.setHelpUrl('');
    }
};

// Valeur texte
Blockly.Blocks['valeur_texte'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('"')
            .appendField(new Blockly.FieldTextInput('texte'), 'TEXTE')
            .appendField('"');
        this.setOutput(true, 'String');
        this.setColour(270);
        this.setTooltip('Une chaîne de texte');
        this.setHelpUrl('');
    }
};

// Valeur booléen
Blockly.Blocks['valeur_booleen'] = {
    init: function() {
        this.appendDummyInput()
            .appendField(new Blockly.FieldDropdown([
                ['vrai', 'TRUE'],
                ['faux', 'FALSE']
            ]), 'VALEUR');
        this.setOutput(true, 'Boolean');
        this.setColour(270);
        this.setTooltip('Vrai ou Faux');
        this.setHelpUrl('');
    }
};
