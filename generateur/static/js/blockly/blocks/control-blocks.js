/**
 * Blocs Blockly pour les structures de contrôle
 */

// Si (if)
Blockly.Blocks['controle_si'] = {
    init: function() {
        this.appendValueInput('CONDITION')
            .setCheck('Boolean')
            .appendField('🔀 Si');
        this.appendStatementInput('ACTIONS')
            .appendField('faire');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(120);
        this.setTooltip('Exécute les actions si la condition est vraie');
        this.setHelpUrl('');
    }
};

// Si-Sinon (if-else)
Blockly.Blocks['controle_si_sinon'] = {
    init: function() {
        this.appendValueInput('CONDITION')
            .setCheck('Boolean')
            .appendField('🔀 Si');
        this.appendStatementInput('ACTIONS_SI')
            .appendField('faire');
        this.appendStatementInput('ACTIONS_SINON')
            .appendField('sinon');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(120);
        this.setTooltip('Exécute les actions si la condition est vraie, sinon exécute les autres');
        this.setHelpUrl('');
    }
};

// Répéter N fois (for)
Blockly.Blocks['controle_repeter'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('🔁 Répéter')
            .appendField(new Blockly.FieldNumber(10, 1, 1000, 1), 'FOIS')
            .appendField('fois');
        this.appendStatementInput('ACTIONS')
            .appendField('faire');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(120);
        this.setTooltip('Répète les actions un certain nombre de fois');
        this.setHelpUrl('');
    }
};

// Tant que (while)
Blockly.Blocks['controle_tant_que'] = {
    init: function() {
        this.appendValueInput('CONDITION')
            .setCheck('Boolean')
            .appendField('🔄 Tant que');
        this.appendStatementInput('ACTIONS')
            .appendField('faire');
        this.appendDummyInput()
            .appendField('max itérations')
            .appendField(new Blockly.FieldNumber(100, 1, 10000, 1), 'MAX_ITERATIONS');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(120);
        this.setTooltip('Répète les actions tant que la condition est vraie (avec limite de sécurité)');
        this.setHelpUrl('');
    }
};

// Pour chaque (itération sur liste)
Blockly.Blocks['controle_pour_chaque'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📋 Pour')
            .appendField(new Blockly.FieldTextInput('element'), 'VARIABLE')
            .appendField('dans')
            .appendField(new Blockly.FieldTextInput('liste'), 'LISTE');
        this.appendStatementInput('ACTIONS')
            .appendField('faire');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(120);
        this.setTooltip('Exécute les actions pour chaque élément d\'une liste');
        this.setHelpUrl('');
    }
};
