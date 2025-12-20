# -*- coding: utf-8 -*-
import shutil
import glob

captures = glob.glob(r"C:\Projets\2 project\templates\Capture*.png")
if captures:
    src = captures[0]
    dst = r"C:\Projets\2 project\templates\capture_test.png"
    shutil.copy(src, dst)
    print(f"Copie: {src} -> {dst}")
else:
    print("Aucune capture trouvee")
