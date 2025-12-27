/**
 * Blocs Blockly pour les actions
 */

// ActionBouton - Clic sur une image
Blockly.Blocks['action_bouton'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('🖱️ Cliquer sur image')
            .appendField(new Blockly.FieldTextInput('template.png'), 'TEMPLATE');
        this.appendDummyInput()
            .appendField('seuil')
            .appendField(new Blockly.FieldNumber(0.8, 0.5, 1.0, 0.05), 'THRESHOLD');
        this.appendDummyInput()
            .appendField('décalage X')
            .appendField(new Blockly.FieldNumber(0), 'OFFSET_X')
            .appendField('Y')
            .appendField(new Blockly.FieldNumber(0), 'OFFSET_Y');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip('Clique sur un élément identifié par une image template');
        this.setHelpUrl('');
    }
};

// ActionAttendre - Pause
Blockly.Blocks['action_attendre'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('⏱️ Attendre')
            .appendField(new Blockly.FieldNumber(1, 0.1, 300, 0.1), 'DUREE')
            .appendField('secondes');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip('Attend un certain temps avant de continuer');
        this.setHelpUrl('');
    }
};

// ActionTexte - Clic sur un texte OCR
Blockly.Blocks['action_texte'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📝 Cliquer sur texte')
            .appendField(new Blockly.FieldTextInput('Texte'), 'TEXTE');
        this.appendDummyInput()
            .appendField('décalage X')
            .appendField(new Blockly.FieldNumber(0), 'OFFSET_X')
            .appendField('Y')
            .appendField(new Blockly.FieldNumber(0), 'OFFSET_Y');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip('Clique sur un texte détecté par OCR');
        this.setHelpUrl('');
    }
};

// ActionClicPosition - Clic à une position fixe
Blockly.Blocks['action_clic_position'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📍 Cliquer à position')
            .appendField('X')
            .appendField(new Blockly.FieldNumber(0, 0), 'POS_X')
            .appendField('Y')
            .appendField(new Blockly.FieldNumber(0, 0), 'POS_Y');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip('Clique à une position fixe sur l\'écran');
        this.setHelpUrl('');
    }
};

// ActionLog - Logger un message
Blockly.Blocks['action_log'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📋 Logger')
            .appendField(new Blockly.FieldTextInput('Message'), 'MESSAGE');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(210);
        this.setTooltip('Enregistre un message dans les logs');
        this.setHelpUrl('');
    }
};

// Action personnalisée - Pour utiliser les actions customs
Blockly.Blocks['action_custom'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('⚡ Action:')
            .appendField(new Blockly.FieldTextInput('NomAction'), 'ACTION_NAME');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
        this.setTooltip('Utilise une action personnalisée');
        this.setHelpUrl('');
    }
};

// ActionLongue - Pour imbriquer une action longue existante
Blockly.Blocks['action_longue_ref'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('🔗 ActionLongue:')
            .appendField(new Blockly.FieldTextInput('NomActionLongue'), 'ACTION_LONGUE_NAME');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);
        this.setTooltip('Utilise une action longue existante');
        this.setHelpUrl('');
    }
};
