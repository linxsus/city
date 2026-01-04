"""
Script de vérification du support Intel Arc / XPU
Exécuter avec: python check_intel_xpu.py
"""

import sys

def check_intel_xpu():
    print("=" * 60)
    print("  Vérification du support Intel Arc / XPU")
    print("=" * 60)
    print()

    # Vérifier PyTorch
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
    except ImportError:
        print("✗ PyTorch non installé")
        return False

    # Vérifier Intel Extension for PyTorch
    try:
        import intel_extension_for_pytorch as ipex
        print(f"✓ Intel Extension for PyTorch version: {ipex.__version__}")

        # Vérifier XPU
        xpu_available = ipex.xpu.is_available()
        print(f"✓ Intel XPU disponible: {xpu_available}")

        if xpu_available:
            device_count = ipex.xpu.device_count()
            print(f"✓ Nombre de GPU Intel: {device_count}")

            for i in range(device_count):
                name = ipex.xpu.get_device_name(i)
                print(f"  - GPU {i}: {name}")

            # Test simple
            print("\n  Test de calcul sur XPU...")
            x = torch.randn(1000, 1000).to("xpu")
            y = torch.randn(1000, 1000).to("xpu")
            z = torch.matmul(x, y)
            print("  ✓ Calcul matriciel sur XPU réussi!")

            return True
        else:
            print("\n⚠ Intel XPU non détecté. Vérifiez:")
            print("  1. Pilotes Intel Arc à jour (version 31.0.101.5186+)")
            print("  2. GPU Intel Arc compatible (A380, A580, A750, A770)")
            print("  3. Ou Intel Core Ultra avec iGPU")
            return False

    except ImportError:
        print("✗ Intel Extension for PyTorch non installé")
        print("  Installez avec: pip install intel-extension-for-pytorch")
        return False
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

def check_opencl():
    """Vérifie si OpenCL est disponible (alternative pour Intel GPU)"""
    print("\n" + "=" * 60)
    print("  Vérification OpenCL (alternative)")
    print("=" * 60)

    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
        print(f"✓ OpenCL disponible")
        for platform in platforms:
            print(f"  Platform: {platform.name}")
            devices = platform.get_devices()
            for device in devices:
                print(f"    - {device.name} ({cl.device_type.to_string(device.type)})")
        return True
    except ImportError:
        print("○ PyOpenCL non installé (optionnel)")
        print("  Pour l'installer: pip install pyopencl")
        return False
    except Exception as e:
        print(f"○ OpenCL non disponible: {e}")
        return False

def check_cpu_optimization():
    """Vérifie les optimisations CPU Intel"""
    print("\n" + "=" * 60)
    print("  Optimisations CPU Intel")
    print("=" * 60)

    import torch

    # Vérifier MKL
    mkl_available = torch.backends.mkl.is_available()
    print(f"{'✓' if mkl_available else '○'} Intel MKL: {mkl_available}")

    # Vérifier OpenMP
    try:
        import os
        omp_threads = os.environ.get('OMP_NUM_THREADS', 'non défini')
        print(f"○ OMP_NUM_THREADS: {omp_threads}")
    except:
        pass

    # Nombre de threads PyTorch
    print(f"✓ PyTorch threads: {torch.get_num_threads()}")

    # Vérifier les instructions CPU
    try:
        import intel_extension_for_pytorch as ipex
        print("✓ IPEX optimizations disponibles pour CPU")
    except:
        pass

if __name__ == "__main__":
    print()
    xpu_ok = check_intel_xpu()
    check_cpu_optimization()
    check_opencl()

    print("\n" + "=" * 60)
    if xpu_ok:
        print("  ✓ Votre Intel Arc est prêt pour l'accélération GPU!")
    else:
        print("  Le système fonctionnera en mode CPU optimisé Intel")
        print("  (MKL/OpenMP pour de bonnes performances)")
    print("=" * 60)
    print()
