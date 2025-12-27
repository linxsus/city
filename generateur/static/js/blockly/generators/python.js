/**
 * Générateur de code Python pour les blocs Blockly
 */

// Initialiser le générateur Python
const pythonGenerator = Blockly.Python || python.pythonGenerator;

// ============================================
// GÉNÉRATEURS POUR LES ACTIONS
// ============================================

pythonGenerator.forBlock['action_bouton'] = function(block) {
    const template = block.getFieldValue('TEMPLATE');
    const threshold = block.getFieldValue('THRESHOLD');
    const offsetX = block.getFieldValue('OFFSET_X');
    const offsetY = block.getFieldValue('OFFSET_Y');

    let code = `ActionBouton(manoir, "${template}", threshold=${threshold}`;
    if (offsetX !== 0 || offsetY !== 0) {
        code += `, offset=(${offsetX}, ${offsetY})`;
    }
    code += '),\n';

    return code;
};

pythonGenerator.forBlock['action_attendre'] = function(block) {
    const duree = block.getFieldValue('DUREE');
    return `ActionAttendre(manoir, ${duree}),\n`;
};

pythonGenerator.forBlock['action_texte'] = function(block) {
    const texte = block.getFieldValue('TEXTE');
    const offsetX = block.getFieldValue('OFFSET_X');
    const offsetY = block.getFieldValue('OFFSET_Y');

    let code = `ActionTexte(manoir, "${texte}"`;
    if (offsetX !== 0 || offsetY !== 0) {
        code += `, offset=(${offsetX}, ${offsetY})`;
    }
    code += '),\n';

    return code;
};

pythonGenerator.forBlock['action_clic_position'] = function(block) {
    const posX = block.getFieldValue('POS_X');
    const posY = block.getFieldValue('POS_Y');
    return `ActionSimple(manoir, lambda m: m.click_at(${posX}, ${posY})),\n`;
};

pythonGenerator.forBlock['action_log'] = function(block) {
    const message = block.getFieldValue('MESSAGE');
    return `ActionLog(manoir, "${message}"),\n`;
};

pythonGenerator.forBlock['action_custom'] = function(block) {
    const actionName = block.getFieldValue('ACTION_NAME');
    return `${actionName}(manoir),\n`;
};

pythonGenerator.forBlock['action_longue_ref'] = function(block) {
    const actionLongueName = block.getFieldValue('ACTION_LONGUE_NAME');
    return `${actionLongueName}(manoir),\n`;
};

// ============================================
// GÉNÉRATEURS POUR LES STRUCTURES DE CONTRÔLE
// ============================================

pythonGenerator.forBlock['controle_si'] = function(block) {
    const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'True';
    const actions = pythonGenerator.statementToCode(block, 'ACTIONS');

    // Formater les actions pour ActionIf
    const actionsList = formatActionsForList(actions);

    return `ActionIf(manoir, ${condition}, [\n${actionsList}]),\n`;
};

pythonGenerator.forBlock['controle_si_sinon'] = function(block) {
    const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'True';
    const actionsSi = pythonGenerator.statementToCode(block, 'ACTIONS_SI');
    const actionsSinon = pythonGenerator.statementToCode(block, 'ACTIONS_SINON');

    const actionsListSi = formatActionsForList(actionsSi);
    const actionsListSinon = formatActionsForList(actionsSinon);

    return `ActionIfElse(manoir, ${condition}, [\n${actionsListSi}], [\n${actionsListSinon}]),\n`;
};

pythonGenerator.forBlock['controle_repeter'] = function(block) {
    const fois = block.getFieldValue('FOIS');
    const actions = pythonGenerator.statementToCode(block, 'ACTIONS');

    const actionsList = formatActionsForList(actions);

    return `ActionFor(manoir, ${fois}, [\n${actionsList}]),\n`;
};

pythonGenerator.forBlock['controle_tant_que'] = function(block) {
    const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'True';
    const actions = pythonGenerator.statementToCode(block, 'ACTIONS');
    const maxIterations = block.getFieldValue('MAX_ITERATIONS');

    const actionsList = formatActionsForList(actions);

    return `ActionWhile(manoir, ${condition}, [\n${actionsList}], max_iterations=${maxIterations}),\n`;
};

pythonGenerator.forBlock['controle_pour_chaque'] = function(block) {
    const variable = block.getFieldValue('VARIABLE');
    const liste = block.getFieldValue('LISTE');
    const actions = pythonGenerator.statementToCode(block, 'ACTIONS');

    const actionsList = formatActionsForList(actions);

    return `ActionForEach(manoir, "${variable}", manoir.get_variable("${liste}", []), [\n${actionsList}]),\n`;
};

// ============================================
// GÉNÉRATEURS POUR LES CONDITIONS
// ============================================

pythonGenerator.forBlock['condition_image_presente'] = function(block) {
    const template = block.getFieldValue('TEMPLATE');
    const threshold = block.getFieldValue('THRESHOLD');
    return [`image_presente("${template}", threshold=${threshold})`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['condition_image_absente'] = function(block) {
    const template = block.getFieldValue('TEMPLATE');
    const threshold = block.getFieldValue('THRESHOLD');
    return [`image_absente("${template}", threshold=${threshold})`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['condition_texte_present'] = function(block) {
    const texte = block.getFieldValue('TEXTE');
    return [`texte_present("${texte}")`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['condition_texte_absent'] = function(block) {
    const texte = block.getFieldValue('TEXTE');
    return [`texte_absent("${texte}")`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['condition_variable'] = function(block) {
    const variable = block.getFieldValue('VARIABLE');
    const operateur = block.getFieldValue('OPERATEUR');
    const valeur = block.getFieldValue('VALEUR');

    const operateursPython = {
        'EGAL': 'variable_egale',
        'DIFFERENT': 'variable_differente',
        'SUPERIEUR': 'variable_superieure',
        'INFERIEUR': 'variable_inferieure',
        'SUPERIEUR_EGAL': 'variable_superieure_ou_egale',
        'INFERIEUR_EGAL': 'variable_inferieure_ou_egale'
    };

    const func = operateursPython[operateur] || 'variable_egale';
    return [`${func}("${variable}", ${valeur})`, pythonGenerator.ORDER_FUNCTION_CALL];
};

// ============================================
// GÉNÉRATEURS POUR LA LOGIQUE
// ============================================

pythonGenerator.forBlock['logique_et'] = function(block) {
    const a = pythonGenerator.valueToCode(block, 'A', pythonGenerator.ORDER_NONE) || 'True';
    const b = pythonGenerator.valueToCode(block, 'B', pythonGenerator.ORDER_NONE) || 'True';
    return [`et(${a}, ${b})`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['logique_ou'] = function(block) {
    const a = pythonGenerator.valueToCode(block, 'A', pythonGenerator.ORDER_NONE) || 'True';
    const b = pythonGenerator.valueToCode(block, 'B', pythonGenerator.ORDER_NONE) || 'True';
    return [`ou(${a}, ${b})`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['logique_non'] = function(block) {
    const condition = pythonGenerator.valueToCode(block, 'CONDITION', pythonGenerator.ORDER_NONE) || 'True';
    return [`non(${condition})`, pythonGenerator.ORDER_FUNCTION_CALL];
};

// ============================================
// GÉNÉRATEURS POUR LES VARIABLES
// ============================================

pythonGenerator.forBlock['variable_get'] = function(block) {
    const variable = block.getFieldValue('VARIABLE');
    return [`manoir.get_variable("${variable}")`, pythonGenerator.ORDER_FUNCTION_CALL];
};

pythonGenerator.forBlock['variable_set'] = function(block) {
    const variable = block.getFieldValue('VARIABLE');
    const valeur = pythonGenerator.valueToCode(block, 'VALEUR', pythonGenerator.ORDER_NONE) || '0';
    return `ActionSimple(manoir, lambda m: m.set_variable("${variable}", ${valeur})),\n`;
};

pythonGenerator.forBlock['variable_incrementer'] = function(block) {
    const variable = block.getFieldValue('VARIABLE');
    const increment = block.getFieldValue('INCREMENT');
    return `ActionSimple(manoir, lambda m: m.increment_variable("${variable}", ${increment})),\n`;
};

// ============================================
// GÉNÉRATEURS POUR LES VALEURS
// ============================================

pythonGenerator.forBlock['valeur_nombre'] = function(block) {
    const nombre = block.getFieldValue('NOMBRE');
    return [nombre.toString(), pythonGenerator.ORDER_ATOMIC];
};

pythonGenerator.forBlock['valeur_texte'] = function(block) {
    const texte = block.getFieldValue('TEXTE');
    return [`"${texte}"`, pythonGenerator.ORDER_ATOMIC];
};

pythonGenerator.forBlock['valeur_booleen'] = function(block) {
    const valeur = block.getFieldValue('VALEUR');
    return [valeur === 'TRUE' ? 'True' : 'False', pythonGenerator.ORDER_ATOMIC];
};

// ============================================
// FONCTIONS UTILITAIRES
// ============================================

/**
 * Formate les actions générées pour les mettre dans une liste Python
 */
function formatActionsForList(actionsCode) {
    if (!actionsCode) return '';

    // Indenter le code
    const lines = actionsCode.split('\n').filter(l => l.trim());
    return lines.map(line => '    ' + line).join('\n');
}

/**
 * Génère le code Python complet pour une ActionLongue
 */
function generateActionLongueCode(workspace, nom, etatRequis) {
    const code = pythonGenerator.workspaceToCode(workspace);

    // Formater les actions
    const actions = code.split('\n').filter(l => l.trim()).map(l => '            ' + l.trim()).join('\n');

    return `"""
ActionLongue générée automatiquement par le Générateur de Classes.
"""

from actions.longue.action_longue import ActionLongue
from actions.simple.action_bouton import ActionBouton
from actions.simple.action_attendre import ActionAttendre
from actions.simple.action_texte import ActionTexte
from actions.simple.action_simple import ActionSimple
from actions.control.action_if import ActionIf, ActionIfElse
from actions.control.action_for import ActionFor, ActionForEach
from actions.control.action_while import ActionWhile
from actions.item import (
    image_presente, image_absente,
    texte_present, texte_absent,
    variable_egale, variable_differente,
    variable_superieure, variable_inferieure,
    variable_superieure_ou_egale, variable_inferieure_ou_egale,
    et, ou, non
)


def creer_${nom.replace(/[^a-z0-9_]/gi, '_').toLowerCase()}(manoir):
    """Crée et retourne l'ActionLongue ${nom}."""
    return ActionLongue(
        manoir,
        [
${actions}
        ],
        nom="${nom}",
        etat_requis="${etatRequis || ''}",
    )
`;
}

// Export
window.generateActionLongueCode = generateActionLongueCode;
