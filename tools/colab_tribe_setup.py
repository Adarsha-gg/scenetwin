#!/usr/bin/env python3
"""Bootstrap a Colab runtime for TRIBE v2, then restart the kernel manually.

Run this as phase 1 on a persistent Colab L4/A100/H100 session:

    colab exec -s scenetwin-l4 -f tools/colab_tribe_setup.py --timeout 1800
    colab restart-kernel -s scenetwin-l4
    colab exec -s scenetwin-l4 -f tools/colab_tribe_smoke.py --timeout 1800

Do not import tribev2 in the same kernel after this install phase. The restart is
required so NumPy/SciPy/sklearn compiled extensions come from one coherent stack.
"""
from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check)


print("Bootstrapping pinned TRIBE v2 dependency stack...", flush=True)
run([sys.executable, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"])
run([
    sys.executable,
    "-m",
    "pip",
    "uninstall",
    "-y",
    "tribev2",
    "neuralset",
    "neuraltrain",
    "exca",
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "torch",
    "torchvision",
    "torchaudio",
], check=False)
run([
    sys.executable,
    "-m",
    "pip",
    "install",
    "--no-cache-dir",
    "numpy==2.2.6",
    "scipy==1.15.3",
    "pandas==2.2.3",
    "scikit-learn==1.6.1",
    "torch==2.6.0",
    "torchvision==0.21.0",
])
run([
    sys.executable,
    "-m",
    "pip",
    "install",
    "--no-cache-dir",
    "git+https://github.com/facebookresearch/tribev2.git",
    "yt-dlp",
    "gtts",
])
run([sys.executable, "-m", "pip", "check"], check=False)
print("\nSETUP_DONE: restart the Colab kernel before importing tribev2.", flush=True)
