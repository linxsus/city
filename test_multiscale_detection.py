# -*- coding: utf-8 -*-
"""Test de la detection multi-echelle"""

import cv2
import numpy as np
from pathlib import Path

def test_multiscale():
    """Compare detection normale vs multi-echelle"""

    # Chemins
    template_path = Path(r"C:\Projets\2 project\templates\popups\connexion_quotidienne.png")
    capture_path = Path(r"C:\Projets\2 project\templates\capture_test.png")

    print("="*70)
    print("TEST DETECTION MULTI-ECHELLE")
    print("="*70)

    # Charger les images
    template = cv2.imread(str(template_path))
    capture = cv2.imread(str(capture_path))

    if template is None or capture is None:
        print("[ERREUR] Impossible de charger les images")
        return

    print(f"\nTemplate: {template.shape[1]}x{template.shape[0]} pixels")
    print(f"Capture: {capture.shape[1]}x{capture.shape[0]} pixels")

    # Convertir en niveaux de gris
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    capture_gray = cv2.cvtColor(capture, cv2.COLOR_BGR2GRAY)

    # Test avec detection normale
    print(f"\n--- DETECTION NORMALE (echelle 1.0) ---")
    result = cv2.matchTemplate(capture_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(f"Score: {max_val:.4f}")
    print(f"Position: {max_loc}")

    # Test multi-echelle
    print(f"\n--- DETECTION MULTI-ECHELLE ---")
    scales = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    best_score = 0
    best_scale = 1.0
    best_location = None

    print(f"\nTest de {len(scales)} echelles: {scales}")
    print(f"\n{'Echelle':<10} {'Score':<10} {'Status':<15}")
    print("-" * 35)

    for scale in scales:
        # Redimensionner le template
        h, w = template_gray.shape
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Vérifier que le template n'est pas plus grand que la capture
        if new_w > capture_gray.shape[1] or new_h > capture_gray.shape[0]:
            print(f"{scale:<10.2f} {'N/A':<10} {'Trop grand':<15}")
            continue

        template_resized = cv2.resize(template_gray, (new_w, new_h))

        # Template matching
        result = cv2.matchTemplate(capture_gray, template_resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # Status
        if max_val > best_score:
            status = "MEILLEUR!"
            best_score = max_val
            best_scale = scale
            best_location = max_loc
        elif max_val >= 0.7:
            status = "Bon"
        elif max_val >= 0.6:
            status = "Acceptable"
        else:
            status = ""

        print(f"{scale:<10.2f} {max_val:<10.4f} {status:<15}")

    # Resultats
    print(f"\n--- RESULTATS ---")
    print(f"Detection normale: score={max_val:.4f} (echelle 1.0)")
    print(f"Detection multi-echelle: score={best_score:.4f} (echelle {best_scale:.2f})")

    improvement = best_score - max_val
    improvement_pct = (improvement / max_val * 100) if max_val > 0 else 0

    print(f"\nAmelioration: +{improvement:.4f} ({improvement_pct:+.1f}%)")

    if best_score >= 0.8:
        print(f"\n[EXCELLENT] Score >= 0.8 a l'echelle {best_scale:.2f}")
        print("Recommandation: Utiliser find_template_multiscale() avec ce template")
    elif best_score >= 0.7:
        print(f"\n[BON] Score >= 0.7 a l'echelle {best_scale:.2f}")
        print("Recommandation: find_template_multiscale() ameliorera la detection")
    elif best_score >= 0.6:
        print(f"\n[OK] Score >= 0.6 a l'echelle {best_scale:.2f}")
        print("Le multi-echelle aide mais le template pourrait etre ameliore")
    else:
        print(f"\n[ATTENTION] Score < 0.6 meme avec multi-echelle")
        print("Recommandation: Re-extraire le template depuis une vraie capture")

    # Sauvegarder l'image avec le meilleur match
    if best_location:
        result_img = capture.copy()

        h, w = template_gray.shape
        new_w = int(w * best_scale)
        new_h = int(h * best_scale)

        top_left = best_location
        bottom_right = (top_left[0] + new_w, top_left[1] + new_h)

        cv2.rectangle(result_img, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(result_img, f"Score: {best_score:.3f} (scale: {best_scale:.2f})",
                    (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        output_path = r"C:\Projets\2 project\debug_multiscale_result.png"
        cv2.imwrite(output_path, result_img)
        print(f"\n[INFO] Image sauvegardee: {output_path}")

    print("\n" + "="*70)


if __name__ == "__main__":
    test_multiscale()
