# -*- coding: utf-8 -*-
"""Debug de la detection du popup connexion quotidienne"""

import cv2
import numpy as np
from pathlib import Path

def analyser_images():
    """Compare le template avec la capture d'ecran"""

    # Chemins
    template_path = Path(r"C:\Projets\2 project\templates\popups\connexion_quotidienne.png")
    capture_path = Path(r"C:\Projets\2 project\templates\capture_test.png")

    print("="*70)
    print("ANALYSE DE DETECTION DU POPUP")
    print("="*70)

    # Vérifier que les fichiers existent
    if not template_path.exists():
        print(f"\n[ERREUR] Template non trouve: {template_path}")
        return

    if not capture_path.exists():
        print(f"\n[ERREUR] Capture non trouvee: {capture_path}")
        return

    # Charger les images
    print(f"\n[INFO] Chargement du template: {template_path}")
    template = cv2.imread(str(template_path))

    print(f"[INFO] Chargement de la capture: {capture_path}")
    capture = cv2.imread(str(capture_path))

    if template is None:
        print(f"[ERREUR] Impossible de charger le template")
        return

    if capture is None:
        print(f"[ERREUR] Impossible de charger la capture")
        return

    # Informations sur les images
    print(f"\n--- INFORMATIONS ---")
    print(f"Template: {template.shape[1]}x{template.shape[0]} pixels, {template.shape[2]} canaux")
    print(f"Capture: {capture.shape[1]}x{capture.shape[0]} pixels, {capture.shape[2]} canaux")

    # Convertir en niveaux de gris
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    capture_gray = cv2.cvtColor(capture, cv2.COLOR_BGR2GRAY)

    # Template matching
    print(f"\n--- TEMPLATE MATCHING ---")
    result = cv2.matchTemplate(capture_gray, template_gray, cv2.TM_CCOEFF_NORMED)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"Score minimum: {min_val:.4f}")
    print(f"Score maximum: {max_val:.4f}")
    print(f"Position du meilleur match: {max_loc}")

    # Tester différents seuils
    print(f"\n--- TEST DES SEUILS ---")
    seuils = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]

    for seuil in seuils:
        detecte = max_val >= seuil
        status = "DETECTE" if detecte else "NON DETECTE"
        print(f"Seuil {seuil:.2f}: {status} (score={max_val:.4f})")

    # Analyse
    print(f"\n--- DIAGNOSTIC ---")

    if max_val < 0.5:
        print("[PROBLEME] Score tres faible (<0.5)")
        print("Causes possibles:")
        print("  - Le template ne correspond pas a l'image de la capture")
        print("  - Le template a ete extrait avec une resolution differente")
        print("  - Les couleurs/contraste sont differents")
        print("\nSOLUTION: Re-extraire le template depuis une vraie capture d'ecran")

    elif max_val < 0.7:
        print("[ATTENTION] Score faible (0.5-0.7)")
        print("Le template correspond partiellement mais pas assez")
        print("\nSOLUTION: Verifier que le template est correct ou baisser le seuil")

    elif max_val < 0.8:
        print("[OK] Score acceptable (0.7-0.8)")
        print("Detection possible avec threshold=0.7")

    else:
        print("[EXCELLENT] Score eleve (>0.8)")
        print("Detection fiable")

    # Sauvegarder l'image avec le rectangle de detection
    if max_val >= 0.5:
        h, w = template_gray.shape
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)

        # Copier l'image
        result_img = capture.copy()

        # Dessiner le rectangle
        cv2.rectangle(result_img, top_left, bottom_right, (0, 255, 0), 2)

        # Ajouter le score
        cv2.putText(result_img, f"Score: {max_val:.3f}",
                    (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        output_path = "C:/Projets/2 project/debug_detection_result.png"
        cv2.imwrite(output_path, result_img)
        print(f"\n[INFO] Image de resultat sauvegardee: {output_path}")

    print("\n" + "="*70)


if __name__ == "__main__":
    analyser_images()
