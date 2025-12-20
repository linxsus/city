# -*- coding: utf-8 -*-
"""Catalogue des erreurs connues pour Mafia City

Définit les erreurs détectables et leurs corrections automatiques.
Les images templates doivent être placées dans templates/popups/
"""
from erreurs.item_erreur import ItemErreur, ItemErreurImage, ItemErreurTexte
from utils.config import EXCLUSION_COMPTE_UTILISE, EXCLUSION_RELANCE_BLUESTACKS
import actions.liste_actions as ListeActions


def creer_erreurs_mafia_city(fenetre):
    """Crée la liste des erreurs connues pour Mafia City
    
    Args:
        fenetre: Instance de FenetreBase
        
    Returns:
        dict: Dictionnaire d'erreurs {nom: ItemErreur}
    """
    erreurs = {}
    
    # =====================================================
    # ERREURS DE CONNEXION
    # =====================================================
    
    # Popup "Compte utilisé ailleurs"
    # Nécessite de cliquer OK et d'exclure la fenêtre 2h
    erreurs['compte_utilise'] = ItemErreurImage(
        fenetre,
        image="popup_compte_utilise.png",
        message="Compte utilisé sur un autre appareil",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=False,
        exclure_fenetre=EXCLUSION_COMPTE_UTILISE,
        priorite=100,  # Haute priorité
    )
    
    # Popup "Connexion perdue"
    # Cliquer sur reconnexion et attendre
    erreurs['connexion_perdue'] = ItemErreurImage(
        fenetre,
        image="popup_connexion_perdue.png",
        message="Connexion au serveur perdue",
        action_correction=_creer_action_reconnexion(fenetre),
        retry_action_originale=True,
        priorite=90,
    )
    
    # Popup "Erreur réseau"
    erreurs['erreur_reseau'] = ItemErreurImage(
        fenetre,
        image="popup_erreur_reseau.png",
        message="Erreur réseau",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=True,
        priorite=85,
    )
    
    # =====================================================
    # ERREURS DE JEU
    # =====================================================
    
    # Popup "Pas assez de ressources"
    erreurs['ressources_insuffisantes'] = ItemErreurImage(
        fenetre,
        image="popup_ressources_insuffisantes.png",
        message="Ressources insuffisantes",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=False,
        priorite=50,
    )
    
    # Popup "Slots pleins"
    erreurs['slots_pleins'] = ItemErreurImage(
        fenetre,
        image="popup_slots_pleins.png",
        message="Tous les slots sont occupés",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=False,
        priorite=50,
    )
    
    # Popup "File d'attente pleine"
    erreurs['file_attente_pleine'] = ItemErreurImage(
        fenetre,
        image="popup_file_attente_pleine.png",
        message="File d'attente de construction pleine",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=False,
        priorite=50,
    )
    
    # Popup "Cible introuvable" (mercenaire/joueur disparu)
    erreurs['cible_introuvable'] = ItemErreurImage(
        fenetre,
        image="popup_cible_introuvable.png",
        message="Cible introuvable sur la carte",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=True,  # Réessayer avec une autre cible
        priorite=40,
    )
    
    # Popup "Troupes insuffisantes"
    erreurs['troupes_insuffisantes'] = ItemErreurImage(
        fenetre,
        image="popup_troupes_insuffisantes.png",
        message="Troupes insuffisantes",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=False,
        priorite=50,
    )
    
    # =====================================================
    # POPUPS D'INFORMATION / PUBLICITÉ
    # =====================================================
    
    # Popup événement / publicité
    erreurs['popup_evenement'] = ItemErreurImage(
        fenetre,
        image="popup_evenement.png",
        message="Popup événement/publicité",
        action_correction=_creer_action_fermer_popup(fenetre),
        retry_action_originale=True,
        priorite=30,
    )
    
    # Popup récompense / bonus
    erreurs['popup_recompense'] = ItemErreurImage(
        fenetre,
        image="popup_recompense.png",
        message="Popup récompense",
        action_correction=_creer_action_clic_ok(fenetre),
        retry_action_originale=True,
        priorite=30,
    )
    
    # =====================================================
    # ERREURS SYSTÈME / BLUESTACKS
    # =====================================================
    
    # Popup "Application ne répond pas"
    erreurs['app_ne_repond_pas'] = ItemErreurTexte(
        fenetre,
        texte="ne répond pas",
        message="Application ne répond pas",
        action_correction=_creer_action_attendre(fenetre),
        retry_action_originale=True,
        priorite=95,
    )
    
    # Popup mise à jour disponible
    erreurs['mise_a_jour'] = ItemErreurImage(
        fenetre,
        image="popup_mise_a_jour.png",
        message="Mise à jour disponible",
        action_correction=_creer_action_clic_plus_tard(fenetre),
        retry_action_originale=True,
        priorite=80,
    )
    
    return erreurs


def creer_liste_erreurs_verif_apres(fenetre):
    """Crée la liste des erreurs à vérifier APRÈS chaque action
    
    Ces erreurs sont des popups qui peuvent apparaître à tout moment.
    
    Args:
        fenetre: Instance de FenetreBase
        
    Returns:
        List[ItemErreur]: Liste ordonnée par priorité
    """
    erreurs = creer_erreurs_mafia_city(fenetre)
    
    # Sélectionner les erreurs à vérifier après chaque action
    erreurs_verif = [
        erreurs['compte_utilise'],
        erreurs['connexion_perdue'],
        erreurs['popup_evenement'],
        erreurs['popup_recompense'],
    ]
    
    # Trier par priorité décroissante
    erreurs_verif.sort(key=lambda e: e.priorite, reverse=True)
    
    return erreurs_verif


def creer_liste_erreurs_si_echec(fenetre):
    """Crée la liste des erreurs à vérifier SI une action échoue
    
    Args:
        fenetre: Instance de FenetreBase
        
    Returns:
        List[ItemErreur]: Liste ordonnée par priorité
    """
    erreurs = creer_erreurs_mafia_city(fenetre)
    
    # Erreurs qui peuvent expliquer un échec
    erreurs_echec = [
        erreurs['ressources_insuffisantes'],
        erreurs['slots_pleins'],
        erreurs['file_attente_pleine'],
        erreurs['cible_introuvable'],
        erreurs['troupes_insuffisantes'],
        erreurs['erreur_reseau'],
        erreurs['app_ne_repond_pas'],
    ]
    
    erreurs_echec.sort(key=lambda e: e.priorite, reverse=True)
    
    return erreurs_echec


# =====================================================
# HELPERS POUR CRÉER LES ACTIONS DE CORRECTION
# =====================================================

def _creer_action_clic_ok(fenetre):
    """Crée une action pour cliquer sur OK"""
    def clic_ok(f):
        # Chercher et cliquer sur le bouton OK
        pos = f.find_image("templates/boutons/bouton_ok.png")
        if pos:
            f.click_at(pos[0], pos[1])
            return True
        # Fallback: cliquer au centre de l'écran
        f.click_at(f.largeur // 2, f.hauteur // 2 + 100)
        return True
    
    return ListeActions.ActionSimple(fenetre, clic_ok, nom="ClicOK")


def _creer_action_reconnexion(fenetre):
    """Crée une action pour cliquer sur Reconnexion"""
    def clic_reconnexion(f):
        # Chercher et cliquer sur le bouton Reconnexion
        pos = f.find_image("templates/boutons/bouton_reconnexion.png")
        if pos:
            f.click_at(pos[0], pos[1])
        else:
            # Fallback: cliquer sur OK
            pos = f.find_image("templates/boutons/bouton_ok.png")
            if pos:
                f.click_at(pos[0], pos[1])
        return True
    
    return [
        ListeActions.ActionSimple(fenetre, clic_reconnexion, nom="ClicReconnexion"),
        ListeActions.ActionAttendre(fenetre, 5),  # Attendre la reconnexion
    ]


def _creer_action_fermer_popup(fenetre):
    """Crée une action pour fermer un popup (croix ou clic extérieur)"""
    def fermer_popup(f):
        # Chercher la croix de fermeture
        pos = f.find_image("templates/boutons/bouton_fermer.png")
        if pos:
            f.click_at(pos[0], pos[1])
            return True
        # Fallback: cliquer en dehors du popup
        f.click_at(50, 50)
        return True
    
    return ListeActions.ActionSimple(fenetre, fermer_popup, nom="FermerPopup")


def _creer_action_clic_plus_tard(fenetre):
    """Crée une action pour cliquer sur 'Plus tard'"""
    def clic_plus_tard(f):
        pos = f.find_image("templates/boutons/bouton_plus_tard.png")
        if pos:
            f.click_at(pos[0], pos[1])
            return True
        # Fallback: chercher texte "Plus tard" ou "Later"
        pos = f.find_text("Plus tard")
        if pos:
            f.click_at(pos[0], pos[1])
            return True
        pos = f.find_text("Later")
        if pos:
            f.click_at(pos[0], pos[1])
            return True
        return False
    
    return ListeActions.ActionSimple(fenetre, clic_plus_tard, nom="ClicPlusTard")


def _creer_action_attendre(fenetre):
    """Crée une action pour attendre (app ne répond pas)"""
    def attendre(f):
        # Cliquer sur Attendre si présent
        pos = f.find_image("templates/boutons/bouton_attendre.png")
        if pos:
            f.click_at(pos[0], pos[1])
        return True
    
    return ListeActions.ActionSimple(fenetre, attendre, nom="Attendre")
