"""Schémas Pydantic pour le générateur de classes."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MethodeVerification(str, Enum):
    """Méthode de vérification pour un état."""
    IMAGE = "image"
    TEXTE = "texte"
    COMBINAISON = "combinaison"


class RegionSchema(BaseModel):
    """Région rectangulaire dans une image."""
    x: int = Field(..., ge=0, description="Position X du coin supérieur gauche")
    y: int = Field(..., ge=0, description="Position Y du coin supérieur gauche")
    width: int = Field(..., gt=0, description="Largeur de la région")
    height: int = Field(..., gt=0, description="Hauteur de la région")


class EtatCreate(BaseModel):
    """Données pour créer un nouvel état."""
    nom: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Nom unique de l'état (snake_case)"
    )
    groupes: list[str] = Field(
        default_factory=list,
        description="Groupes auxquels appartient l'état"
    )
    priorite: int = Field(
        default=0,
        ge=-100,
        le=100,
        description="Priorité de l'état (-100 à 100, popups=80+)"
    )
    methode_verif: MethodeVerification = Field(
        default=MethodeVerification.IMAGE,
        description="Méthode de vérification"
    )
    template_region: RegionSchema | None = Field(
        default=None,
        description="Région du template pour détection image"
    )
    texte_ocr: str | None = Field(
        default=None,
        description="Texte à détecter par OCR"
    )
    texte_region: RegionSchema | None = Field(
        default=None,
        description="Région pour la détection OCR"
    )
    threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Seuil de confiance pour la détection"
    )
    image_source: str = Field(
        ...,
        description="Chemin de l'image source uploadée"
    )
    description: str | None = Field(
        default=None,
        description="Description optionnelle de l'état"
    )


class EtatSchema(EtatCreate):
    """État complet avec métadonnées."""
    nom_classe: str = Field(
        ...,
        description="Nom de la classe Python (ex: EtatVille)"
    )
    template_path: str | None = Field(
        default=None,
        description="Chemin du template généré"
    )
    fichier_genere: str | None = Field(
        default=None,
        description="Chemin du fichier Python généré"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création"
    )


class ActionReference(BaseModel):
    """Référence à une action dans un chemin."""
    type: Literal["ActionBouton", "ActionAttendre", "ActionTexte", "ActionLongue"] = Field(
        ...,
        description="Type d'action"
    )
    parametres: dict[str, Any] = Field(
        default_factory=dict,
        description="Paramètres de l'action"
    )
    ordre: int = Field(
        default=0,
        description="Ordre d'exécution dans la séquence"
    )


class CheminCreate(BaseModel):
    """Données pour créer un nouveau chemin."""
    nom: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nom du chemin"
    )
    etat_initial: str = Field(
        ...,
        description="Nom de l'état de départ"
    )
    etat_sortie: str = Field(
        ...,
        description="Nom de l'état d'arrivée principal"
    )
    etats_sortie_possibles: list[str] = Field(
        default_factory=list,
        description="États de sortie alternatifs (popups, erreurs)"
    )
    actions: list[ActionReference] = Field(
        default_factory=list,
        description="Séquence d'actions du chemin"
    )
    description: str | None = Field(
        default=None,
        description="Description optionnelle"
    )


class CheminSchema(CheminCreate):
    """Chemin complet avec métadonnées."""
    nom_classe: str = Field(
        ...,
        description="Nom de la classe Python"
    )
    fichier_genere: str | None = Field(
        default=None,
        description="Chemin du fichier Python généré"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création"
    )


class ActionBoutonSchema(BaseModel):
    """Schéma pour ActionBouton."""
    type: Literal["ActionBouton"] = "ActionBouton"
    template_path: str = Field(..., description="Chemin du template")
    template_region: RegionSchema | None = Field(
        default=None,
        description="Région du template dans l'image source"
    )
    offset_x: int = Field(default=0, description="Décalage X du clic")
    offset_y: int = Field(default=0, description="Décalage Y du clic")
    threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Seuil de détection"
    )
    delai_avant: float = Field(
        default=0.0,
        ge=0.0,
        description="Délai avant l'action"
    )
    delai_apres: float = Field(
        default=0.1,
        ge=0.0,
        description="Délai après l'action"
    )


class ActionAttendreSchema(BaseModel):
    """Schéma pour ActionAttendre."""
    type: Literal["ActionAttendre"] = "ActionAttendre"
    duree: float = Field(
        ...,
        gt=0,
        le=300,
        description="Durée d'attente en secondes"
    )


class ActionTexteSchema(BaseModel):
    """Schéma pour ActionTexte."""
    type: Literal["ActionTexte"] = "ActionTexte"
    texte_recherche: str = Field(..., description="Texte à cliquer")
    region: RegionSchema | None = Field(
        default=None,
        description="Région de recherche"
    )
    offset_x: int = Field(default=0, description="Décalage X")
    offset_y: int = Field(default=0, description="Décalage Y")


class ActionCreate(BaseModel):
    """Données pour créer une nouvelle Action simple."""
    nom: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Nom unique de l'action (snake_case)"
    )
    description: str | None = Field(
        default=None,
        description="Description de l'action"
    )
    condition_code: str | None = Field(
        default=None,
        description="Code Python pour la condition (optionnel)"
    )
    run_code: str = Field(
        ...,
        description="Code Python pour _run()"
    )
    parametres: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Paramètres du constructeur [{name, type, default}]"
    )
    erreurs_verif_apres: list[str] = Field(
        default_factory=list,
        description="Erreurs à vérifier après succès"
    )
    erreurs_si_echec: list[str] = Field(
        default_factory=list,
        description="Erreurs à vérifier si échec"
    )
    retry_si_erreur_non_identifiee: bool = Field(
        default=False,
        description="Réessayer si l'action échoue sans erreur identifiée"
    )


class ActionSchema(ActionCreate):
    """Action complète avec métadonnées."""
    nom_classe: str = Field(
        ...,
        description="Nom de la classe Python (ex: ActionMonAction)"
    )
    fichier_genere: str | None = Field(
        default=None,
        description="Chemin du fichier Python généré"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création"
    )


class ControlBlock(BaseModel):
    """Bloc de contrôle pour ActionLongue (if, while, for)."""
    type: Literal["if", "if_else", "while", "for", "action"] = Field(
        ...,
        description="Type de bloc"
    )
    condition: str | None = Field(
        default=None,
        description="Condition pour if/while"
    )
    iterations: int | None = Field(
        default=None,
        description="Nombre d'itérations pour for"
    )
    actions: list["ControlBlock | ActionReference"] = Field(
        default_factory=list,
        description="Actions dans le bloc"
    )
    actions_else: list["ControlBlock | ActionReference"] = Field(
        default_factory=list,
        description="Actions pour le else (if_else uniquement)"
    )
    max_iterations: int = Field(
        default=100,
        description="Limite de sécurité pour while"
    )


class ActionLongueCreate(BaseModel):
    """Données pour créer une ActionLongue."""
    nom: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Nom unique de l'action longue (snake_case)"
    )
    description: str | None = Field(
        default=None,
        description="Description de l'action"
    )
    blocks: list[ControlBlock | ActionReference] = Field(
        default_factory=list,
        description="Blocs de contrôle et actions"
    )
    etat_requis: str | None = Field(
        default=None,
        description="État requis avant exécution"
    )
    maintenant: bool = Field(
        default=False,
        description="Insérer immédiatement dans la séquence"
    )


class ActionLongueSchema(ActionLongueCreate):
    """ActionLongue complète avec métadonnées."""
    nom_classe: str = Field(
        ...,
        description="Nom de la classe Python"
    )
    fichier_genere: str | None = Field(
        default=None,
        description="Chemin du fichier Python généré"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création"
    )


class SuggestionIA(BaseModel):
    """Suggestion de l'IA Claude."""
    regions: list[dict] = Field(
        default_factory=list,
        description="Régions suggérées avec descriptions"
    )
    textes: list[str] = Field(
        default_factory=list,
        description="Textes détectés"
    )
    groupe_suggere: str | None = Field(
        default=None,
        description="Groupe suggéré"
    )
    priorite_suggeree: int = Field(
        default=0,
        description="Priorité suggérée"
    )
    explication: str | None = Field(
        default=None,
        description="Explication de l'IA"
    )


class TypeErreur(str, Enum):
    """Type de détection d'erreur."""
    IMAGE = "image"
    TEXTE = "texte"
    COULEUR = "couleur"


class ErreurSchema(BaseModel):
    """Schéma pour une erreur détectable."""
    nom: str = Field(..., description="Identifiant unique de l'erreur")
    type: TypeErreur = Field(..., description="Type de détection")
    image: str | None = Field(default=None, description="Chemin de l'image template")
    texte: str | None = Field(default=None, description="Texte à détecter (OCR)")
    message: str = Field(..., description="Message descriptif de l'erreur")
    retry_action_originale: bool = Field(
        default=False,
        description="Réessayer l'action originale après correction"
    )
    exclure_fenetre: int = Field(
        default=0,
        ge=0,
        description="Durée d'exclusion de la fenêtre en secondes"
    )
    priorite: int = Field(
        default=0,
        description="Priorité de l'erreur (plus haut = vérifié en premier)"
    )
    categorie: str | None = Field(
        default=None,
        description="Catégorie de l'erreur (connexion, jeu, popup, système)"
    )


class ErreurCreate(BaseModel):
    """Données pour créer une nouvelle erreur."""
    nom: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Nom unique de l'erreur (snake_case)"
    )
    type: TypeErreur = Field(..., description="Type de détection")
    image: str | None = Field(
        default=None,
        description="Chemin de l'image template (pour type image)"
    )
    texte: str | None = Field(
        default=None,
        description="Texte à détecter (pour type texte)"
    )
    message: str = Field(..., description="Message descriptif")
    action_correction: str | None = Field(
        default=None,
        description="Type d'action de correction (clic_ok, fermer, etc.)"
    )
    retry_action_originale: bool = Field(
        default=False,
        description="Réessayer l'action après correction"
    )
    exclure_fenetre: int = Field(
        default=0,
        ge=0,
        description="Durée d'exclusion en secondes"
    )
    priorite: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Priorité de l'erreur"
    )
    categorie: str = Field(
        default="autre",
        description="Catégorie de l'erreur"
    )


class EtatUpdate(BaseModel):
    """Données pour mettre à jour un état existant."""
    groupes: list[str] | None = Field(
        default=None,
        description="Nouveaux groupes (optionnel)"
    )
    priorite: int | None = Field(
        default=None,
        ge=-100,
        le=100,
        description="Nouvelle priorité (optionnel)"
    )


class CheminUpdate(BaseModel):
    """Données pour mettre à jour un chemin existant."""
    etat_initial: str | None = Field(
        default=None,
        description="Nouvel état initial (optionnel)"
    )
    etat_sortie: str | None = Field(
        default=None,
        description="Nouvel état de sortie (optionnel)"
    )


class APIResponse(BaseModel):
    """Réponse standard de l'API."""
    success: bool = Field(..., description="Succès de l'opération")
    data: Any | None = Field(default=None, description="Données retournées")
    error: dict | None = Field(default=None, description="Détails de l'erreur")
    message: str | None = Field(default=None, description="Message informatif")


# =====================================================
# SCHEMAS POUR LE SYSTÈME DE TEMPLATES
# =====================================================


class GroupConfigSchema(BaseModel):
    """Configuration d'un groupe pour un template."""
    variants: list[str] = Field(
        ...,
        min_length=1,
        description="Liste des fichiers de variantes"
    )
    threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Seuil de confiance pour la détection"
    )


class TemplateConfigCreate(BaseModel):
    """Données pour créer un nouveau template."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Nom unique du template (snake_case)"
    )
    description: str = Field(
        default="",
        description="Description du template"
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Catégorie du template (boutons, popups, etc.)"
    )
    group_configs: dict[str, GroupConfigSchema] = Field(
        ...,
        min_length=1,
        description="Configuration par groupe (bluestack, scrcpy, etc.)"
    )


class TemplateConfigSchema(TemplateConfigCreate):
    """Template complet avec métadonnées."""
    base_path: str | None = Field(
        default=None,
        description="Chemin vers le dossier du template"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création"
    )


class VariantCreate(BaseModel):
    """Données pour ajouter une variante à un template."""
    template_name: str = Field(
        ...,
        description="Nom du template parent"
    )
    group: str = Field(
        ...,
        description="Groupe auquel appartient la variante"
    )
    variant_name: str = Field(
        ...,
        min_length=1,
        description="Nom du fichier de variante"
    )
    threshold: float | None = Field(
        default=None,
        ge=0.5,
        le=1.0,
        description="Seuil spécifique (optionnel, hérite du groupe sinon)"
    )
    image_region: RegionSchema | None = Field(
        default=None,
        description="Région de l'image source à extraire"
    )
    image_source: str | None = Field(
        default=None,
        description="Chemin de l'image source uploadée"
    )


class TemplateStatsSchema(BaseModel):
    """Statistiques d'utilisation d'un template pour un manoir."""
    priority_order: list[str] = Field(
        default_factory=list,
        description="Ordre de priorité des variantes"
    )
    hits: dict[str, int] = Field(
        default_factory=dict,
        description="Nombre de matchs par variante"
    )
    last_match: str | None = Field(
        default=None,
        description="Dernière variante qui a matché"
    )


class TemplateListItem(BaseModel):
    """Élément de la liste des templates."""
    name: str = Field(..., description="Nom du template")
    category: str = Field(..., description="Catégorie")
    description: str = Field(default="", description="Description")
    groups: list[str] = Field(
        default_factory=list,
        description="Groupes configurés"
    )
    variant_count: int = Field(
        default=0,
        description="Nombre total de variantes"
    )


class TemplateTestRequest(BaseModel):
    """Requête pour tester un template sur une image."""
    template_name: str = Field(
        ...,
        description="Nom du template à tester"
    )
    image_source: str = Field(
        ...,
        description="Chemin de l'image source"
    )
    groups: list[str] = Field(
        default_factory=list,
        description="Groupes à tester (tous si vide)"
    )


class TemplateTestResult(BaseModel):
    """Résultat du test d'un template."""
    variant: str = Field(..., description="Nom de la variante")
    group: str = Field(..., description="Groupe de la variante")
    found: bool = Field(..., description="Template trouvé ou non")
    position: tuple[int, int] | None = Field(
        default=None,
        description="Position (x, y) si trouvé"
    )
    confidence: float | None = Field(
        default=None,
        description="Confiance du match"
    )
    threshold: float = Field(..., description="Seuil utilisé")
