/**
 * Configuration de la toolbox Blockly pour ActionLongue
 */

const BLOCKLY_TOOLBOX = {
    kind: 'categoryToolbox',
    contents: [
        {
            kind: 'category',
            name: 'Actions de base',
            colour: '#5b80a5',
            contents: [
                { kind: 'block', type: 'action_bouton' },
                { kind: 'block', type: 'action_attendre' },
                { kind: 'block', type: 'action_texte' },
                { kind: 'block', type: 'action_clic_position' },
                { kind: 'block', type: 'action_log' },
            ]
        },
        {
            kind: 'category',
            name: 'Actions personnalisées',
            colour: '#a55b80',
            contents: [
                { kind: 'block', type: 'action_custom' },
                { kind: 'block', type: 'action_longue_ref' },
            ]
        },
        {
            kind: 'category',
            name: 'Contrôle',
            colour: '#5ba55b',
            contents: [
                { kind: 'block', type: 'controle_si' },
                { kind: 'block', type: 'controle_si_sinon' },
                { kind: 'block', type: 'controle_repeter' },
                { kind: 'block', type: 'controle_tant_que' },
                { kind: 'block', type: 'controle_pour_chaque' },
            ]
        },
        {
            kind: 'category',
            name: 'Conditions',
            colour: '#a55b80',
            contents: [
                { kind: 'block', type: 'condition_image_presente' },
                { kind: 'block', type: 'condition_image_absente' },
                { kind: 'block', type: 'condition_texte_present' },
                { kind: 'block', type: 'condition_texte_absent' },
                { kind: 'block', type: 'condition_variable' },
            ]
        },
        {
            kind: 'category',
            name: 'Logique',
            colour: '#5b67a5',
            contents: [
                { kind: 'block', type: 'logique_et' },
                { kind: 'block', type: 'logique_ou' },
                { kind: 'block', type: 'logique_non' },
            ]
        },
        {
            kind: 'category',
            name: 'Variables',
            colour: '#a5745b',
            contents: [
                { kind: 'block', type: 'variable_get' },
                { kind: 'block', type: 'variable_set' },
                { kind: 'block', type: 'variable_incrementer' },
            ]
        },
        {
            kind: 'category',
            name: 'Valeurs',
            colour: '#7d5ba5',
            contents: [
                { kind: 'block', type: 'valeur_nombre' },
                { kind: 'block', type: 'valeur_texte' },
                { kind: 'block', type: 'valeur_booleen' },
            ]
        },
    ]
};

// Export
window.BLOCKLY_TOOLBOX = BLOCKLY_TOOLBOX;
